from dataclasses import dataclass, field


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
