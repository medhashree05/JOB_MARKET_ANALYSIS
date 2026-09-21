# Task 1 — Dataset + HDFS

Owner: (you)
Status: ✅ Complete — handoff point for Task 2 (Pig)

## What this task does

Takes the raw Naukri-style job postings dataset (`indian-job-market-dataset-2025.xlsx`,
~97.9K rows) and produces a clean, validated CSV loaded into HDFS at
`/jobmarket/cleaned/jobs_cleaned.csv`, ready for Pig to consume.

## How to run it (WSL)

WSL's system Python is "externally managed" (Debian/Ubuntu blocks plain `pip
install`), so dependencies are installed into a `uv`-managed virtual
environment instead of system-wide:

```bash
cd task1_hdfs

# 0. Create a venv and install dependencies from requirements.txt
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

cd scripts

# 1. Convert the source .xlsx to CSV (data/raw/jobs_raw.csv)
python3 01_convert_xlsx_to_csv.py

# 2. Clean + validate -> data/cleaned/jobs_cleaned.csv
python3 02_clean_data.py

# 3. Start Hadoop (if not already running) and load into HDFS
start-dfs.sh
bash 03_hdfs_load.sh

# 4. Verify HDFS upload + record counts
bash 04_verify_hdfs.sh
```

Requires: Python deps in `requirements.txt` (`pandas`, `openpyxl`) installed
via `uv` (see above), and a running Hadoop cluster.

Every new terminal session needs `source task1_hdfs/.venv/bin/activate` again
before running the Python scripts — the venv doesn't persist across shells.

**If `bash 03_hdfs_load.sh` fails with `Connection refused`:** HDFS isn't
running — run `start-dfs.sh` first, then `jps` to confirm `NameNode` and
`DataNode` are listed.

**If it fails with `Name node is in safe mode`:** this is normal right after
`start-dfs.sh` — the NameNode briefly checks its data blocks on startup.
Wait ~15–30 seconds and retry, or force it off:
```bash
hdfs dfsadmin -safemode leave
```

## HDFS structure produced

```
/jobmarket/
  raw/
    jobs_raw.csv        <- straight CSV conversion of the source xlsx, no cleaning
  cleaned/
    jobs_cleaned.csv     <- cleaned, validated, deduplicated (THIS is what Pig should read)
```

## Cleaning decisions made (read this before building on top of it)

The real dataset is messier than a toy example, so some judgment calls were made.
Documenting them here so Task 2/3 don't get surprised by the data:

| Issue in raw data | Decision |
|---|---|
| 250 duplicate `job_id`s | Kept first occurrence, dropped rest |
| 4 missing `company_name` | Filled with `"Unknown"` |
| 571 missing `skills` (tagsAndSkills) | Filled with `"Not Specified"` |
| 64,076 rows with `salary = "Not disclosed"` (source hardcodes min/max salary to `0`) | Converted to `NaN` (empty) — a real 0 would look identical to "unknown" otherwise. Genuine `"Unpaid"` postings (333 rows) keep `0` since that's a real value, not missing data. |
| `location` is a free-text, often multi-location string, e.g. `"Kolkata(Chinar Park)"` or `"Noida, Greater Noida"` | Derived a clean **primary** `location` column (first city, parenthetical dropped). Original kept as `location_raw` in case Pig/Hive need the full string. |
| `jobUploaded` is relative text (`"6 Days Ago"`, `"Just Now"`, `"Starts : 6th Oct' 25"`) with **no scrape date given** | Could NOT be converted to an absolute date without fabricating a reference date — that would produce fake `posted_date` values. Kept as-is in `posted_raw`. **Task 3 (Hive) time-trend analysis (2024/2025/2026 by year) is not directly supported by this column as-is** — see note below. |
| Rows with negative or logically inconsistent salary/experience (min > max) | Removed |
| Exact duplicate rows | Removed |

**Result: 97,929 raw rows → 97,679 cleaned rows (99.7% retained).**

### ⚠️ Note on time-based / emerging-skill trend analysis (spec section 3, analysis 5)

The spec's example (`Skill demand by year: 2024/2025/2026`) assumes the data has a
true `posted_date`. This dataset only has **relative recency text** (`posted_raw`),
which reflects the day it was scraped, not an actual historical timeline across years.
Two options for whoever does Task 3:
1. Treat it as a **relative recency bucket** instead (e.g. "posted this week" vs
   "posted 1-3 months out" vs "starts in future") rather than a year-over-year trend, or
2. If a true historical trend is required for the assignment, that needs a
   different/supplementary dataset with real posting dates — flag this to the
   instructor rather than fabricating dates.
Either way, don't silently invent a `posted_date` — say so in the final report.

## Cleaned schema (`jobs_cleaned.csv`) — contract for Task 2 (Pig)

| Column | Type | Notes |
|---|---|---|
| `job_id` | string (numeric id) | unique after dedup |
| `job_title` | string | |
| `company_name` | string | `"Unknown"` if missing |
| `company_id` | string (numeric id) | |
| `location` | string | cleaned primary city — **use this for location grouping** |
| `location_raw` | string | original multi-location text, kept for reference |
| `currency` | string | `INR` or `USD` |
| `min_salary` | float / empty | annual, in `currency` units; empty = not disclosed |
| `max_salary` | float / empty | same |
| `avg_salary` | float / empty | `(min_salary + max_salary) / 2`, empty if both missing |
| `experience_raw` | string | e.g. `"2-4 Yrs"` |
| `min_experience` | float | years |
| `max_experience` | float | years |
| `skills` | string | **comma-separated** (not semicolon — see below), `"Not Specified"` if missing |
| `posted_raw` | string | relative recency text — see time-trend note above |
| `reviews_count` | float / empty | company review count, often missing |
| `rating` | float / empty | company rating out of 5, often missing |

**Important for Pig (Task 2, step 6 "split the skills column"):** skills are
comma-separated in this dataset (e.g. `"Python,SQL,Machine Learning"`), NOT
semicolon-separated like the spec's toy example. Split on `,` not `;`.

## Sample cleaned record

```json
{
  "job_id": "270925008041",
  "job_title": "Sr. HR Recruiter (NON IT)",
  "company_name": "Orion",
  "company_id": "645563",
  "location": "Kolkata",
  "location_raw": "Kolkata(Chinar Park)",
  "currency": "INR",
  "min_salary": 200000.0,
  "max_salary": 400000.0,
  "avg_salary": 300000.0,
  "experience_raw": "2-4 Yrs",
  "min_experience": 2.0,
  "max_experience": 4.0,
  "skills": "Communication,Manpower,Staffing,Convincing Power,Hiring,Recruitment,SR,Communication skills",
  "posted_raw": "6 Days Ago",
  "reviews_count": null,
  "rating": null
}
```

## Handoff to Task 2 (Pig)

- Load from HDFS: `/jobmarket/cleaned/jobs_cleaned.csv`
- It's a standard comma-delimited CSV **with a header row** — `LOAD ... USING PigStorage(',')`
  then drop/skip row 1, or load with an explicit schema matching the table above.
- Split `skills` on `,` (see note above).
- Output your processed datasets to `/jobmarket/processed/{jobs,skills,location,salary,time_based}/`
  as laid out in the top-level project README / spec.