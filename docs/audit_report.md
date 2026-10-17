# Comprehensive Audit Report: Big Data Job Market Analysis

**Project Title:** Large-Scale Job Market Intelligence and Emerging Skill Demand Analysis Using HDFS, Apache Pig, and Apache Hive  
**Course:** CSE412 — Big Data & Large-Scale Computing, IIIT Kottayam  
**Student Team:**  
- N Medhashree (2023BCS0042)  
- Ashmi S N (2023BCS0196)  
- Deepanjali Tudu (2023BCS0066)  
**Auditor / Date:** Big Data Technical Auditor, October 2026  
**Repository Location:** `D:\JOB_MARKET_ANALYSIS` (WSL: `/mnt/d/JOB_MARKET_ANALYSIS`)

---

## 1. Executive Summary

This audit evaluated the implementation artifacts, execution logs, distributed storage filesystems (HDFS), data pipelines (Python, Apache Pig, Apache Hive), and presentation layers (Streamlit, Plotly) of the *Job Market Intelligence* project.

### Key Audit Findings:
1. **Phase I Pipeline (Verified and Highly Reproducible):**
   - The Stage 1 (Python HDFS ingestion and cleaning), Stage 2 (Apache Pig transformations over MapReduce), and Stage 3 (Apache Hive tables and HiveQL analytical scripts) exist, are completely implemented, and were successfully executed on the local WSL Hadoop cluster.
   - Verified HDFS storage blocks and offline NameNode metadata (`fsimage_0000000000000029319`) confirm genuine MapReduce execution on 2026-09-25 with complete `_SUCCESS` markers across all seven Pig output directories (`/jobmarket/processed/{jobs, skills, skills_demand, location, salary, salary_location, time_based}`).
   - Hive external tables and the managed `skill_trends` table were created in database `jobmarket` in the Hive warehouse (`/user/hive/warehouse/jobmarket.db/skill_trends`).

2. **Root Cause of Numerical Discrepancies (Fully Resolved):**
   - **97,679 vs. 97,715 Records:** The true ground truth after Task 1 cleaning is **97,679** unique job postings. The figure 97,715 in the report arose because 36 unescaped newline characters within raw text fields (such as multi-line job titles or location strings) caused 36 broken record fragments during Hive/Pig quoted-CSV text export into `dashboard/data/jobs_cleaned.csv`.
   - **18,320 vs. 18,310 Bengaluru Postings:** The true ground truth count for Bengaluru is **18,320**. Exactly 10 postings located in Bengaluru had embedded line breaks in preceding fields, which shifted `"Bengaluru"` into the `job_id` column of the split lines, reducing the parsed Bengaluru count to 18,310 in the export dataset.
   - **Skill Counts (Sales: 9,178 vs. 9,175; Python: 5,846 vs. 5,841):** Directly mirrors the same text-split phenomenon where 3 to 5 postings containing these skills were corrupted across newline boundaries during CSV export.

3. **Phase II and SDVI Status (Unimplemented / Unverified):**
   - No source data (`linkedin_postings.csv`), no extraction scripts (`clean_and_extract.pig`), no Jython UDFs, no Hive partition scripts (`sdvi_query.hql`), no exported JSON (`sdvi_results.json`), and no HTML5 canvas dashboard (`index.html`) exist in the repository, local filesystem, Git history, or HDFS cluster.
   - An offline inspection of HDFS NameNode FSImage confirmed that no path matching `/user/ashmi_sn/` or `linkedin` ever existed on the cluster.
   - Mathematical audit of the stated SDVI quadrant rules revealed a fundamental logical impossibility: since $\text{SDVI} = \text{growth\_rate} \times \ln(1 + \text{mentions})$, any skill with $\text{growth\_rate} \le 0$ must have $\text{SDVI} \le 0$. Consequently, the condition for *Stable Core* ($\text{growth\_rate} \le 0 \land \text{SDVI} > \text{median}$) is mathematically unsatisfiable whenever $\text{median} > 0$. High-volume incumbent skills with flat growth ($G = 0$) receive $\text{SDVI} = 0$, improperly placing them in the *Declining* quadrant under the report's rule.

4. **Dashboard Presentation Layer (Verified):**
   - The Streamlit dashboard (`dashboard/app.py`) is fully functional and decoupled from live Hadoop services. It features 7 distinct pages, extensive interactive sidebar filtering, and an active CSV export button on the Data Explorer page.

