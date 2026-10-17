import os
import sys

import report
from api_client import get_languages
from local_analyzer import analyze_repo

owner, repo = sys.argv[1].split("/")
r = analyze_repo(owner, repo)
api_langs = get_languages(owner, repo)

os.makedirs("out", exist_ok=True)
report.language_comparison_bar(api_langs, r.loc_by_language).write_html("out/languages.html")
report.commit_timeline(r.commits).write_html("out/timeline.html")
report.contributors_bar(r.commits).write_html("out/contributors.html")
report.activity_heatmap(r.commits).write_html("out/heatmap.html")
print(report.language_comparison(api_langs, r.loc_by_language))
print("Charts written to ./out")
