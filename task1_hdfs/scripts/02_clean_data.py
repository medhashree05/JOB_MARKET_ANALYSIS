"""
Step 2 of Task 1 (HDFS): clean + validate the raw job market data.

Implements, against the REAL dataset columns (not the toy spec example):
  - standardize column names (snake_case, meaningful names)
  - validate records (required fields present)
  - handle missing values (documented per-column decisions below)
  - remove duplicate job postings (exact dup rows AND duplicate job_id)
  - remove invalid salary / experience records
  - derive a clean primary "location" from the messy multi-location string
  - write data/cleaned/jobs_cleaned.csv, ready for Task 2 (Pig)

Run AFTER 01_convert_xlsx_to_csv.py.

Usage:
    python3 02_clean_data.py
"""

import re
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "jobs_raw.csv"
CLEANED_CSV = PROJECT_ROOT / "data" / "cleaned" / "jobs_cleaned.csv"

# Source -> standardized column names
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


def clean_location(raw: str) -> str:
    """'Kolkata(Chinar Park)' -> 'Kolkata'; 'Gandhinagar, Ahmedabad' -> 'Gandhinagar'."""
    if not isinstance(raw, str) or not raw.strip():
        return "Unknown"
    first = raw.split(",")[0]
    first = re.sub(r"\(.*?\)", "", first)  # drop parenthetical area
    return first.strip() or "Unknown"


def main():
    print(f"Reading {RAW_CSV} ...")
    df = pd.read_csv(RAW_CSV, dtype={"jobId": str, "companyId": str})
    n_start = len(df)
    print(f"Loaded {n_start:,} raw rows")

    # 1. Standardize column names
    df = df.rename(columns=RENAME_MAP)

    # 2. Trim whitespace on string columns
    str_cols = ["job_title", "company_name", "location_raw", "skills",
                "experience_raw", "salary_raw", "posted_raw"]
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"nan": ""})
        df[c] = df[c].str.replace(r"[\r\n]+", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()

    # 3. Remove exact duplicate rows, then duplicate job_id (keep first)
    n_before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="job_id", keep="first")
    print(f"Removed {n_before - len(df):,} duplicate rows/job_ids")

    # 4. Validate required fields: job_id, job_title, location must exist
    n_before = len(df)
    df = df[(df["job_id"].astype(str).str.strip() != "") &
            (df["job_title"] != "") &
            (df["location_raw"] != "")]
    print(f"Removed {n_before - len(df):,} rows missing required fields "
          f"(job_id/job_title/location)")

    # 5. Handle missing values
    df["company_name"] = df["company_name"].replace("", "Unknown")
    df["skills"] = df["skills"].replace("", "Not Specified")
    df["reviews_count"] = pd.to_numeric(df["reviews_count"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # 6. Fix salary: "Not disclosed" rows have min/max hardcoded to 0 in the
    #    source, which is misleading (0 looks like a real free/unpaid salary).
    #    Set those to NaN instead; genuine "Unpaid" postings keep 0.
    df["min_salary"] = pd.to_numeric(df["min_salary"], errors="coerce")
    df["max_salary"] = pd.to_numeric(df["max_salary"], errors="coerce")
    not_disclosed_mask = df["salary_raw"].str.lower().str.contains("not disclosed", na=False)
    df.loc[not_disclosed_mask, ["min_salary", "max_salary"]] = pd.NA

    # 7. Remove invalid salary/experience records
    #    (negative values, or min > max when both are known)
    n_before = len(df)
    df["min_experience"] = pd.to_numeric(df["min_experience"], errors="coerce")
    df["max_experience"] = pd.to_numeric(df["max_experience"], errors="coerce")

    bad_salary = ((df["min_salary"] < 0) | (df["max_salary"] < 0) |
                  ((df["min_salary"] > df["max_salary"]) & df["max_salary"].notna() & (df["max_salary"] > 0)))
    bad_experience = ((df["min_experience"] < 0) | (df["max_experience"] < 0) |
                       ((df["min_experience"] > df["max_experience"]) & df["max_experience"].notna()))
    df = df[~(bad_salary.fillna(False) | bad_experience.fillna(False))]
    print(f"Removed {n_before - len(df):,} rows with invalid salary/experience")

    # 8. Derived columns
    df["avg_salary"] = df[["min_salary", "max_salary"]].mean(axis=1)
    df["location"] = df["location_raw"].apply(clean_location)

    # 9. Final column order/selection
    df = df[FINAL_COLUMNS]

    CLEANED_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEANED_CSV, index=False)

    print(f"\nFinal cleaned rows: {len(df):,} / {n_start:,} "
          f"({len(df) / n_start:.1%} retained)")
    print(f"Wrote -> {CLEANED_CSV} ({CLEANED_CSV.stat().st_size / 1e6:.1f} MB)")
    print("\nSample:")
    print(df.head(3).to_string())


if __name__ == "__main__":
    main()