---

## 2. Repository Inventory and File Provenance

| Relative Path | Primary Purpose | Evidence for Report Claims | Verification Status |
|---|---|---|---|
| `dataset/indian-job-market-dataset-2025.xlsx` | Raw source dataset (Naukri scrape, 31.7 MB, 97,929 rows) | Raw input data source, 17 raw columns | **Verified** |
| `data/raw/jobs_raw.csv` | Direct CSV conversion of raw Excel file (84.1 MB) | Pre-cleaning intermediate file | **Verified** |
| `data/cleaned/jobs_cleaned.csv` | Cleaned, deduplicated Phase I dataset (24.3 MB, 97,679 rows) | Task 1 schema contract, baseline metrics | **Verified (Ground Truth)** |
| `task1_hdfs/scripts/01_convert_xlsx_to_csv.py` | Converts `.xlsx` to CSV via pandas/openpyxl | Raw ingestion step | **Verified** |
| `task1_hdfs/scripts/02_clean_data.py` | Cleaning, deduplication, salary validation, location parsing | Data cleaning methodology | **Verified** |
| `task1_hdfs/scripts/03_hdfs_load.sh` | Shell script loading raw and cleaned data into HDFS | Distributed loading | **Verified** |
| `task1_hdfs/scripts/04_verify_hdfs.sh` | Read-only HDFS verification script | HDFS integrity checks | **Verified** |
| `task1_hdfs/README.md` | Schema contract, field definitions, and cleaning rationale | Data engineering documentation | **Verified** |
| `task2_pig/scripts/task2_jobmarket.pig` | Apache Pig Latin script (Piggybank `CSVExcelStorage`, MapReduce) | Large-scale transformations | **Verified** |
| `task2_pig/scripts/run_task2_pig.sh` | Reusable Bash runner for Pig with JobHistoryServer checks | Execution orchestration | **Verified** |
| `task2_pig/README.md` | Pig execution instructions and intermediate aggregate outputs | Output specifications | **Verified** |
| `task3_hive/scripts/01_create_tables.sql` | Hive DDL creating external tables with `OpenCSVSerde` | Warehouse metadata layer | **Verified** |
| `task3_hive/scripts/02_build_skill_trends.sql` | HiveQL building `skill_trends` using `LAG()` window function | Temporal analysis attempt | **Verified** |
| `task3_hive/scripts/03_analysis.sql` | Analytical HiveQL queries (roles, skills, locations, salary) | Core analytical findings | **Verified** |
| `task3_hive/scripts/04_screenshot_queries.sql` | Formatted queries for report demonstration | Analytical results | **Verified** |
| `task3_hive/scripts/run_task3_hive.sh` | Hive Beeline automation runner | Execution orchestration | **Verified** |
| `task3_hive/PROJECT_STATUS.md` | Reproduction notes and run log summary (2026-09-22 run) | Execution history | **Verified** |
| `task3_hive/README.md` | Table schemas, query definitions, interpretation guidelines | Hive documentation | **Verified** |
| `dashboard/app.py` | 7-page Streamlit dashboard application (24.1 KB) | Presentation layer | **Verified** |
| `dashboard/data_loader.py` | Data loading and caching layer; fallback Excel cleaning contract | Data ingestion priority | **Verified** |
| `dashboard/analytics.py` | Pure analytical calculation functions (KPIs, distributions) | Dashboard metric computation | **Verified** |
| `dashboard/charts.py` | Plotly visualization generators | Interactive charts | **Verified** |
| `dashboard/data/jobs_cleaned.csv` | Exported Hive/Pig table (97,715 lines, newline-fragmented) | Origin of 97,715 count | **Verified (Flawed Export)** |
| `dashboard/data/skills_demand.csv` | Exported Pig `skills_demand` table (44,065 unique skills) | Pig aggregate output | **Verified** |
| `dashboard/data/job_skills.csv` | Exported Pig `job_skills` table (53.3 MB) | Job-skill exploded pairs | **Verified** |
| `dashboard/data/time_based.csv` | Exported Pig `time_based` table (relative recency buckets) | Time-trend limitations | **Verified** |
| `docs/screenshots/executive-overview.png` | Real screenshot of dashboard Executive Overview page | Visual evidence | **Verified** |
| `docs/screenshots/skill-demand.png` | Real screenshot of dashboard Skill Demand page | Visual evidence | **Verified** |
| `docs/report.tex` | Original supplied academic LaTeX report | Baseline report text | **Preserved** |
| `Phase II Files` (`linkedin_postings.csv`, `clean_and_extract.pig`, `sdvi_query.hql`, `sdvi_results.json`, `index.html`) | LinkedIn time-series ingestion, Jython UDF, SDVI calculation, HTML dashboard | Phase II claims | **MISSING / UNVERIFIED** |

