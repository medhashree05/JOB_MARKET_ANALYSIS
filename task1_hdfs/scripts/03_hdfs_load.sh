#!/usr/bin/env bash
# Step 3 of Task 1 (HDFS): upload raw + cleaned data into HDFS.
#
# Run this from WSL, from anywhere, AFTER:
#   1) Hadoop daemons are running (start-dfs.sh)
#   2) 01_convert_xlsx_to_csv.py and 02_clean_data.py have been run
#
# Usage:
#   bash 03_hdfs_load.sh

set -euo pipefail

# Resolve project root relative to this script (task1_hdfs/scripts/../..)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RAW_CSV="$PROJECT_ROOT/data/raw/jobs_raw.csv"
CLEANED_CSV="$PROJECT_ROOT/data/cleaned/jobs_cleaned.csv"

for f in "$RAW_CSV" "$CLEANED_CSV"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing $f — run the python scripts first." >&2
    exit 1
  fi
done

echo ">>> Creating HDFS directory structure under /jobmarket ..."
hdfs dfs -mkdir -p /jobmarket/raw
hdfs dfs -mkdir -p /jobmarket/cleaned

echo ">>> Uploading raw dataset ..."
hdfs dfs -put -f "$RAW_CSV" /jobmarket/raw/jobs_raw.csv

echo ">>> Uploading cleaned dataset ..."
hdfs dfs -put -f "$CLEANED_CSV" /jobmarket/cleaned/jobs_cleaned.csv

echo ">>> Done. Current HDFS structure:"
hdfs dfs -ls -R /jobmarket
