"""
Data loading layer for the Job Market Intelligence dashboard.

Design (see PART 7 of the project brief):
  1. If exported Hive/Pig outputs are present under dashboard/data/, prefer
     them for the analysis they cover.
  2. Otherwise fall back to the original raw Excel dataset and replicate the
     exact Task 1 (HDFS) cleaning contract documented in
     task1_hdfs/README.md / task1_hdfs/scripts/02_clean_data.py, so the
     dashboard's numbers match what the real pipeline would produce.
  3. Every consumer of this module can ask which source was actually used
     via `get_source_labels()`, and the UI must surface that.

This module never fabricates data. Where a value is genuinely missing or
un-derivable (e.g. an absolute posting date), it is left missing and the
caller is expected to disclose that rather than guess.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASHBOARD_DIR.parent
RAW_EXCEL_PATH = PROJECT_ROOT / "dataset" / "indian-job-market-dataset-2025.xlsx"
HIVE_EXPORT_DIR = DASHBOARD_DIR / "data"

# Source -> standardized column names (identical to task1_hdfs/scripts/02_clean_data.py)
RENAME_MAP = {
    "jobId": "job_id",
    "title": "job_title",
    "companyName": "company_name",
    "companyId": "company_id",
    "location": "location_raw",
    "tagsAndSkills": "skills",
    "experience": "experience_raw",
    "minimumExperience": "min_experience",
    "maximumExperience": "max_experience",
    "salary": "salary_raw",
    "minimumSalary": "min_salary",
    "maximumSalary": "max_salary",
    "currency": "currency",
    "jobUploaded": "posted_raw",
    "jobDescription": "job_description",
    "ReviewsCount": "reviews_count",
    "AggregateRating": "rating",
}

FINAL_COLUMNS = [
    "job_id", "job_title", "company_name", "company_id",
    "location", "location_raw",
    "currency", "min_salary", "max_salary", "avg_salary",
    "experience_raw", "min_experience", "max_experience",
    "skills", "posted_raw", "reviews_count", "rating",
]

# Recency buckets derived from `posted_raw` (relative text only — there is no
# absolute scrape date in the source data, so this is NOT a historical
# calendar timeline; see task1_hdfs/README.md "Note on time-based analysis").
def _bucket_posted_raw(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return "Unknown"
    t = text.lower().strip()
    if t in ("just now", "today") or "few hours ago" in t:
        return "Today"
    m = re.match(r"(\d+)\s*day", t)
    if m:
        n = int(m.group(1))
        if n <= 3:
            return "1-3 Days Ago"
        if n <= 7:
            return "4-7 Days Ago"
        return "8-14 Days Ago"
    if "starts within 1 month" in t:
        return "Future Start (<1 month)"
    if "starts in 1-3 months" in t or "starts in 1–3 months" in t:
        return "Future Start (1-3 months)"
    if t.startswith("starts"):
        return "Future Start (other)"
    return "Unknown"


def _clean_location(raw: str) -> str:
    """'Kolkata(Chinar Park)' -> 'Kolkata'; 'Gandhinagar, Ahmedabad' -> 'Gandhinagar'."""
    if not isinstance(raw, str) or not raw.strip():
        return "Unknown"
    first = raw.split(",")[0]
    first = re.sub(r"\(.*?\)", "", first)
    return first.strip() or "Unknown"


@st.cache_data(show_spinner="Loading and cleaning job postings...")
def load_cleaned_jobs() -> tuple[pd.DataFrame, dict]:
    """
    Returns (cleaned_jobs_df, meta) where meta documents provenance and the
    row-level exclusions applied, exactly mirroring task1_hdfs/scripts/02_clean_data.py.
    """
    meta: dict = {"source": None, "excel_path": str(RAW_EXCEL_PATH)}

    # 1) Prefer an already-cleaned export from the real Hive/Pig pipeline if present.
        # 1) Prefer the cleaned export from the real Hive/Pig pipeline.
    hive_cleaned = HIVE_EXPORT_DIR / "jobs_cleaned.csv"

    if hive_cleaned.exists():
        df = pd.read_csv(
            hive_cleaned,
            dtype={"job_id": str, "company_id": str}
        )

        # Remove Beeline table prefixes, e.g. jobs.job_id -> job_id.
        df.columns = [
            str(col).split(".")[-1].strip()
            for col in df.columns
        ]

        missing = [c for c in FINAL_COLUMNS if c not in df.columns]

        if not missing:
            # Recreate the recency bucket used by the dashboard.
            if "posted_bucket" not in df.columns:
                if "posted_raw" in df.columns:
                    df["posted_bucket"] = (
                        df["posted_raw"].apply(_bucket_posted_raw)
                    )
                else:
                    df["posted_bucket"] = "Unknown"

            meta["source"] = "hive_export"
            meta["n_raw"] = None
            meta["n_cleaned"] = len(df)
            meta["removed_duplicates"] = None
            meta["removed_missing_required"] = None
            meta["removed_invalid_salary_experience"] = None

            return df[FINAL_COLUMNS + ["posted_bucket"]], meta

        else:
            print(
                "Hive export is missing required columns:",
                missing
            )

    # 2) Fall back to the raw Excel dataset and replicate the Task 1 cleaning contract.
    if not RAW_EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Could not find the dataset at {RAW_EXCEL_PATH}. "
            "Make sure dataset/indian-job-market-dataset-2025.xlsx exists in the repo."
        )

    df = pd.read_excel(RAW_EXCEL_PATH, dtype={"jobId": str, "companyId": str})
    n_start = len(df)
    df = df.rename(columns=RENAME_MAP)

    str_cols = ["job_title", "company_name", "location_raw", "skills",
                "experience_raw", "salary_raw", "posted_raw"]
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"nan": ""})
        df[c] = df[c].str.replace(r"[\r\n]+", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()

    n_before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="job_id", keep="first")
    removed_duplicates = n_before - len(df)

    n_before = len(df)
    df = df[(df["job_id"].astype(str).str.strip() != "") &
            (df["job_title"] != "") &
            (df["location_raw"] != "")]
    removed_missing_required = n_before - len(df)

    df["company_name"] = df["company_name"].replace("", "Unknown")
    df["skills"] = df["skills"].replace("", "Not Specified")
    df["reviews_count"] = pd.to_numeric(df["reviews_count"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    df["min_salary"] = pd.to_numeric(df["min_salary"], errors="coerce")
    df["max_salary"] = pd.to_numeric(df["max_salary"], errors="coerce")
    not_disclosed_mask = df["salary_raw"].str.lower().str.contains("not disclosed", na=False)
    df.loc[not_disclosed_mask, ["min_salary", "max_salary"]] = pd.NA

    n_before = len(df)
    df["min_experience"] = pd.to_numeric(df["min_experience"], errors="coerce")
    df["max_experience"] = pd.to_numeric(df["max_experience"], errors="coerce")
    bad_salary = ((df["min_salary"] < 0) | (df["max_salary"] < 0) |
                  ((df["min_salary"] > df["max_salary"]) & df["max_salary"].notna() & (df["max_salary"] > 0)))
    bad_experience = ((df["min_experience"] < 0) | (df["max_experience"] < 0) |
                       ((df["min_experience"] > df["max_experience"]) & df["max_experience"].notna()))
    df = df[~(bad_salary.fillna(False) | bad_experience.fillna(False))]
    removed_invalid = n_before - len(df)

    df["avg_salary"] = df[["min_salary", "max_salary"]].mean(axis=1)
    df["location"] = df["location_raw"].apply(_clean_location)
    df["posted_bucket"] = df["posted_raw"].apply(_bucket_posted_raw)

    df = df[FINAL_COLUMNS + ["posted_bucket"]]

    meta.update({
        "source": "excel_fallback",
        "n_raw": n_start,
        "n_cleaned": len(df),
        "removed_duplicates": removed_duplicates,
        "removed_missing_required": removed_missing_required,
        "removed_invalid_salary_experience": removed_invalid,
    })
    return df, meta


@st.cache_data(show_spinner="Indexing skills...")
def build_skills_long(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prefer the actual Hive job_skills.csv export.
    Enrich Hive skill rows with salary, experience and posting data
    from the cleaned jobs export. Fall back to local skill extraction
    only if the Hive skills export is unavailable or invalid.
    """

    hive_skills_path = HIVE_EXPORT_DIR / "job_skills.csv"

    if hive_skills_path.exists():
        try:
            hive_skills = pd.read_csv(
                hive_skills_path,
                dtype={"job_id": str}
            )

            # Remove any Beeline table prefixes from column names.
            hive_skills.columns = [
                str(col).split(".")[-1].strip()
                for col in hive_skills.columns
            ]

            required = {
                "job_id", "job_title", "location",
                "currency", "skill"
            }

            if required.issubset(hive_skills.columns):
                hive_skills["job_id"] = (
                    hive_skills["job_id"].astype(str).str.strip()
                )

                hive_skills["skill"] = (
                    hive_skills["skill"].fillna("").astype(str).str.strip()
                )

                hive_skills = hive_skills[
                    (hive_skills["skill"] != "") &
                    (hive_skills["skill"].str.lower() != "not specified")
                ].copy()

                # Normalize skills and remove duplicate job-skill pairs.
                hive_skills["skill_key"] = (
                    hive_skills["skill"].str.casefold()
                )

                hive_skills = hive_skills.drop_duplicates(
                    subset=["job_id", "skill_key"]
                )

                # Keep the most frequent original spelling for display.
                display_map = (
                    hive_skills.groupby(
                        ["skill_key", "skill"]
                    ).size()
                    .reset_index(name="n")
                    .sort_values("n", ascending=False)
                    .drop_duplicates("skill_key")
                    .set_index("skill_key")["skill"]
                )

                hive_skills["skill_display_raw"] = hive_skills["skill"]
                hive_skills["skill"] = (
                    hive_skills["skill_key"].map(display_map)
                )

                # Bring in job-level information from the cleaned Hive export.
                enrichment_cols = [
                    "job_id", "min_experience", "max_experience",
                    "avg_salary", "posted_bucket"
                ]

                available_cols = [
                    c for c in enrichment_cols if c in jobs_df.columns
                ]

                job_details = jobs_df[available_cols].copy()
                job_details["job_id"] = (
                    job_details["job_id"].astype(str).str.strip()
                )
                job_details = job_details.drop_duplicates(
                    subset="job_id"
                )

                hive_skills = hive_skills.merge(
                    job_details,
                    on="job_id",
                    how="left"
                )

                # Ensure all expected dashboard columns exist.
                for col in [
                    "min_experience", "max_experience",
                    "avg_salary", "posted_bucket"
                ]:
                    if col not in hive_skills.columns:
                        hive_skills[col] = (
                            "Unknown" if col == "posted_bucket" else pd.NA
                        )

                result_cols = [
                    "job_id", "job_title", "location",
                    "min_experience", "max_experience",
                    "avg_salary", "currency", "posted_bucket",
                    "skill_key", "skill_display_raw", "skill"
                ]

                result = hive_skills[result_cols].copy()

                result["min_experience"] = pd.to_numeric(
                    result["min_experience"], errors="coerce"
                )
                result["max_experience"] = pd.to_numeric(
                    result["max_experience"], errors="coerce"
                )
                result["avg_salary"] = pd.to_numeric(
                    result["avg_salary"], errors="coerce"
                )

                return result

        except Exception as exc:
            print(f"Hive skills export could not be loaded: {exc}")

    # Fallback: derive skills from the cleaned jobs export.
    records = []
    has_bucket = "posted_bucket" in jobs_df.columns

    subset = jobs_df[jobs_df["skills"].notna()].copy()
    subset = subset[
        subset["skills"].str.strip().str.lower() != "not specified"
    ]
    subset = subset[subset["skills"].str.strip() != ""]

    for row in subset.itertuples(index=False):
        raw_skills = getattr(row, "skills")
        seen_this_job = set()

        for piece in str(raw_skills).split(","):
            skill = piece.strip()
            if not skill:
                continue

            key = skill.casefold()
            if key in seen_this_job:
                continue

            seen_this_job.add(key)

            records.append((
                getattr(row, "job_id"),
                getattr(row, "job_title"),
                getattr(row, "location"),
                getattr(row, "min_experience"),
                getattr(row, "max_experience"),
                getattr(row, "avg_salary"),
                getattr(row, "currency"),
                getattr(row, "posted_bucket") if has_bucket else "Unknown",
                key,
                skill
            ))

    columns = [
        "job_id", "job_title", "location",
        "min_experience", "max_experience", "avg_salary",
        "currency", "posted_bucket", "skill_key",
        "skill_display_raw"
    ]

    long_df = pd.DataFrame(records, columns=columns)

    if long_df.empty:
        long_df["skill"] = pd.Series(dtype="object")
        return long_df

    display_map = (
        long_df.groupby(["skill_key", "skill_display_raw"]).size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .drop_duplicates(subset="skill_key")
        .set_index("skill_key")["skill_display_raw"]
    )

    long_df["skill"] = long_df["skill_key"].map(display_map)
    return long_df


def load_optional_hive_csv(filename: str, required_cols: list[str]) -> Optional[pd.DataFrame]:
    """
    Load an exported Hive/Pig result, normalizing Beeline column prefixes.
    Returns None if the file is absent, invalid, or lacks required columns.
    """
    path = HIVE_EXPORT_DIR / filename
    if not path.exists():
        return None

    try:
        df = pd.read_csv(path)
        df.columns = [
            str(col).split(".")[-1].strip()
            for col in df.columns
        ]
    except Exception as exc:
        print(f"Could not load Hive export {filename}: {exc}")
        return None

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Hive export {filename} is missing columns: {missing}")
        return None

    return df


def get_source_labels(meta: dict) -> str:
    if meta.get("source") == "hive_export":
        return (
            "Hive/Pig exports from dashboard/data/ "
            "(interactive filtering and some aggregations computed in Python)"
        )
    return (
        "Computed locally from the raw Excel dataset "
        "(Hive/Pig jobs_cleaned.csv export not found)"
    )

