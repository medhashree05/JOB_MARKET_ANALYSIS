"""
Step 1 of Task 1 (HDFS): convert the raw Excel dataset to CSV.

Hadoop/Pig/Hive don't read .xlsx natively, so the very first thing we do
is convert the source file to CSV and treat THAT as the "raw" artifact
that goes into HDFS at /jobmarket/raw/jobs_raw.csv.

The original .xlsx is kept in data/raw/ purely as the source-of-truth
backup; it is NOT what gets uploaded to HDFS.

Usage:
    python3 01_convert_xlsx_to_csv.py
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_XLSX = PROJECT_ROOT / "data" / "raw" / "indian-job-market-dataset-2025.xlsx"
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "jobs_raw.csv"


def main():
    if not RAW_XLSX.exists():
        raise FileNotFoundError(
            f"Expected raw file at {RAW_XLSX}. Put the dataset there first."
        )

    print(f"Reading {RAW_XLSX} ...")
    df = pd.read_excel(RAW_XLSX)
    print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV, index=False)
    print(f"Wrote raw CSV -> {RAW_CSV} ({RAW_CSV.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
