import pandas as pd
import plotly.express as px

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------- aggregation (DataFrame in, DataFrame out) ----------

def commits_per_month(df):
    if df.empty:
        return pd.DataFrame(columns=["month", "commits"])
    months = df["date"].dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
    out = months.value_counts().sort_index().reset_index()
    out.columns = ["month", "commits"]
    return out


def top_contributors(df, n=10):
    if df.empty:
        return pd.DataFrame(columns=["author", "commits"])
    out = df["author"].value_counts().head(n).reset_index()
    out.columns = ["author", "commits"]
    return out


def activity_matrix(df):
    """Weekday x hour table of commit counts."""
    if df.empty:
        return pd.DataFrame(0, index=DAYS, columns=range(24))
    m = pd.crosstab(df["date"].dt.day_name().str[:3], df["date"].dt.hour)
    return m.reindex(index=DAYS, columns=range(24), fill_value=0)


def language_comparison(api_bytes, local_loc):
    """Percent share per language: GitHub API (bytes) vs local (lines of code)."""
    def pct(d):
        total = sum(d.values()) or 1
        return {k: v * 100 / total for k, v in d.items()}

    a, l = pct(api_bytes), pct(local_loc)
    langs = sorted(set(a) | set(l))
    return pd.DataFrame({
        "language": langs,
        "API %": [round(a.get(x, 0), 1) for x in langs],
        "Local %": [round(l.get(x, 0), 1) for x in langs],
    })


# ---------- figures (data in, Plotly figure out) ----------

def language_pie(lang_dict, title="Languages"):
    return px.pie(names=list(lang_dict), values=list(lang_dict.values()), title=title)


def commit_timeline(df):
    return px.line(commits_per_month(df), x="month", y="commits",
                   markers=True, title="Commits per month")


def contributors_bar(df):
    return px.bar(top_contributors(df), x="commits", y="author",
                  orientation="h", title="Top contributors")


def activity_heatmap(df):
    return px.imshow(activity_matrix(df),
                     labels=dict(x="Hour of day", y="Weekday", color="Commits"),
                     aspect="auto", title="When commits happen")


def language_comparison_bar(api_bytes, local_loc):
    d = language_comparison(api_bytes, local_loc)
    long = d.melt(id_vars="language", var_name="source", value_name="percent")
    return px.bar(long, x="language", y="percent", color="source",
                  barmode="group", title="Language share: API vs local")
