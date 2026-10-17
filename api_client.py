import os
import json
import hashlib
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.github.com"
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 60 * 60  # cache for 1 hour

token = os.getenv("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json"}
if token:
    HEADERS["Authorization"] = f"Bearer {token}"


class GitHubError(Exception):
    """Raised when the GitHub API returns an error we want to explain."""


def _cache_path(url, params):
    key = url + json.dumps(params or {}, sort_keys=True)
    return CACHE_DIR / (hashlib.md5(key.encode()).hexdigest() + ".json")


def _get(path, params=None):
    """GET a GitHub API path with caching and error handling."""
    url = f"{BASE}{path}"
    cache_file = _cache_path(url, params)

    if cache_file.exists() and time.time() - cache_file.stat().st_mtime < CACHE_TTL:
        return json.loads(cache_file.read_text())

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        raise GitHubError(f"Network error: {e}")

    if r.status_code == 404:
        raise GitHubError("Not found. Check the username or repo name.")
    if r.status_code in (403, 429) and r.headers.get("X-RateLimit-Remaining") == "0":
        reset = int(r.headers.get("X-RateLimit-Reset", 0))
        mins = max(0, (reset - int(time.time())) // 60)
        raise GitHubError(f"Rate limit hit. Resets in about {mins} minutes.")
    if r.status_code == 401:
        raise GitHubError("Bad token. Check GITHUB_TOKEN in your .env file.")
    r.raise_for_status()

    data = r.json()
    cache_file.write_text(json.dumps(data))
    return data


def get_user(username):
    return _get(f"/users/{username}")


def get_repos(username):
    """Fetch all public repos, following pagination."""
    repos, page = [], 1
    while True:
        batch = _get(f"/users/{username}/repos",
                     {"per_page": 100, "page": page, "sort": "updated"})
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def get_languages(owner, repo):
    """Returns {language: bytes_of_code}."""
    return _get(f"/repos/{owner}/{repo}/languages")


def get_rate_limit():
    return _get("/rate_limit")
