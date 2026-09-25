"""
Pure calculation functions for the dashboard. No Streamlit or Plotly here —
every function takes a (filtered) DataFrame and returns numbers/DataFrames,
so the UI layer (app.py) and the loader stay decoupled from the math.
"""

from __future__ import annotations

import pandas as pd


def kpis(jobs_df: pd.DataFrame) -> dict:
    """Headline KPI numbers for the Executive Overview page. Respects whatever
    filters were already applied to jobs_df before this is called."""
    n = len(jobs_df)
    valid_salary = jobs_df["avg_salary"].dropna()
    valid_salary = valid_salary[valid_salary > 0]

    top_role = jobs_df["job_title"].mode()
    top_role = top_role.iloc[0] if not top_role.empty else "N/A"

    n_skill_col = jobs_df["skills"].dropna()
    n_distinct_skills = None  # filled in by caller using the exploded skills df, see skill_counts()

    return {
        "total_postings": n,
        "unique_companies": jobs_df["company_name"].nunique(),
        "unique_locations": jobs_df["location"].nunique(),
        "avg_salary": valid_salary.mean() if not valid_salary.empty else None,
        "median_salary": valid_salary.median() if not valid_salary.empty else None,
        "min_salary": valid_salary.min() if not valid_salary.empty else None,
        "max_salary": valid_salary.max() if not valid_salary.empty else None,
        "n_with_salary": int(valid_salary.shape[0]),
        "n_without_salary": int(n - valid_salary.shape[0]),
        "top_role": top_role,
    }


