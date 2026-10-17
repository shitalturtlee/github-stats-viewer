import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import git
import pandas as pd
from pygount import SourceAnalysis

from models import RepoAnalysis

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
TODO_RE = re.compile(r"\b(TODO|FIXME)\b")


def clone_repo(owner, repo):
    """Clone a public repo into a temp folder and return its path."""
    tmp = tempfile.mkdtemp(prefix="ghstats_")
    git.Repo.clone_from(f"https://github.com/{owner}/{repo}.git", tmp)
    return Path(tmp)


def cleanup(path):
    shutil.rmtree(path, ignore_errors=True)


def _source_files(path):
    """Yield every file in the repo, skipping junk folders."""
    for p in Path(path).rglob("*"):
        if p.is_file() and not (set(p.parts) & SKIP_DIRS):
            yield p


def get_commits(path):
    """Return a DataFrame with one row per commit."""
    repo = git.Repo(path)
    rows = [
        {
            "author": c.author.name,
            "date": c.committed_datetime,
            "message": c.message.strip().split("\n")[0],
        }
        for c in repo.iter_commits()
    ]
    df = pd.DataFrame(rows, columns=["author", "date", "message"])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], utc=True)
    return df


def count_loc(path):
    """Return {language: lines_of_code} using pygount."""
    totals = Counter()
    for f in _source_files(path):
        try:
            a = SourceAnalysis.from_file(str(f), "stats")
            if a.code_count > 0 and a.language not in ("__unknown__", "__binary__"):
                totals[a.language] += a.code_count
        except Exception:
            continue  # skip files pygount can't read
    return dict(totals.most_common())


def most_changed_files(path, n=10):
    """Files that appear in the most commits."""
    repo = git.Repo(path)
    out = repo.git.log("--name-only", "--pretty=format:")
    names = [line for line in out.splitlines() if line.strip()]
    return Counter(names).most_common(n)


def largest_files(path, n=10):
    sizes = [(str(f.relative_to(path)), f.stat().st_size) for f in _source_files(path)]
    return sorted(sizes, key=lambda x: x[1], reverse=True)[:n]


def count_todos(path):
    total = 0
    for f in _source_files(path):
        try:
            total += len(TODO_RE.findall(f.read_text(errors="ignore")))
        except Exception:
            continue
    return total


def analyze_repo(owner, repo):
    """Clone, analyze, clean up, and return a RepoAnalysis."""
    path = clone_repo(owner, repo)
    try:
        commits = get_commits(path)
        loc = count_loc(path)
        return RepoAnalysis(
            name=repo,
            total_loc=sum(loc.values()),
            loc_by_language=loc,
            commit_count=len(commits),
            top_authors=commits["author"].value_counts().head(10).to_dict()
            if not commits.empty else {},
            top_changed_files=most_changed_files(path),
            largest_files=largest_files(path),
            todo_count=count_todos(path),
        )
    finally:
        cleanup(path)
