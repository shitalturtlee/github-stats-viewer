import sys
from local_analyzer import analyze_repo

if len(sys.argv) != 2 or "/" not in sys.argv[1]:
    print("Usage: python try_local.py owner/repo")
    sys.exit(1)

owner, repo = sys.argv[1].split("/")
print(f"Analyzing {owner}/{repo} ...")

try:
    r = analyze_repo(owner, repo)
except Exception as e:
    print("Failed:", e)
    sys.exit(1)

print("Commits:", r.commit_count)
print("Total LOC:", r.total_loc)
print("Languages:", r.loc_by_language)
print("Top authors:", r.top_authors)
print("Most changed files:", r.top_changed_files[:5])
print("Largest files:", r.largest_files[:3])
print("TODOs:", r.todo_count)