def top_job_roles(jobs_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (
        jobs_df["job_title"].value_counts().head(n)
        .rename_axis("job_title").reset_index(name="postings")
    )


def postings_by_location(jobs_df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    return (
        jobs_df["location"].value_counts().head(n)
        .rename_axis("location").reset_index(name="postings")
    )


def experience_bucket(min_exp: float) -> str:
    """Categorize by minimum years of experience required.
    Bucketing rule (documented for the user): 0-2 yrs = Entry, 2-5 = Mid,
    5+ = Senior. Rows with no experience info are labeled 'Not specified'."""
    if pd.isna(min_exp):
        return "Not specified"
    if min_exp < 2:
        return "Entry-level (0-2 yrs)"
    if min_exp < 5:
        return "Mid-level (2-5 yrs)"
    return "Senior (5+ yrs)"


def add_experience_bucket(jobs_df: pd.DataFrame) -> pd.DataFrame:
    out = jobs_df.copy()
    out["experience_bucket"] = out["min_experience"].apply(experience_bucket)
    return out


def postings_by_experience(jobs_df: pd.DataFrame) -> pd.DataFrame:
    df = add_experience_bucket(jobs_df)
    order = ["Entry-level (0-2 yrs)", "Mid-level (2-5 yrs)", "Senior (5+ yrs)", "Not specified"]
    counts = df["experience_bucket"].value_counts().reindex(order).fillna(0).astype(int)
    return counts.rename_axis("experience_bucket").reset_index(name="postings")


def skill_counts(skills_long_df: pd.DataFrame, total_postings: int, n: int | None = None) -> pd.DataFrame:
    if skills_long_df.empty:
        return pd.DataFrame(columns=["skill", "postings", "pct_of_postings"])
    counts = skills_long_df.groupby("skill")["job_id"].nunique().sort_values(ascending=False)
    out = counts.rename_axis("skill").reset_index(name="postings")
    out["pct_of_postings"] = (out["postings"] / total_postings * 100).round(2) if total_postings else 0
    return out.head(n) if n else out


def skill_demand_by_location(skills_long_df: pd.DataFrame, skill: str, n: int = 10) -> pd.DataFrame:
    sub = skills_long_df[skills_long_df["skill"] == skill]
    return (
        sub.groupby("location")["job_id"].nunique().sort_values(ascending=False).head(n)
        .rename_axis("location").reset_index(name="postings")
    )


def skill_demand_by_role(skills_long_df: pd.DataFrame, skill: str, n: int = 10) -> pd.DataFrame:
    sub = skills_long_df[skills_long_df["skill"] == skill]
    return (
        sub.groupby("job_title")["job_id"].nunique().sort_values(ascending=False).head(n)
        .rename_axis("job_title").reset_index(name="postings")
    )


def skill_cooccurrence(skills_long_df: pd.DataFrame, top_skill_keys: list[str], max_pairs: int = 15) -> pd.DataFrame:
    """How often each pair of top skills appears together in the same posting."""
    sub = skills_long_df[skills_long_df["skill"].isin(top_skill_keys)]
    if sub.empty:
        return pd.DataFrame(columns=["skill_a", "skill_b", "postings_together"])
    pivot = sub.groupby(["job_id", "skill"]).size().unstack(fill_value=0)
    pivot = (pivot > 0).astype(int)
    co = pivot.T.dot(pivot)
    pairs = []
    cols = co.columns.tolist()
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            val = int(co.loc[a, b])
            if val > 0:
                pairs.append((a, b, val))
    out = pd.DataFrame(pairs, columns=["skill_a", "skill_b", "postings_together"])
    return out.sort_values("postings_together", ascending=False).head(max_pairs)


def salary_stats_by_group(jobs_df: pd.DataFrame, group_col: str, n: int = 15, min_count: int = 5) -> pd.DataFrame:
    """Average/median salary per group, only for groups with a minimum sample
    size and only for rows with disclosed salary (see valid_salary_jobs)."""
    df = valid_salary_jobs(jobs_df)
    if df.empty:
        return pd.DataFrame(columns=[group_col, "postings_with_salary", "avg_salary", "median_salary"])
    g = df.groupby(group_col)["avg_salary"].agg(["count", "mean", "median"]).reset_index()
    g.columns = [group_col, "postings_with_salary", "avg_salary", "median_salary"]
    g = g[g["postings_with_salary"] >= min_count]
    return g.sort_values("avg_salary", ascending=False).head(n)


def valid_salary_jobs(jobs_df: pd.DataFrame, currency: str | None = "INR") -> pd.DataFrame:
    """Rows with a real, disclosed salary. Restricted to one currency by
    default so INR and USD postings are never averaged together."""
    df = jobs_df[jobs_df["avg_salary"].notna() & (jobs_df["avg_salary"] > 0)]
    if currency:
        df = df[df["currency"] == currency]
    return df


def salary_exclusion_summary(jobs_df: pd.DataFrame, currency: str = "INR") -> dict:
    total = len(jobs_df)
    other_currency = int((jobs_df["currency"] != currency).sum())
    usable = len(valid_salary_jobs(jobs_df, currency))
    return {
        "total": total,
        "usable_for_salary_stats": usable,
        "excluded_other_currency": other_currency,
        "excluded_missing_or_zero_salary": total - other_currency - usable if total else 0,
    }


def recency_coverage(jobs_df: pd.DataFrame) -> pd.DataFrame:
    if "posted_bucket" not in jobs_df.columns:
        return pd.DataFrame(columns=["posted_bucket", "postings"])
    order = ["Today", "1-3 Days Ago", "4-7 Days Ago", "8-14 Days Ago",
             "Future Start (<1 month)", "Future Start (1-3 months)", "Future Start (other)", "Unknown"]
    counts = jobs_df["posted_bucket"].value_counts().reindex(order).dropna().astype(int)
    return counts.rename_axis("posted_bucket").reset_index(name="postings")


def top_skills_by_experience_bucket(skills_long_df: pd.DataFrame, jobs_df: pd.DataFrame, bucket: str, n: int = 10) -> pd.DataFrame:
    jd = add_experience_bucket(jobs_df)
    job_ids = set(jd[jd["experience_bucket"] == bucket]["job_id"])
    sub = skills_long_df[skills_long_df["job_id"].isin(job_ids)]
    if sub.empty:
        return pd.DataFrame(columns=["skill", "postings"])
    return (
        sub.groupby("skill")["job_id"].nunique().sort_values(ascending=False).head(n)
        .rename_axis("skill").reset_index(name="postings")
    )