---

## 3. Verification Commands and Cluster Environment

### 3.1 Environment Overview
- **Host OS:** Windows 11 Enterprise (64-bit)
- **WSL Subsystem:** Ubuntu 22.04 LTS (WSL 2)
- **WSL User:** `medha`
- **Java Runtime:** OpenJDK 1.8.0_422 (`/usr/lib/jvm/java-8-openjdk-amd64`)
- **Hadoop Stack:** Apache Hadoop 3.3.6 (`/usr/local/hadoop`)
- **Pig Engine:** Apache Pig 0.17.0 (`/usr/local/pig`)
- **Hive Warehouse:** Apache Hive 3.1.3 (`/usr/local/hive`)
- **Python Runtimes:** Python 3.12 (WSL `.venv`), Python 3.13 (`dashboard/.venv`)
- **LaTeX Distribution:** MiKTeX 26.5 (Windows 64-bit; `pdflatex`, `xelatex`, `latexmk` installed)

### 3.2 HDFS Offline and Online Verification
To verify the actual state of the Hadoop distributed cluster without risking accidental data overwrite or deletion, two methods were employed:

1. **Online HDFS Ingestion Check:**
   ```bash
   start-dfs.sh
   hdfs dfsadmin -safemode get
   hdfs dfs -ls /jobmarket
   hdfs dfs -ls /jobmarket/processed
   ```
   *Result:* Returned active NameNode on port 9000 and DataNode on port 9866. All 7 processed directories (`jobs`, `location`, `salary`, `salary_location`, `skills`, `skills_demand`, `time_based`) contained `_SUCCESS` markers and valid part files.

2. **Offline Image Viewer (PBImageTextWriter):**
   ```bash
   latest_image=$(ls -1 /home/medha/hadoopdata/hdfs/namenode/current/fsimage_* | grep -v '\.md5$' | tail -n 1)
   hdfs oiv -i "$latest_image" -o /tmp/fsimage.tsv -p Delimited
   ```
   *Result:* Scanned 694 INodes. Verified complete file trees for:
   - `/jobmarket/raw/jobs_raw.csv` (84,148,964 bytes)
   - `/jobmarket/cleaned/jobs_cleaned.csv` (24,255,287 bytes)
   - `/jobmarket/processed/jobs/part-m-00000` (24,254,380 bytes)
   - `/jobmarket/processed/skills/part-r-00000` (53,363,947 bytes)
   - `/jobmarket/processed/skills_demand/part-r-00000` (876,713 bytes)
   - `/user/hive/warehouse/jobmarket.db/skill_trends/000000_0` (1,449,549 bytes)
   Confirmed zero records matching `ashmi`, `linkedin`, or `sdvi`.

---

## 4. Stage-by-Stage Verification Findings

### 4.1 Task 1: Ingestion, Cleaning, and HDFS Loading
- **Raw Input:** `dataset/indian-job-market-dataset-2025.xlsx` contains 97,929 rows and 17 columns.
- **Deduplication:**
  - 247 exact duplicate rows were identified and removed.
  - 3 additional rows sharing existing `job_id` values were dropped, removing a total of **250 duplicate records** ($97,929 - 250 = 97,679$).
- **Missing Required Fields:** 0 rows were missing `job_id`, `job_title`, or `location_raw`.
- **Invalid Salaries/Experience:** 0 rows exhibited negative values or minimums exceeding maximums after "Not disclosed" strings were mapped to `NaN`.
- **Salary Sanitization:** In the raw dataset, 64,076 rows had `salary = "Not disclosed"` with min/max salary artificially hardcoded to `0.0`. Task 1 correctly converted these to `NaN` so they are not conflated with genuine unpaid internships (333 postings with true 0 compensation).
- **HDFS Loading:** Script `03_hdfs_load.sh` successfully loaded the resulting 97,679 rows into `/jobmarket/cleaned/jobs_cleaned.csv` (24,255,287 bytes).

