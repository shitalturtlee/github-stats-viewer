from collections import Counter

import pandas as pd
import streamlit as st

import report
from api_client import GitHubError, get_languages, get_repos, get_user
from local_analyzer import analyze_repo

st.set_page_config(page_title="GitHub Stats Viewer", layout="wide")
st.title("GitHub Stats Viewer")


@st.cache_data(ttl=3600, show_spinner=False)
def load_profile(username):
    return get_user(username), get_repos(username)


@st.cache_data(ttl=3600, show_spinner=False)
def load_languages(owner, repo):
    return get_languages(owner, repo)


@st.cache_data(ttl=3600, show_spinner=False)
def run_local(owner, repo):
    return analyze_repo(owner, repo)


# ---------- 1. Username input ----------
username = st.text_input("GitHub username", placeholder="e.g. torvalds")
if st.button("Load profile") and username.strip():
    st.session_state["username"] = username.strip()
    st.session_state.pop("analyzed", None)

name = st.session_state.get("username")
if not name:
    st.info("Enter a GitHub username and click Load profile.")
    st.stop()

try:
    user, repos = load_profile(name)
except GitHubError as e:
    st.error(str(e))
    st.stop()

# ---------- 2. Profile (from the API) ----------
st.header("Profile")
c1, c2 = st.columns([1, 4])
with c1:
    st.image(user["avatar_url"], width=120)
with c2:
    st.subheader(user.get("name") or user["login"])
    if user.get("bio"):
        st.write(user["bio"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Followers", user["followers"])
    m2.metric("Following", user["following"])
    m3.metric("Public repos", user["public_repos"])
    m4.metric("Total stars", sum(r["stargazers_count"] for r in repos))

if not repos:
    st.warning("This user has no public repositories.")
    st.stop()

# ---------- 3. Repositories table ----------
st.header("Repositories")
hide_forks = st.checkbox("Hide forks", value=True)
shown = [r for r in repos if not (hide_forks and r["fork"])] or repos

table = pd.DataFrame([{
    "name": r["name"],
    "language": r["language"],
    "stars": r["stargazers_count"],
    "forks": r["forks_count"],
    "size (MB)": round(r["size"] / 1024, 1),
    "updated": r["updated_at"][:10],
} for r in shown]).sort_values("stars", ascending=False)
st.dataframe(table, hide_index=True, width="stretch")

main_langs = Counter(r["language"] for r in shown if r["language"])
if main_langs:
    st.plotly_chart(report.language_pie(dict(main_langs), "Main language per repo"),
                    width="stretch")

# ---------- 4. Pick a repo for local analysis ----------
st.header("Deep dive: local analysis")
repo_name = st.selectbox("Choose a repository", [r["name"] for r in shown])
repo_info = next(r for r in shown if r["name"] == repo_name)

too_big = repo_info["size"] > 100_000  # size is in KB
if too_big:
    st.warning(f"This repo is about {repo_info['size'] / 1024:.0f} MB and may take a long time to clone.")
allow = st.checkbox("Analyze anyway") if too_big else True

if st.button("Analyze repo", disabled=not allow):
    st.session_state["analyzed"] = repo_name

if st.session_state.get("analyzed") != repo_name:
    st.stop()

owner = user["login"]
try:
    with st.spinner("Cloning and analyzing..."):
        result = run_local(owner, repo_name)
        api_langs = load_languages(owner, repo_name)
except GitHubError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"Could not analyze this repo (is it empty or private?): {e}")
    st.stop()

# ---------- 5. Results ----------
k1, k2, k3 = st.columns(3)
k1.metric("Commits", result.commit_count)
k2.metric("Lines of code", f"{result.total_loc:,}")
k3.metric("TODO / FIXME", result.todo_count)

st.subheader("Languages")
if api_langs or result.loc_by_language:
    st.plotly_chart(report.language_comparison_bar(api_langs, result.loc_by_language),
                    width="stretch")
    st.caption("API percentages are by bytes; local percentages are by lines of code.")
else:
    st.write("No language data.")

st.subheader("Commit activity")
if result.commits is not None and not result.commits.empty:
    a, b = st.columns(2)
    a.plotly_chart(report.commit_timeline(result.commits), width="stretch")
    b.plotly_chart(report.contributors_bar(result.commits), width="stretch")
    st.plotly_chart(report.activity_heatmap(result.commits), width="stretch")
    st.caption("Times are in UTC.")
else:
    st.write("No commits found.")

st.subheader("Code health")
x, y = st.columns(2)
x.write("Most frequently changed files")
x.dataframe(pd.DataFrame(result.top_changed_files, columns=["file", "commits"]),
            hide_index=True, width="stretch")
y.write("Largest files")
y.dataframe(pd.DataFrame(result.largest_files, columns=["file", "bytes"]),
            hide_index=True, width="stretch")
