#!/usr/bin/env bash
# Step 4 of Task 1 (HDFS): verify uploaded files and record counts.
#
# Usage:
#   bash 04_verify_hdfs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RAW_CSV="$PROJECT_ROOT/data/raw/jobs_raw.csv"
CLEANED_CSV="$PROJECT_ROOT/data/cleaned/jobs_cleaned.csv"

echo "=== HDFS file listing ==="
hdfs dfs -ls -R /jobmarket

echo
echo "=== File sizes (hdfs -du -h) ==="
hdfs dfs -du -h /jobmarket/raw /jobmarket/cleaned

echo
echo "=== Record counts: local vs HDFS ==="
local_raw_count=$(($(wc -l < "$RAW_CSV") - 1))          # minus header
local_cleaned_count=$(($(wc -l < "$CLEANED_CSV") - 1))  # minus header
hdfs_raw_count=$(($(hdfs dfs -cat /jobmarket/raw/jobs_raw.csv | wc -l) - 1))
hdfs_cleaned_count=$(($(hdfs dfs -cat /jobmarket/cleaned/jobs_cleaned.csv | wc -l) - 1))

echo "Raw      -> local: $local_raw_count   | hdfs: $hdfs_raw_count"
echo "Cleaned  -> local: $local_cleaned_count   | hdfs: $hdfs_cleaned_count"

if [[ "$local_raw_count" -eq "$hdfs_raw_count" && "$local_cleaned_count" -eq "$hdfs_cleaned_count" ]]; then
  echo
  echo "✅ Verification passed: record counts match."
else
  echo
  echo "❌ Verification FAILED: counts do not match." >&2
  exit 1
fi
