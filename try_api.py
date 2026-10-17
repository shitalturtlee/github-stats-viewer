from api_client import get_user, get_repos, get_languages, GitHubError

try:
    user = get_user("torvalds")
    print(user["name"], "-", user["followers"], "followers")

    repos = get_repos("torvalds")
    print("Repos:", len(repos))

    total_stars = sum(r["stargazers_count"] for r in repos)
    print("Total stars:", total_stars)

    top = max(repos, key=lambda r: r["stargazers_count"])
    print("Top repo:", top["name"], top["stargazers_count"])
    print("Languages:", get_languages("torvalds", top["name"]))

except GitHubError as e:
    print("Error:", e)
