"""
Job Market Intelligence Dashboard
Presentation layer for the HDFS + Pig + Hive big-data pipeline
(Large-Scale Job Market Intelligence and Emerging Skill Demand Analysis).

Run with:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import analytics as an
import charts as ch
import data_loader as dl

st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="ðŸ“Š",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }
    section[data-testid="stSidebar"] * { color: #E5E7EB !important; }
    section[data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; }
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #EDEFF3;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(16,24,40,0.04);
    }
    div[data-testid="stMetricLabel"] { color: #6B7280; }
    h1, h2, h3 { color: #111827; }
    .source-tag {
        display: inline-block; padding: 2px 10px; border-radius: 999px;
        background: #EEF2FF; color: #3730A3; font-size: 0.75rem; margin-bottom: 8px;
    }
    .footer-note {
        color: #9CA3AF; font-size: 0.8rem; margin-top: 40px;
        border-top: 1px solid #EDEFF3; padding-top: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
def load_everything():
    jobs_df, meta = dl.load_cleaned_jobs()
    skills_long = dl.build_skills_long(jobs_df)
    return jobs_df, meta, skills_long


try:
    jobs_df_full, load_meta, skills_long_full = load_everything()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

FMT = "â‚¹{:,.0f}"


def fmt_money(v):
    if v is None or pd.isna(v):
        return "N/A"
    return FMT.format(v)


# ---------------------------------------------------------------------------
# Sidebar: navigation + global filters
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 📊 Job Market Intelligence")
st.sidebar.caption("HDFS • Pig • Hive — Big Data Analytics")

PAGES = [
    "Executive Overview",
    "Skill Demand Intelligence",
    "Salary Analytics",
    "Location & Hiring",
    "Experience & Job Roles",
    "Emerging Skill Trends",
    "Data Explorer",
]
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

if st.sidebar.button("â†º Reset Filters", use_container_width=True):
    for k in list(st.session_state.keys()):
        if k.startswith("filt_"):
            del st.session_state[k]
    st.rerun()

locations_all = sorted(jobs_df_full["location"].dropna().unique().tolist())
roles_all = jobs_df_full["job_title"].value_counts().head(200).index.tolist()  # cap for a usable dropdown
exp_buckets_all = ["Entry-level (0-2 yrs)", "Mid-level (2-5 yrs)", "Senior (5+ yrs)", "Not specified"]

sel_locations = st.sidebar.multiselect("Location", locations_all, key="filt_locations")
sel_roles = st.sidebar.multiselect("Job role (top 200 by volume)", roles_all, key="filt_roles")
sel_exp = st.sidebar.multiselect("Experience level", exp_buckets_all, key="filt_exp")

salary_available = jobs_df_full["avg_salary"].dropna()
salary_available = salary_available[salary_available > 0]
if not salary_available.empty:
    smin, smax = float(salary_available.min()), float(salary_available.max())
    sel_salary = st.sidebar.slider(
        "Salary range (annual, disclosed only)", min_value=0.0, max_value=round(smax, -3),
        value=(0.0, round(smax, -3)), key="filt_salary",
    )
else:
    sel_salary = None

st.sidebar.caption(
    "Note: there is no absolute posting date in the source data â€” see the "
    "Emerging Skill Trends page for why a date-range filter isn't offered."
)

st.sidebar.markdown("---")
source_note = dl.get_source_labels(load_meta)
st.sidebar.caption(f"Data source: {source_note}")


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    out = an.add_experience_bucket(df)
    if sel_locations:
        out = out[out["location"].isin(sel_locations)]
    if sel_roles:
        out = out[out["job_title"].isin(sel_roles)]
    if sel_exp:
        out = out[out["experience_bucket"].isin(sel_exp)]
    if sel_salary is not None:
        lo, hi = sel_salary
        has_salary = out["avg_salary"].notna() & (out["avg_salary"] > 0)
        in_range = out["avg_salary"].between(lo, hi)
        out = out[~has_salary | in_range]
    return out


jobs_df = apply_filters(jobs_df_full)
filtered_ids = set(jobs_df["job_id"])
skills_long = skills_long_full[skills_long_full["job_id"].isin(filtered_ids)]

if jobs_df.empty:
    st.warning("No postings match the current filters. Try removing a filter or hit **Reset Filters**.")
    st.stop()


def footer():
    st.markdown(
        '<div class="footer-note">Large-Scale Job Market Intelligence and Emerging Skill Demand '
        'Analysis â€” processed with <b>HDFS</b>, <b>Apache Pig</b>, and <b>Apache Hive</b> for '
        'large-scale big-data transformations; this dashboard is the presentation layer.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# PAGE 1 â€” Executive Overview
# ---------------------------------------------------------------------------
if page == "Executive Overview":
    st.title("Executive Overview")
    st.caption("Large-Scale Job Market Intelligence and Emerging Skill Demand Analysis â€” Indian job market, ~97.9K postings.")
    st.markdown(f'<span class="source-tag">Source: {source_note}</span>', unsafe_allow_html=True)

    k = an.kpis(jobs_df)
    n_distinct_skills = skills_long["skill"].nunique() if not skills_long.empty else 0
    top_skill_row = an.skill_counts(skills_long, k["total_postings"], n=1)
    top_skill = top_skill_row.iloc[0]["skill"] if not top_skill_row.empty else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Postings", f"{k['total_postings']:,}")
    c2.metric("Unique Companies", f"{k['unique_companies']:,}")
    c3.metric("Unique Locations", f"{k['unique_locations']:,}")
    c4.metric("Distinct Skills", f"{n_distinct_skills:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Avg Salary (INR, disclosed)", fmt_money(k["avg_salary"]))
    c6.metric("Median Salary (INR, disclosed)", fmt_money(k["median_salary"]))
    c7.metric("Top Job Role", k["top_role"][:28] + ("â€¦" if len(k["top_role"]) > 28 else ""))
    c8.metric("Top Skill", top_skill)

    st.caption(
        f"Salary stats computed from {k['n_with_salary']:,} of {k['total_postings']:,} postings "
        f"with a disclosed salary ({k['n_without_salary']:,} excluded as undisclosed)."
    )

    st.markdown("### ")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(ch.horizontal_bar(an.top_job_roles(jobs_df, 10), "postings", "job_title",
                                           "Top 10 Job Roles by Posting Count"), use_container_width=True)
    with col2:
        top_skills_df = an.skill_counts(skills_long, k["total_postings"], n=10)
        st.plotly_chart(ch.horizontal_bar(top_skills_df, "postings", "skill",
                                           "Top 10 Most Demanded Skills"), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(ch.horizontal_bar(an.postings_by_location(jobs_df, 10), "postings", "location",
                                           "Job Postings by Location (Top 10)"), use_container_width=True)
    with col4:
        exp_df = an.postings_by_experience(jobs_df)
        st.plotly_chart(ch.vertical_bar(exp_df, "experience_bucket", "postings",
                                         "Postings by Experience Level", color=ch.ACCENT_2),
                         use_container_width=True)

    st.markdown("### Automated Insights")
    insights = []
    if not top_skills_df.empty:
        row = top_skills_df.iloc[0]
        insights.append(f"**{row['skill']}** appears in {row['postings']:,} postings "
                         f"({row['pct_of_postings']:.1f}% of postings in the current filter).")
    top_role_df = an.top_job_roles(jobs_df, 1)
    if not top_role_df.empty:
        r = top_role_df.iloc[0]
        insights.append(f"**{r['job_title']}** is the most frequently posted role, with {r['postings']:,} postings.")
    top_loc_df = an.postings_by_location(jobs_df, 1)
    if not top_loc_df.empty:
        l = top_loc_df.iloc[0]
        insights.append(f"**{l['location']}** leads hiring activity with {l['postings']:,} postings "
                         f"({l['postings'] / k['total_postings'] * 100:.1f}% of the filtered total).")
    for i in insights:
        st.markdown(f"- {i}")
    footer()

# ---------------------------------------------------------------------------
# PAGE 2 â€” Skill Demand Intelligence
# ---------------------------------------------------------------------------
elif page == "Skill Demand Intelligence":
    st.title("Skill Demand Intelligence")
    st.markdown(f'<span class="source-tag">Source: {source_note}</span>', unsafe_allow_html=True)
    st.caption(
        "Skills are parsed from the comma-separated `skills` field, trimmed, case-normalized for "
        "grouping, and de-duplicated within each posting so one job can't inflate a skill's count."
    )

    total = len(jobs_df)
    all_skill_counts = an.skill_counts(skills_long, total)

    top20 = all_skill_counts.head(20)
    st.plotly_chart(ch.horizontal_bar(top20, "postings", "skill", "Top 20 Skills by Demand"),
                     use_container_width=True)

    st.markdown("### Explore a Specific Skill")
    if all_skill_counts.empty:
        st.info("No skill data available for the current filter.")
    else:
        chosen_skill = st.selectbox("Search / select a skill", all_skill_counts["skill"].tolist())
        col1, col2 = st.columns(2)
        with col1:
            by_loc = an.skill_demand_by_location(skills_long, chosen_skill, 10)
            st.plotly_chart(ch.horizontal_bar(by_loc, "postings", "location",
                                               f"'{chosen_skill}' Demand by Location"), use_container_width=True)
        with col2:
            by_role = an.skill_demand_by_role(skills_long, chosen_skill, 10)
            st.plotly_chart(ch.horizontal_bar(by_role, "postings", "job_title",
                                               f"'{chosen_skill}' Demand by Job Role"), use_container_width=True)

        st.markdown("### Skill Co-occurrence (Top 15 Skills)")
        top15_keys = all_skill_counts.head(15)["skill"].tolist()
        co = an.skill_cooccurrence(skills_long, top15_keys)
        if co.empty:
            st.info("Not enough overlapping postings among the top skills to show co-occurrence.")
        else:
            co["pair"] = co["skill_a"] + " + " + co["skill_b"]
            st.plotly_chart(ch.horizontal_bar(co, "postings_together", "pair",
                                               "Most Common Skill Pairs (same posting)"), use_container_width=True)

    st.markdown("### All Skills")
    st.dataframe(
        all_skill_counts.rename(columns={"postings": "Postings", "pct_of_postings": "% of Postings", "skill": "Skill"}),
        use_container_width=True, height=350,
    )
    footer()

# ---------------------------------------------------------------------------
# PAGE 3 â€” Salary Analytics
# ---------------------------------------------------------------------------
elif page == "Salary Analytics":
    st.title("Salary Analytics")
    st.markdown(f'<span class="source-tag">Source: {source_note}</span>', unsafe_allow_html=True)

    excl = an.salary_exclusion_summary(jobs_df, currency="INR")
    st.info(
        f"Salary figures below use **INR, annual** postings only "
        f"({excl['usable_for_salary_stats']:,} of {excl['total']:,} postings). "
        f"Excluded: {excl['excluded_other_currency']:,} non-INR postings and "
        f"{excl['excluded_missing_or_zero_salary']:,} with no disclosed salary "
        f"(source data hardcodes these to 0, which would misrepresent them as real salaries). "
        f"Where a posting gave a salary range, the midpoint of min/max is used as the representative salary."
    )

    valid_df = an.valid_salary_jobs(jobs_df, currency="INR")
    if valid_df.empty:
        st.warning("No postings with a disclosed INR salary match the current filters.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            role_sal = an.salary_stats_by_group(jobs_df, "job_title", n=15)
            st.plotly_chart(ch.horizontal_bar(role_sal, "avg_salary", "job_title",
                                               "Average Salary by Job Role (top by avg, min 5 postings)"),
                             use_container_width=True)
        with col2:
            st.plotly_chart(ch.histogram(valid_df["avg_salary"], "Salary Distribution (INR/year)"),
                             use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            exp_df = an.add_experience_bucket(valid_df)
            st.plotly_chart(ch.box_plot(exp_df, "experience_bucket", "avg_salary",
                                         "Salary vs. Experience Level"), use_container_width=True)
        with col4:
            loc_sal = an.salary_stats_by_group(jobs_df, "location", n=15)
            st.plotly_chart(ch.horizontal_bar(loc_sal, "avg_salary", "location",
                                               "Average Salary by Location (top by avg, min 5 postings)"),
                             use_container_width=True)

        st.markdown("### Salary by Skill (Top 15 Skills, min 5 postings)")
        top_skills = an.skill_counts(skills_long, len(jobs_df), n=15)["skill"].tolist()
        merged = skills_long[skills_long["skill"].isin(top_skills)].merge(
            valid_df[["job_id"]], on="job_id", how="inner"
        )
        if merged.empty:
            st.info("Not enough disclosed-salary postings among the top skills to show this breakdown.")
        else:
            sk_sal = merged.groupby("skill")["avg_salary"].agg(["count", "mean"]).reset_index()
            sk_sal.columns = ["skill", "postings_with_salary", "avg_salary"]
            sk_sal = sk_sal[sk_sal["postings_with_salary"] >= 5].sort_values("avg_salary", ascending=False)
            st.plotly_chart(ch.horizontal_bar(sk_sal, "avg_salary", "skill", "Average Salary by Skill"),
                             use_container_width=True)

        st.markdown("### Role/Location Salary Table")
        st.dataframe(
            role_sal.rename(columns={"job_title": "Job Role", "postings_with_salary": "Postings",
                                      "avg_salary": "Avg Salary", "median_salary": "Median Salary"}),
            use_container_width=True,
        )
    footer()

# ---------------------------------------------------------------------------
# PAGE 4 â€” Location & Hiring Analytics
# ---------------------------------------------------------------------------
elif page == "Location & Hiring":
    st.title("Location & Hiring Analytics")
    st.markdown(f'<span class="source-tag">Source: {source_note}</span>', unsafe_allow_html=True)
    st.caption(
        "`location` is the primary city extracted from the original multi-location text "
        "(e.g. 'Kolkata(Chinar Park)' â†’ 'Kolkata'); different cities are never merged."
    )

    top_locs = an.postings_by_location(jobs_df, 20)
    st.plotly_chart(ch.horizontal_bar(top_locs, "postings", "location", "Top Hiring Locations"),
                     use_container_width=True)

    st.markdown("### Drill Into a Location")
    chosen_loc = st.selectbox("Select a location", top_locs["location"].tolist() if not top_locs.empty else [])
    if chosen_loc:
        loc_jobs = jobs_df[jobs_df["location"] == chosen_loc]
        st.metric(f"Postings in {chosen_loc}", f"{len(loc_jobs):,}")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(ch.horizontal_bar(an.top_job_roles(loc_jobs, 10), "postings", "job_title",
                                               f"Top Job Roles in {chosen_loc}"), use_container_width=True)
        with col2:
            loc_skill_long = skills_long[skills_long["location"] == chosen_loc]
            loc_skills = an.skill_counts(loc_skill_long, len(loc_jobs), n=10)
            st.plotly_chart(ch.horizontal_bar(loc_skills, "postings", "skill",
                                               f"Top Skills Demanded in {chosen_loc}"), use_container_width=True)

        valid_loc = an.valid_salary_jobs(loc_jobs, currency="INR")
        if not valid_loc.empty:
            st.plotly_chart(ch.histogram(valid_loc["avg_salary"], f"Salary Distribution in {chosen_loc} (INR/year)"),
                             use_container_width=True)
    else:
            st.info(f"No disclosed INR salary postings for {chosen_loc} in the current filter.")
    footer()

# ---------------------------------------------------------------------------
# PAGE 5 â€” Experience & Job Role Analytics
# ---------------------------------------------------------------------------
elif page == "Experience & Job Roles":
    st.title("Experience & Job Role Analytics")
    st.markdown(f'<span class="source-tag">Source: {source_note}</span>', unsafe_allow_html=True)
    st.caption(
        "Experience buckets are derived from `min_experience` (years): "
        "Entry-level = 0-2, Mid-level = 2-5, Senior = 5+. Postings with no experience "
        "field are kept as 'Not specified' rather than guessed."
    )

    exp_df = an.postings_by_experience(jobs_df)
    st.plotly_chart(ch.vertical_bar(exp_df, "experience_bucket", "postings",
                                     "Job Demand by Experience Level"), use_container_width=True)

    valid_df = an.valid_salary_jobs(jobs_df, currency="INR")
    if not valid_df.empty:
        exp_sal = an.add_experience_bucket(valid_df)
        st.plotly_chart(ch.box_plot(exp_sal, "experience_bucket", "avg_salary",
                                     "Salary by Experience Level (INR/year)"), use_container_width=True)
    else:
        st.info("No disclosed INR salary postings in the current filter.")

    st.markdown("### Top Skills per Experience Level")
    c1, c2, c3 = st.columns(3)
    for col, bucket, label in zip(
        (c1, c2, c3),
        ("Entry-level (0-2 yrs)", "Mid-level (2-5 yrs)", "Senior (5+ yrs)"),
        ("Entry-level", "Mid-level", "Senior"),
    ):
        with col:
            top = an.top_skills_by_experience_bucket(skills_long, jobs_df, bucket, n=10)
            if top.empty:
                st.caption(f"No {label} postings with skill data in this filter.")
    else:
                st.plotly_chart(ch.horizontal_bar(top, "postings", "skill", f"Top Skills â€” {label}"),
                                 use_container_width=True)
    footer()

# ---------------------------------------------------------------------------
# PAGE 6 â€” Emerging Skill Trends
# ---------------------------------------------------------------------------
elif page == "Emerging Skill Trends":
    st.title("Emerging Skill Trends")
    st.markdown(f'<span class="source-tag">Source: {source_note}</span>', unsafe_allow_html=True)

    st.warning(
        "**Important limitation:** the source `jobUploaded` field is relative recency text "
        "only ('6 Days Ago', 'Just Now', 'Starts in 1-3 months') with **no scrape date and no "
        "absolute posting date**. A true year-over-year emerging-skill trend (e.g. 2024 vs 2025 "
        "vs 2026) is **not derivable from this dataset** without fabricating dates. "
        "This page therefore shows (a) the dataset's actual recency coverage, and "
        "(b) overall skill demand â€” which reflects total popularity, **not growth** â€” "
        "rather than inventing a historical trend line.",
        icon="⚠️",
    )

    cov = an.recency_coverage(jobs_df)
    st.plotly_chart(ch.vertical_bar(cov, "posted_bucket", "postings",
                                     "Posting Recency Coverage (relative text, not a calendar timeline)",
                                     color=ch.ACCENT_2),
                     use_container_width=True)

    st.markdown("### Highest Total Demand (Not Growth)")
    st.caption(
        "These are the most-demanded skills overall â€” ranked by total posting count, "
        "the same metric as the Executive Overview and Skill Demand pages. Labeling any of "
        "these 'emerging' would not be supported by the data, since growth requires comparable "
        "counts across multiple real time periods, which this dataset does not have."
    )
    top_overall = an.skill_counts(skills_long, len(jobs_df), n=15)
    st.plotly_chart(ch.horizontal_bar(top_overall, "postings", "skill", "Top 15 Skills by Total Demand"),
                     use_container_width=True)

    st.markdown("### If Real Hive Time-Based Aggregates Are Available")
    hive_time = dl.load_optional_hive_csv("time_based.csv", ["period", "skill", "postings"])
    if hive_time is not None:
        st.success(
            "Loaded a Hive-exported time-based aggregate "
            "from dashboard/data/time_based.csv."
        )

        hive_time["postings"] = pd.to_numeric(
            hive_time["postings"], errors="coerce"
        )
        hive_time = hive_time.dropna(subset=["postings"])

        top_skills = (
            hive_time.groupby("skill")["postings"]
            .sum()
            .nlargest(10)
            .index
        )

        chart_df = hive_time[hive_time["skill"].isin(top_skills)]

        st.plotly_chart(
            ch.line_chart(
                chart_df,
                "period",
                "postings",
                "Skill Demand by Posting Recency",
                color="skill",
            ),
            use_container_width=True,
        )
    else:
        st.info(
            "No `dashboard/data/time_based.csv` export found. If Task 3 (Hive) produces a real "
            "period-over-period skill aggregate from a dataset with true posting dates, drop it "
            "here with columns `period, skill, postings` and this page will chart it automatically."
        )
    footer()

# ---------------------------------------------------------------------------
# PAGE 7 â€” Data Explorer
# ---------------------------------------------------------------------------
elif page == "Data Explorer":
    st.title("Data Explorer")
    st.markdown(f'<span class="source-tag">Source: {source_note}</span>', unsafe_allow_html=True)

    display_cols = ["job_id", "job_title", "company_name", "location", "currency",
                     "min_salary", "max_salary", "avg_salary", "experience_raw",
                     "skills", "posted_raw"]
    display_cols = [c for c in display_cols if c in jobs_df.columns]

    search = st.text_input("Search job title or company", "")
    view_df = jobs_df[display_cols]
    if search:
        mask = (
            view_df["job_title"].str.contains(search, case=False, na=False)
            | view_df["company_name"].str.contains(search, case=False, na=False)
        )
        view_df = view_df[mask]

    st.caption(f"{len(view_df):,} of {len(jobs_df):,} filtered postings match.")
    st.dataframe(view_df, use_container_width=True, height=500)

    st.download_button(
        "â¬‡ Download filtered results as CSV",
        data=view_df.to_csv(index=False).encode("utf-8"),
        file_name="job_postings_filtered.csv",
        mime="text/csv",
    )
    footer()





