# Project Status and Reproduction Notes

## Project

**Large-Scale Job Market Intelligence and Emerging Skill Demand Analysis Using HDFS, Pig, and Hive**

Date of the current verified run: 2026-09-22.

## Completed work

### Task 1 - Dataset and HDFS

- Source dataset: `dataset/indian-job-market-dataset-2025.xlsx`.
- Converted the Excel source to CSV.
- Standardized the real dataset columns and cleaned locations.
- Removed duplicate job IDs and exact duplicate rows.
- Validated required fields and salary/experience values.
- Loaded raw data to `/jobmarket/raw/jobs_raw.csv`.
- Loaded cleaned data to `/jobmarket/cleaned/jobs_cleaned.csv`.
- The verified run retained 97,679 cleaned postings from 97,929 source rows.

### Task 2 - Pig

- Loads cleaned jobs from HDFS.
- Normalizes titles and locations.
- Splits comma-separated skills into one row per job and skill.
- Produces role, skill, location, salary, salary-location, and recency outputs.
- Uses quoted CSV output so commas inside text fields are preserved.
- The reusable runner is `task2_pig/scripts/run_task2_pig.sh`.

### Task 3 - Hive

- Creates the `jobmarket` database and external tables over Pig outputs.
- Creates the Hive-managed `skill_trends` table.
- Runs demand, salary, role-skill, recency, trend, emerging-skill, and quality queries.
- The reusable runner is `task3_hive/scripts/run_task3_hive.sh`.
- The corrected Hive CSV metadata uses `OpenCSVSerde` to read quoted Pig output.

## Canonical pipeline

```text
dataset/*.xlsx
  -> Task 1 Python cleaning
  -> HDFS /jobmarket/raw and /jobmarket/cleaned
  -> Task 2 Pig
  -> HDFS /jobmarket/processed
  -> Task 3 Hive tables and analysis queries
```

## WSL service setup

Run this once in every new WSL terminal before Hadoop tools:

```bash
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export HIVE_HOME=/usr/local/hive
export PIG_HOME=/usr/local/pig
export PATH=$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin:$PIG_HOME/bin:$PATH
```

Start the services before running the pipeline:

```bash
start-dfs.sh
start-yarn.sh
mapred --daemon start historyserver
hdfs dfsadmin -safemode leave
jps
```

Expected Java processes include `NameNode`, `DataNode`, `ResourceManager`, `NodeManager`, and `JobHistoryServer`. The JobHistoryServer web UI is normally available at `http://localhost:19888`.

The JobHistoryServer is not the source of the data and does not execute the SQL. It lets Pig retrieve completed MapReduce statistics. If YARN reports `FinalApplicationStatus=SUCCEEDED` but Pig retries `localhost:10020`, the job ran successfully but the history server was unavailable.

## Reproduce from the repository root

```bash
cd /mnt/c/Users/Ashmi_SN/Desktop/bigdataactual/JOB_MARKET_ANALYSIS

python3 -m venv task1_hdfs/.venv
source task1_hdfs/.venv/bin/activate
python -m pip install -r task1_hdfs/requirements.txt

mkdir -p data/raw
cp dataset/indian-job-market-dataset-2025.xlsx data/raw/
python task1_hdfs/scripts/01_convert_xlsx_to_csv.py
python task1_hdfs/scripts/02_clean_data.py
bash task1_hdfs/scripts/03_hdfs_load.sh
bash task1_hdfs/scripts/04_verify_hdfs.sh

bash task2_pig/scripts/run_task2_pig.sh
bash task3_hive/scripts/run_task3_hive.sh
```

The Python virtual environment is only needed for Task 1. The Hadoop, Pig, and Hive commands require the WSL environment variables above.

## HDFS outputs

```text
/jobmarket/raw/jobs_raw.csv
/jobmarket/cleaned/jobs_cleaned.csv
/jobmarket/processed/jobs
/jobmarket/processed/skills
/jobmarket/processed/skills_demand
/jobmarket/processed/location
/jobmarket/processed/salary
/jobmarket/processed/salary_location
/jobmarket/processed/time_based
```

## Hive tables

| Table | Type | Source |
|---|---|---|
| `jobs` | External | `/jobmarket/processed/jobs` |
| `job_skills` | External | `/jobmarket/processed/skills` |
| `skills_demand` | External | `/jobmarket/processed/skills_demand` |
| `job_locations` | External | `/jobmarket/processed/location` |
| `job_salary` | External | `/jobmarket/processed/salary` |
| `salary_by_location` | External | `/jobmarket/processed/salary_location` |
| `time_based` | External | `/jobmarket/processed/time_based` |
| `skill_trends` | Managed | Built from `jobs` and `job_skills` |

## Add or rerun queries

Add queries to `task3_hive/scripts/03_analysis.sql`, or run them interactively:

```bash
hive -S -e "USE jobmarket;
SELECT skill, SUM(job_count) AS total_demand
FROM skills_demand
GROUP BY skill
ORDER BY total_demand DESC
LIMIT 20;"
```

Useful tables are described in `task3_hive/README.md`. Do not delete `/jobmarket/cleaned`; rerun Task 2 only after rebuilding its `/jobmarket/processed` outputs.

## Important limitation

`posted_raw` contains mostly relative values such as `6 Days Ago` and `Just Now`, not reliable historical dates. Hive only extracts an explicit year when one is present; other records are assigned to `unknown`. Therefore, `skill_trends` is not a complete 2024/2025/2026 historical trend. A true year-over-year analysis requires a source dataset with an absolute posting date or dated snapshots.

## Current interpretation of warnings

- `NativeCodeLoader` warnings are common in WSL Hadoop installations.
- Multiple SLF4J binding warnings are dependency-classpath warnings.
- Pig retries on port `10020` mean JobHistoryServer is unavailable; start it with `mapred --daemon start historyserver`.
- A YARN line reporting `FinalApplicationStatus=SUCCEEDED` means the MapReduce computation succeeded.