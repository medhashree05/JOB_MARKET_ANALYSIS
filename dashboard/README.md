# Job Market Intelligence Dashboard

An interactive Streamlit dashboard that presents the results of the
**Large-Scale Job Market Intelligence and Emerging Skill Demand Analysis**
project (HDFS + Apache Pig + Apache Hive). This folder is a presentation
layer only — it does **not** replace or re-implement the big-data pipeline
in `task1_hdfs/`, `task2_pig/`, `task3_hive/`.

## Architecture

```
dashboard/
├── app.py            # UI + page routing (Streamlit)
├── data_loader.py     # Loads + cleans data; replicates the Task 1 cleaning
│                       # contract when Hive/Pig exports aren't available
├── analytics.py       # Pure calculation functions (no UI, no plotting)
├── charts.py          # Plotly figure builders
├── requirements.txt   # Dashboard-only Python dependencies
├── .streamlit/
│   └── config.toml    # Theme
└── data/               # Optional: drop Hive/Pig CSV exports here (gitignored)
```

**Data source priority:**
1. If `dashboard/data/jobs_cleaned.csv` exists (a real export of the Task 1
   HDFS output), it's used directly.
2. Otherwise the dashboard reads `dataset/indian-job-market-dataset-2025.xlsx`
   and re-applies the exact cleaning rules documented in
   `task1_hdfs/README.md` / `task1_hdfs/scripts/02_clean_data.py` (dedup,
   `"Not disclosed"` → NaN salary fix, primary-location extraction, etc.), so
   the numbers match what the real pipeline produces.

The active source is always shown as a small badge at the top of every page,
and Page 6 (Emerging Skill Trends) will automatically pick up
`dashboard/data/time_based.csv` if a real Hive time-based aggregate is ever
exported (columns: `period, skill, postings`).

The dashboard **never** presents a number computed from the raw Excel file
as if it came from Hive or Pig.

## Prerequisites

- Python 3.9+
- The dataset already present at `dataset/indian-job-market-dataset-2025.xlsx`
  (already in the repo)
- No running Hadoop/Pig/Hive cluster is required to view the dashboard

## Installation (Windows PowerShell)

```powershell
cd D:\JOB_MARKET_ANALYSIS
python -m venv .venv-dashboard
.\.venv-dashboard\Scripts\Activate.ps1
pip install -r dashboard\requirements.txt
```

(If you're on WSL/macOS/Linux, use `python3 -m venv` and
`source .venv-dashboard/bin/activate` instead.)

## Running it

```powershell
streamlit run dashboard/app.py
```

Then open **http://localhost:8501** in your browser (Streamlit opens it
automatically by default).

## Using real Hive/Pig outputs (optional)

If you've run the full pipeline and exported results, drop CSVs into
`dashboard/data/` (this folder is gitignored so large exports never get
committed):

| File | Required columns | Used by |
|---|---|---|
| `jobs_cleaned.csv` | same as the Task 1 schema contract in `task1_hdfs/README.md` | replaces the Excel-fallback cleaning for every page |
| `time_based.csv` | `period, skill, postings` | Page 6, Emerging Skill Trends — only if you have a dataset with real historical posting dates |

Any file that's missing or doesn't match the expected columns is silently
ignored and the dashboard falls back to computing the same thing from the
Excel dataset — it will never crash because an optional export isn't there.

## Pages

1. **Executive Overview** — KPIs, top roles/skills/locations, automated insights
2. **Skill Demand Intelligence** — top 20 skills, per-skill drill-down, co-occurrence
3. **Salary Analytics** — by role/location/skill/experience, with disclosed-salary-only disclosure
4. **Location & Hiring** — top locations, per-location drill-down
5. **Experience & Job Roles** — demand and salary by experience bucket, top skills per level
6. **Emerging Skill Trends** — honest treatment of the dataset's lack of real historical dates (see below)
7. **Data Explorer** — searchable/filterable table with CSV export

## Known data limitations (disclosed in the UI, not hidden)

- **No absolute posting date.** `jobUploaded` is relative recency text only
  ("6 Days Ago", "Starts in 1-3 months") with no scrape date, so a true
  year-over-year "emerging skill" trend cannot be computed without
  fabricating dates — the dashboard says so explicitly on Page 6 instead of
  inventing one.
- **Salary** is disclosed for ~34% of postings; the rest are excluded from
  salary statistics (never treated as ₹0), and INR/USD postings are never
  averaged together.
- **Skills** are parsed from a free-text, comma-separated field with no
  controlled vocabulary, so near-duplicate variants (e.g. different casing)
  are grouped for counting but the most common original casing is shown.

## Testing performed

- `python -m py_compile` on all four dashboard modules
- Data-loading logic validated against the real dataset: 97,929 raw rows →
  97,679 cleaned rows, 250 duplicates removed (matches `task1_hdfs/README.md`)
- All 7 pages exercised with Streamlit's `AppTest` harness — no exceptions
- Sidebar filters (location, role, experience, salary range) and the Reset
  Filters button exercised via `AppTest` — no exceptions
- `streamlit run app.py --server.headless true` smoke-tested; server started
  and served HTTP 200 with no errors in the log