### 4.2 Task 2: Apache Pig MapReduce Transformations
- **Script:** `task2_pig/scripts/task2_jobmarket.pig` uses Piggybank's `CSVExcelStorage(',')`.
- **Transformations Executed:**
  - Header row dropped (`FILTER jobs_raw BY job_id != 'job_id'`).
  - Text normalization: `LOWER(TRIM(job_title))` and `LOWER(TRIM(location))`.
  - Skill tokenization: Comma-separated strings flattened via `TOKENIZE(skills, ',')`, stripped of whitespace, lowercased, and deduplicated per job with `DISTINCT`.
  - Salary aggregations: Grouped by role/currency and location/currency with undisclosed salaries excluded.
  - Recency mapping: Mapped `posted_raw` into relative recency buckets.
- **Output Directories:** All 7 directories exist in HDFS with valid part files and `_SUCCESS` completion markers.

### 4.3 Task 3: Apache Hive Analytics
- **Metastore:** Managed database `jobmarket` created in Hive warehouse.
- **External Tables:** Defined over HDFS `/jobmarket/processed/` using `OpenCSVSerde` to handle internal commas within titles and locations.
- **The `skill_trends` Table:** Populated by `02_build_skill_trends.sql` (1,449,549 bytes in HDFS). Contains 44,021 records.
  - **Critical Finding:** Because the source dataset recorded relative posting recency (`posted_raw` containing `"6 Days Ago"`, `"Just Now"`, etc.) without an absolute calendar scrape timestamp, regex year extraction (`RLIKE '.*[0-9]{4}.*'`) matched 0 postings.
  - Every single row in `skill_trends` has `period = 'unknown'`.
  - `previous_period_count` is 0 across all rows, rendering `growth_pct` entirely `NULL`.
  - This limitation was honestly identified in the team's `task3_hive/PROJECT_STATUS.md` and `task1_hdfs/README.md`.

---

## 5. Comprehensive Numerical Discrepancy Resolution

The table below reconciles all conflicting figures found between the original LaTeX report, the README files, the dashboard data exports, and the true ground-truth cleaned dataset.

| Metric | Original Report Value | Verified Ground Truth | Export Dataset Value | Resolution & Root Cause |
|---|---|---|---|---|
| **Cleaned Postings Count** | 97,679 (in text) / 97,715 (overview) | **97,679** | 97,715 | Ground truth is 97,679. The 97,715 figure in `dashboard/data/jobs_cleaned.csv` was caused by 36 unescaped line breaks in raw text fields splitting into pseudo-rows during Hive/Pig export. |
| **Bengaluru Postings** | 18,320 (table) / 18,310 (Pig README) | **18,320** | 18,310 | Ground truth is 18,320 (18.76% of all postings). Exactly 10 Bengaluru postings were broken across newline boundaries during export, shifting `"Bengaluru"` into the `job_id` column. |
| **Top 1 Skill (Sales)** | 9,178 | **9,178** | 9,175 | Ground truth is 9,178 unique postings. 3 postings were lost to newline export fragmentation in `skills_demand.csv`. |
| **Top 2 Skill (Python)** | 5,846 | **5,846** | 5,841 | Ground truth is 5,846 unique postings. 5 postings were lost to newline export fragmentation. |
| **Top 3 Skill (Project Management)** | 5,544 | **5,543** | 5,541 | Ground truth is 5,543 unique postings (5,544 in report was a slight off-by-one counting error). |
| **Disclosed Salaries Count** | 33,128 of 97,715 (33.9%) | **33,124 (INR)** / **33,144 (All)** | 33,128 of 97,715 | The report copied 33,128 directly from the dashboard KPI widget (which read the 97,715-row export). Ground truth has 33,124 INR disclosed postings (33.96% of 97,550 INR jobs). |
| **Mean Disclosed Salary (INR)** | INR 756,844 | **INR 757,776.33** | INR 756,844.47 | INR 756,844 was computed on the fragmented 33,128 export subset. True INR disclosed mean is INR 757,776.33. |
| **Median Disclosed Salary (INR)** | INR 425,000 | **INR 425,000.00** | INR 425,000.00 | Exact match across both datasets. Robust to outlier fragmentation. |
| **Top 3 Cities Combined Volume** | 37,624 | **37,624** | 37,611 | Bengaluru (18,320) + Hyderabad (10,899) + Pune (8,405) = 37,624 (38.52% of national total). |
| **Bengaluru to Hyderabad Ratio** | ~1.7x | **1.6809x** | 1.6801x | $18,320 / 10,899 = 1.6809$. |
| **Posting Recency 1–7 Days** | 88.1% | **88.19% (86,140)** | 88.13% (86,115) | Live scrape recency distribution. |
| **Posting Recency Unknown** | 8.5% | **8.44% (8,248)** | 8.50% (8,310) | Postings with missing or unparseable recency strings. |
| **Posting Recency 0–1 Days** | 2.8% | **2.82% (2,753)** | 2.82% (2,752) | Postings listed as "Today" or "Just Now". |
| **Posting Recency 30+ Days** | 0.6% | **0.55% (538)** | 0.55% (538) | Postings older than one month. |

