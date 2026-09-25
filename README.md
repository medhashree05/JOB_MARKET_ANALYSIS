# Large-Scale Job Market Intelligence and Emerging Skill Demand Analysis
### Using HDFS, Pig, and Hive

Dataset: [Indian Job Market Dataset 2025](.) (Naukri-style scrape, ~97.9K job postings)

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
Transformed + Aggregated Data  (/jobmarket/processed/{jobs,skills,skills_demand,location,salary,salary_location,time_based}/)
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
├── task2_pig/           # Pig scripts and reproducible runner
├── task3_hive/          # Hive scripts, queries, runner, and status report
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
6. Write outputs to `/jobmarket/processed/{jobs,skills,skills_demand,location,salary,salary_location,time_based}/`

Run the reproducible Pig stage with:

```bash
bash task2_pig/scripts/run_task2_pig.sh
```

## Task 3 (Hive) — what's expected

Read processed data from `/jobmarket/processed/`, then:
1. Create Hive DB + tables: `jobs`, `job_skills`, `job_locations`, `job_salary`, `salary_by_location`, `skills_demand`, `time_based`, `skill_trends`
2. Run the analyses: top job roles, top skills, demand by location, salary by role/location,
   skill+role combinations, and skill-demand-over-time / emerging skills
   (see the time-trend caveat in `task1_hdfs/README.md` first)
3. Produce the final job market intelligence output

The complete reproduction guide and current implementation notes are in
[`task3_hive/PROJECT_STATUS.md`](task3_hive/PROJECT_STATUS.md). The dataset's
`posted_raw` field is mostly relative text, so skill trends are explicit-year-only
when a year is present; they are not a fabricated 2024/2025/2026 history.

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

## Git workflow

`.gitignore` excludes the large/generated files (`.venv/`, raw `.xlsx`/`.csv`,
`data/cleaned/*.csv`, Hadoop/Hive/Pig log junk) so the repo only carries
scripts, docs, and config — not multi-hundred-MB data files.

```bash
git add .
git status   # sanity check BEFORE committing — confirm none of these show up:
             #   task1_hdfs/.venv/
             #   data/raw/*.xlsx, data/raw/*.csv
             #   data/cleaned/*.csv
git commit -m "Describe what you changed"
git push
```

If a data file or `.venv/` ever shows up as staged (usually because it got
committed before `.gitignore` existed), untrack it rather than just deleting
it — deleting alone won't stop git from tracking it:

```bash
git rm -r --cached task1_hdfs/.venv data/raw/*.csv data/raw/*.xlsx data/cleaned/*.csv 2>/dev/null
git commit -m "Remove large/generated files from tracking"
git push
```

**For teammates picking up Task 2/3:** after `git pull`, the `data/` files
won't be there (gitignored) — either regenerate them locally with the Task 1
scripts above, or pull the cleaned CSV straight from HDFS if you're sharing
the same cluster:
```bash
hdfs dfs -get /jobmarket/cleaned/jobs_cleaned.csv data/cleaned/
```

## Interactive Dashboard

A separate, self-contained Streamlit dashboard in [`dashboard/`](dashboard/)
presents the results of the pipeline above for a live demo — KPIs, skill
demand, salary analytics, location/hiring, experience breakdowns, an honest
treatment of "emerging skills" given the dataset's lack of real historical
dates, and a searchable data explorer with CSV export.

**It does not require Hadoop, Pig, or Hive to be running.** It reads the raw
Excel dataset and replicates the exact Task 1 cleaning contract
(`task1_hdfs/README.md`) by default, and will automatically prefer real
exported Hive/Pig CSVs if you drop them into `dashboard/data/` — the active
data source is always shown in the UI.

### Architecture

```
dashboard/
├── app.py            # UI + page routing
├── data_loader.py     # cleaning + optional Hive/Pig CSV adapters
├── analytics.py       # KPI / aggregation logic
├── charts.py          # Plotly figure builders
└── requirements.txt
```

### Prerequisites

- Python 3.9+
- `dataset/indian-job-market-dataset-2025.xlsx` present (already in the repo)

### Installation (Windows PowerShell)

```powershell
cd D:\JOB_MARKET_ANALYSIS
python -m venv .venv-dashboard
.\.venv-dashboard\Scripts\Activate.ps1
pip install -r dashboard\requirements.txt
```

### Run it

```powershell
streamlit run dashboard/app.py
```

Open **http://localhost:8501**.

### Configuring Hive CSV exports (optional)

Drop `jobs_cleaned.csv` (Task 1 schema) or `time_based.csv`
(`period, skill, postings`) into `dashboard/data/` and the dashboard will use
them automatically instead of recomputing from the raw Excel file — see
[`dashboard/README.md`](dashboard/README.md) for the full contract.

### Screenshots

_Add screenshots here after running the dashboard locally, e.g.:_
```markdown
![Executive Overview](docs/screenshots/executive-overview.png)
![Skill Demand Intelligence](docs/screenshots/skill-demand.png)
```

Full dashboard setup, page-by-page documentation, and known data
limitations: [`dashboard/README.md`](dashboard/README.md).
