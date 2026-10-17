from dataclasses import dataclass, field
from typing import Any


@dataclass
class RepoAnalysis:
    name: str
    total_loc: int
    loc_by_language: dict
    commit_count: int
    top_authors: dict
    top_changed_files: list = field(default_factory=list)
    largest_files: list = field(default_factory=list)
    todo_count: int = 0
    commits: Any = None  # pandas DataFrame: author, date, message