---

## 6. Audit of Phase II and the Skill Demand Velocity Index (SDVI)

### 6.1 Artifact Search and Verification Status
A forensic audit was conducted across the Windows repository, WSL user directories, and HDFS clusters:
- **Searched Locations:**
  - `D:\JOB_MARKET_ANALYSIS` and all subdirectories
  - WSL `/home/medha/` and `/home/`
  - HDFS `/` and `/user/` via NameNode PBImageTextWriter
  - Full Git commit history across all remote and local branches (`main`, `feature/streamlit-dashboard`, `task2-pig`, `task-3`, `docs/add-screenshots`)
- **Findings:**
  - `linkedin_postings.csv` (claimed 10,000 rows, 4.8 MB): **Does not exist.**
  - `clean_and_extract.pig` and Jython regex UDF: **Does not exist.**
  - `sdvi_query.hql` and external partitioned tables: **Does not exist.**
  - `sdvi_results.json` (claimed 567 records): **Does not exist.**
  - `index.html` (HTML5 canvas scatter dashboard): **Does not exist.**
  - HDFS directory `/user/ashmi_sn/jobmarket/raw/`: **Does not exist.**

**Audit Conclusion:** Phase II is **unimplemented and unverified** in the codebase. It represents a theoretical proposal or conceptual design rather than an empirically executed data pipeline.

### 6.2 Mathematical Audit of the SDVI Formulation
The report defines the Skill Demand Velocity Index as:
$$\text{growth\_rate} = \frac{\text{Mentions}_t - \text{Mentions}_{t-1}}{\text{Mentions}_{t-1}}$$
$$\text{SDVI} = \text{growth\_rate} \times \ln(1 + \text{Mentions}_t)$$

1. **Arithmetic Verification of Report Examples:**
   - *Low-volume jump ($2 \rightarrow 4$ mentions):*  
     $\text{growth\_rate} = (4 - 2)/2 = 1.0$ ($+100\%$).  
     $\text{SDVI} = 1.0 \times \ln(1 + 4) = \ln(5) \approx 1.6094 \rightarrow \mathbf{1.61}$. (Verified)
   - *High-volume jump ($100 \rightarrow 150$ mentions):*  
     $\text{growth\_rate} = (150 - 100)/100 = 0.5$ ($+50\%$).  
     $\text{SDVI} = 0.5 \times \ln(1 + 150) = 0.5 \times \ln(151) \approx 2.5086 \rightarrow \mathbf{2.51}$. (Verified)

2. **Division by Zero at Boundary:**
   If a new skill emerges in period $t$ with $\text{Mentions}_{t-1} = 0$, $\text{growth\_rate}$ is mathematically undefined (division by zero). In standard SQL, this produces `NULL` or throws a runtime exception. The report does not document how zero denominators are handled. An additive smoothing term ($\text{Mentions}_{t-1} + 1$) is required for mathematical stability.

