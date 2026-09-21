# Large-Scale Job Market Intelligence and Emerging Skill Demand Analysis
### Using HDFS, Pig, and Hive

Dataset: [Indian Job Market Dataset 2025](.) (Naukri-style scrape, ~97.9K job postings)

## Team split

| Task | Owner | Status |
|---|---|---|
| Task 1 — Dataset + HDFS | you | ✅ Done |
| Task 2 — Pig (aggregation) | teammate | ⬜ Not started — see below |
| Task 3 — Hive (analytics) | teammate | ⬜ Not started — see below |

## Pipeline

```
Raw Job Market Dataset (.xlsx)
        ↓
Task 1: HDFS   — convert, clean, validate, dedupe, load to HDFS
        ↓
Cleaned + Validated Dataset  (/jobmarket/cleaned/jobs_cleaned.csv)
        ↓
Task 2: Pig    — normalize, split skills, group by role/location/skill, aggregate salary
        ↓
Transformed + Aggregated Data  (/jobmarket/processed/{jobs,skills,location,salary,time_based}/)
        ↓
Task 3: Hive   — tables + queries: demand by role/location/skill, salary trends, emerging skills
        ↓
Final Job Market Intelligence Report
```

## Project structure

```
.
├── data/
│   ├── raw/            # source .xlsx + converted jobs_raw.csv (also mirrored in HDFS /jobmarket/raw/)
│   └── cleaned/         # jobs_cleaned.csv (also mirrored in HDFS /jobmarket/cleaned/)
├── docs/                # write-ups, final report, diagrams
├── task1_hdfs/
│   ├── scripts/         # 01_convert_xlsx_to_csv.py, 02_clean_data.py, 03_hdfs_load.sh, 04_verify_hdfs.sh
│   └── README.md        # full schema contract + cleaning decisions — READ THIS before Task 2
├── task2_pig/           # <- Pig scripts go here (teammate)
├── task3_hive/          # <- Hive scripts/queries go here (teammate)
└── README.md            # this file
```

## Where Task 1 left off (start here for Task 2)

- **Input for Pig**: HDFS path `/jobmarket/cleaned/jobs_cleaned.csv`
- **Full column list, types, and cleaning caveats**: see [`task1_hdfs/README.md`](task1_hdfs/README.md)
  — in particular, note that `skills` is **comma-separated** (not semicolon like the
  original spec example) and there's an important caveat about `posted_raw` not
  being a true date (relative-time text only) — read it before doing the
  time-based trend analysis in Task 3.
- To regenerate everything from scratch:
  ```bash
  cd task1_hdfs
  uv venv && source .venv/bin/activate
  uv pip install -r requirements.txt
  cd scripts
  python3 01_convert_xlsx_to_csv.py
  python3 02_clean_data.py
  start-dfs.sh
  bash 03_hdfs_load.sh
  bash 04_verify_hdfs.sh
  ```

## Task 2 (Pig) — what's expected

Read cleaned data from `/jobmarket/cleaned/jobs_cleaned.csv`, then:
1. Define schema matching `task1_hdfs/README.md`
2. Filter any remaining invalid records
3. Normalize job titles / locations
4. Split `skills` on `,` into individual skill rows
5. Group by job role, location, and skill; compute counts and avg/min/max salary
6. Write outputs to `/jobmarket/processed/{jobs,skills,location,salary,time_based}/`

## Task 3 (Hive) — what's expected

Read processed data from `/jobmarket/processed/`, then:
1. Create Hive DB + tables: `jobs`, `job_skills`, `job_locations`, `job_salary`, `skill_trends`
2. Run the analyses: top job roles, top skills, demand by location, salary by role/location,
   skill+role combinations, and skill-demand-over-time / emerging skills
   (see the time-trend caveat in `task1_hdfs/README.md` first)
3. Produce the final job market intelligence output

## Setup

WSL's system Python is externally managed (plain `pip install` is blocked),
so dependencies go into a `uv`-managed venv instead:

```bash
cd task1_hdfs
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cd ..

# Hadoop, Pig, Hive assumed installed in WSL and on PATH
start-dfs.sh   # start HDFS before running task1 scripts
jps            # confirm NameNode/DataNode are up
```

Note: `source task1_hdfs/.venv/bin/activate` needs to be re-run in every new
terminal session before running the Python scripts — the venv doesn't persist
across shells. If `start-dfs.sh` gives `Connection refused` on later commands,
Hadoop just isn't running yet; if you get `Name node is in safe mode` right
after starting it, wait ~15–30s and retry (or run `hdfs dfsadmin -safemode leave`).