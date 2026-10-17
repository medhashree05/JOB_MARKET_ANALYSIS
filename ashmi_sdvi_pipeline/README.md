# Job Market Intelligence — Skill Demand Velocity Index (SDVI) Pipeline

**Course:** CSE412 — Big Data & Large-Scale Computing  
**Student:** Ashmi S N (2023BCS0196)  
**Track:** Batch ETL & Warehousing (`HDFS ➔ Apache Pig ➔ Apache Hive ➔ Web Dashboard`)  
**Stack:** Apache Hadoop 3.3.6 (HDFS & YARN), Apache Pig 0.17.0, Apache Hive 3.1.3, WSL 2 Ubuntu, Python 3.12, HTML5 / Chart.js  
**Dataset:** Real Kaggle LinkedIn Job Postings (`dataset/postings.csv`), 10,000 Cleaned Tech Records across 6 Months (2024-01 to 2024-06), 100 Technical Skills  

---

## 1. Tool Versions & Environment

All pipeline components execute in WSL 2 (`ashmi_sn`):
- **Hadoop (HDFS & YARN):** `3.3.6` (`/usr/local/hadoop`)
- **Apache Pig:** `0.17.0` (`/usr/local/pig`)
- **Apache Hive:** `3.1.3` (`/usr/local/hive`)
- **Java:** OpenJDK 8 (`/usr/bin/java`)
- **Python:** Python 3.12 (Host & WSL)

Verify installed versions:
```bash
hadoop version
pig -version
hive --version
```

---

## 2. One-Command Execution (Full Pipeline)

An automated orchestration script handles daemon startup, HDFS safe-mode management, ingestion, Pig MapReduce ETL, Hive external warehouse setup, SDVI window queries, and JSON conversion:

```bash
# In WSL 2 terminal:
bash run_full_pipeline.sh
```

---

## 3. Step-by-Step Run Order

### Step 1: Start Daemons & Check Cluster Health
```bash
start-dfs.sh
start-yarn.sh
jps
hdfs dfsadmin -report
hdfs dfsadmin -safemode leave
```

### Step 2: Ingest & Land Real Kaggle Dataset in HDFS
```bash
# Filter 10,000 tech postings from dataset/postings.csv and generate 100-skill taxonomy:
python prepare_new_dataset.py

# Create HDFS directories:
hdfs dfs -mkdir -p /user/ashmi_sn/jobmarket/raw
hdfs dfs -mkdir -p /user/ashmi_sn/jobmarket/cleaned/jobs
hdfs dfs -mkdir -p /user/ashmi_sn/jobmarket/cleaned/job_skills
hdfs dfs -mkdir -p /user/ashmi_sn/jobmarket/warehouse

# Upload to HDFS raw zone:
hdfs dfs -put -f linkedin_postings.csv skill_taxonomy.txt /user/ashmi_sn/jobmarket/raw/
hdfs dfs -ls -h /user/ashmi_sn/jobmarket/raw/
```

### Step 3: Run Apache Pig MapReduce Cleaning & Extraction
```bash
# Run Pig Latin ETL with Jython regex skill extraction:
pig -x mapreduce clean_and_extract.pig

# Verify partition sanity counts:
bash check_day2_counts.sh
```
*Output: 10,000 cleaned jobs partitioned across 6 monthly HDFS directories (`posted_month=2024-01` to `2024-06`) and 43,180 skill mention rows.*

### Step 4: Configure Apache Hive Warehouse & Partition Recovery
```bash
# Create external partitioned tables and repair partitions:
hive -f warehouse_setup.hql
```
*Output: Discovers and registers 6 partitions for `jobs` and `job_skills`. Validates 100 distinct skills.*

### Step 5: Execute HiveQL Window Query & Export Results
```bash
# Calculate month-over-month growth and SDVI using LAG() window functions:
hive -f sdvi_query.hql

# Convert exported TSV to structured JSON:
python convert_tsv_to_json.py
```
*Output: Generates `sdvi_results.json` containing 567 verified analytical time-series records.*

### Step 6: Launch Web Dashboard
Open the standalone single-page application in any browser:
```powershell
# In Windows PowerShell:
Start-Process index.html
```
Features:
- **360° Radar Momentum Pulse Canvas:** Pulsing blips sized by SDVI magnitude and color-coded by quadrant.
- **Logarithmic Quadrant Scatter Matrix:** Real-time log mentions vs. SDVI scatter plot.
- **Top Velocity Leaderboard:** Ranked ranking of accelerating technologies with progress bars.
- **Multi-Month Trend Analyzer:** Historical trajectory tracking for key skills (Hadoop, Python, AWS, Docker, Spark, React, Kubernetes, Snowflake).

### Step 7: Documentation & Word Report Generation
```powershell
# Regenerate high-resolution screenshots:
py -3.12 create_screenshots.py

# Compile Microsoft Word submission report:
py -3.12 generate_word_document.py
```
*Output: `Job_Market_Intelligence_Report.docx` containing complete report and all embedded visual evidence.*

---

## 4. How to Refresh with New Data (Future Updates)

To refresh the pipeline with any new batch of job postings:
1. Place the new CSV file into `dataset/postings.csv`.
2. Run data filtering & taxonomy generation:
   ```bash
   python prepare_new_dataset.py
   ```
3. Run the automated pipeline:
   ```bash
   bash run_full_pipeline.sh
   ```
4. Rebuild `index.html` to sync dashboard payload:
   ```powershell
   py -3.12 scratch/rebuild_index.py
   ```
5. Refresh Word report screenshots and document:
   ```powershell
   py -3.12 create_screenshots.py
   py -3.12 generate_word_document.py
   ```

---

## 5. Repository File Map

| File | Purpose |
| :--- | :--- |
| `prepare_new_dataset.py` | Ingests `dataset/postings.csv`, filters 10,000 tech jobs, outputs `linkedin_postings.csv` & `skill_taxonomy.txt`. |
| `clean_and_extract.pig` | Pig Latin MapReduce script for deduplication, null filtering, and monthly partitioning. |
| `pig_skill_udf.py` | Jython Python UDF performing regular expression skill extraction with word boundary matching. |
| `warehouse_setup.hql` | Hive DDL for external partitioned tables (`jobs`, `job_skills`) and `MSCK REPAIR TABLE`. |
| `sdvi_query.hql` | HiveQL window query evaluating `LAG()`, computing SDVI, and assigning analytical quadrants. |
| `convert_tsv_to_json.py` | Serializes Hive output into `sdvi_results.json` (567 records). |
| `run_full_pipeline.sh` | Bash orchestration script executing the entire end-to-end pipeline with safe-mode handling. |
| `index.html` | Cyberpunk single-page web dashboard with Canvas radar, scatter plot, leaderboard, and trend charts. |
| `create_screenshots.py` | Python script generating high-resolution terminal and visualization screenshots. |
| `generate_word_document.py` | Python script producing the formatted submission report `Job_Market_Intelligence_Report.docx`. |
| `PROJECT_REPORT.md` | Comprehensive 7-section academic project report. |
| `architecture_diagram.md` | Mermaid architecture and dataflow diagram. |