3. **Flaw in Quadrant Classification Rules:**
   The report defines four quadrants based on $\text{growth\_rate}$ and $\text{median(SDVI)}$:
   - *Emerging:* $\text{growth\_rate} > 0$ and $\text{SDVI} > \text{median}$
   - *Established Growth:* $\text{growth\_rate} > 0$ and $\text{SDVI} \le \text{median}$
   - *Stable Core:* $\text{growth\_rate} \le 0$ and $\text{SDVI} > \text{median}$
   - *Declining:* $\text{growth\_rate} \le 0$ and $\text{SDVI} \le \text{median}$

   **Mathematical Inconsistency:**
   - Because volume is non-negative ($\text{Mentions}_t \ge 0$), the scaling factor $\ln(1 + \text{Mentions}_t)$ is strictly non-negative ($\ge 0$).
   - Therefore, the sign of $\text{SDVI}$ is identical to the sign of $\text{growth\_rate}$:
     $$\text{growth\_rate} \le 0 \implies \text{SDVI} \le 0$$
   - In any job market where overall tech hiring expands, the median SDVI across active skills is positive ($\text{median} > 0$).
   - If $\text{median} > 0$, then for any skill with $\text{growth\_rate} \le 0$:
     $$\text{SDVI} \le 0 < \text{median}$$
   - Consequently, the condition for *Stable Core* ($\text{growth\_rate} \le 0 \land \text{SDVI} > \text{median}$) is **mathematically impossible to satisfy**.
   - Furthermore, a massive incumbent skill (e.g. Python or SQL with 10,000 mentions) with flat growth ($\text{growth\_rate} = 0$) receives $\text{SDVI} = 0 \times \ln(10001) = 0$. Since $0 \le \text{median}$, the rule improperly classifies the vital market core as **"Declining"**!

### 6.3 Recommended Methodological Correction
To achieve the intended classification, momentum and volume must be evaluated on **two orthogonal axes** rather than collapsing volume into the velocity multiplier:
1. **Growth Axis ($Y$):** Percentage growth $\Delta = (\text{Mentions}_t - \text{Mentions}_{t-1}) / \text{Mentions}_{t-1}$
2. **Volume Axis ($X$):** Total market presence $\ln(1 + \text{Mentions}_t)$
3. **Corrected Quadrant Rules:**
   - **Emerging:** $\text{Growth} > +\epsilon$ and $\text{Volume} \le \text{Median Volume}$
   - **Established Growth:** $\text{Growth} > +\epsilon$ and $\text{Volume} > \text{Median Volume}$
   - **Stable Core:** $|\text{Growth}| \le \epsilon$ and $\text{Volume} > \text{Median Volume}$
   - **Declining:** $\text{Growth} < -\epsilon$ (or low growth with low volume)

---

## 7. Dashboard Implementation Verification

- **Architecture:** The Streamlit app (`dashboard/app.py`) serves as a standalone presentation layer. It loads data through `dashboard/data_loader.py` and performs pure math calculations via `dashboard/analytics.py`.
- **Pages (7 Verified Pages):**
  1. *Executive Overview:* Headline KPIs, top roles, top locations, top skills.
  2. *Skill Demand Intelligence:* Horizontal bar charts of top 20 skills, drill-down selectors.
  3. *Salary Analytics:* Role and location breakdowns, right-skew disclosures.
  4. *Location & Hiring:* Geographic concentration, city drill-downs.
  5. *Experience & Job Roles:* Experience bucket distribution and top skills per experience band.
  6. *Emerging Skill Trends:* Honest disclosure regarding snapshot recency and lack of multi-year calendar dates.
  7. *Data Explorer:* Full tabular browser with live column search and interactive CSV download button (`st.download_button`).
- **Data Source Decoupling:** The dashboard operates without active Hadoop daemons. If exports exist in `dashboard/data/`, it utilizes them; otherwise, it executes the exact Stage 1 cleaning contract in-process from the Excel source.

---

## 8. Summary of Corrections for the Final Report

1. **Unify Cleaned Postings Count:** Standardize on **97,679** cleaned postings throughout the entire report. Explain that 97,715 was an export artifact.
2. **Harmonize Location & Skill Counts:** Report **18,320** for Bengaluru (18.8%), **9,178** for Sales, and **5,846** for Python.
3. **Disclose Salary Denominators:** Clarify that disclosed salaries represent **33,124 INR postings** (33.96% of 97,550 INR postings) with an average of **INR 757,776** and median of **INR 425,000**.
4. **Transparent Framing of Phase II:** Present Phase II and the SDVI metric as a conceptual and methodological extension designed to address snapshot limitations, transparently noting that empirical evaluation was constrained by the absence of a verified multi-month longitudinal dataset in the repository.
5. **Incorporate Mathematical Critique:** Detail the quadrant classification limitation and document the mathematically consistent 2D orthogonal taxonomy.
