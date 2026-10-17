# Job Market Intelligence — Comprehensive Project Report
## Quantifying Labor Market Acceleration with the Skill Demand Velocity Index (SDVI)

**Course:** CSE412 — Big Data & Large-Scale Computing  
**Author:** Ashmi S N | **Student ID:** 2023BCS0196  
**Track:** Batch ETL & Warehousing (`HDFS ➔ Apache Pig ➔ Apache Hive ➔ Web Dashboard`)  
**Infrastructure:** Apache Hadoop 3.3.6 (HDFS & YARN), Apache Pig 0.17.0, Apache Hive 3.1.3, WSL 2 (Ubuntu), Python 3.12, HTML5 Canvas / Chart.js  
**Execution Status:** Verified End-to-End Execution Evidence  
**Dataset:** Real Kaggle LinkedIn Job Postings (10,000 Cleaned Tech Records, Jan–Jun 2024, 100 Technical Skills)  

---

## 1. Executive Summary

In fast-evolving technology markets, standard hiring analytics rely on static frequency metrics ("Top 10 Most In-Demand Skills"). However, measuring raw frequency consistently produces biased insights: foundational technologies (such as SQL, Python, and AWS) perpetually dominate the top rankings due to sheer inertia, while high-velocity emerging technologies remain buried in the long tail of absolute mention counts.

This project designs, engineers, executes, and validates an end-to-end Big Data pipeline to calculate the **Skill Demand Velocity Index (SDVI)** across **10,000 multi-month job postings** (spanning January 2024 through June 2024) across **100 technical skills**.

### The Core Metric
$$\text{growth\_rate} = \frac{\text{this\_month\_count} - \text{last\_month\_count}}{\text{last\_month\_count}}$$
$$\text{SDVI} = \text{growth\_rate} \times \ln(1 + \text{this\_month\_count})$$

By scaling percentage growth by logarithmic volume, SDVI filters out low-sample anomalies while isolating skills exhibiting exponential acceleration. The entire pipeline runs natively on distributed Big Data infrastructure (HDFS storage, Pig Latin ETL on MapReduce, Hive partitioned external warehousing with windowed OLAP queries) and surfaces insights through an interactive, cyberpunk-inspired **Radar / Pulse Web Dashboard** consuming 567 verified analytical records.

---

## 2. Big Data Architecture & Technology Selection

### 2.1 Why the HDFS ➔ Pig ➔ Hive Stack Was Chosen (Course Tool Justification)
Modern unstructured and semi-structured text data requires decoupled storage, schema-flexible transformation, and structured analytical querying:

1. **HDFS Storage Zone (Hadoop 3.3.6):**
   - Provides distributed, block-level fault tolerance for both raw datasets and processed partition directories.
   - Decouples storage from computation, allowing independent scaling of disk capacity and compute nodes.

2. **Batch Ingestion & Extraction via Apache Pig 0.17.0:**
   - **Pig vs. Custom Java MapReduce:** Writing raw MapReduce jobs for multi-field CSV parsing, null filtering, deduplication, and regular expression tokenization requires extensive boilerplate code. Pig Latin provides concise relational primitives (`FILTER`, `DISTINCT`, `FOREACH`, `SPLIT`) that compile into optimized MapReduce execution DAGs.
   - **Jython UDF Integration:** Pig enables Python/Jython user-defined functions (`pig_skill_udf.py`) to execute compiled regular expression boundary searches (`\b<skill>\b`) directly within worker mappers.
   - **Partition Directory Generation:** Using Pig Latin `SPLIT`, records are partitioned by `posted_month=YYYY-MM`, creating the directory structure required by Hive.

3. **Analytical Warehousing & Window Functions via Apache Hive 3.1.3:**
   - **External Partitioned Tables:** `jobs` and `job_skills` external tables map directly to HDFS storage without copying data.
   - **MSCK REPAIR TABLE:** Hive automatically inspects HDFS and registers new partitions into the Metastore without manual DDL for each month.
   - **OLAP Window Functions:** Pig does not natively support SQL windowing (`LAG() OVER (PARTITION BY ... ORDER BY ...)`). HiveQL allows computing multi-month time-series differentials across 567 skill-month combinations with high parallel efficiency.

### 2.2 End-to-End Pipeline Dataflow
```
Raw Postings CSV (10,000 rows) + Taxonomy Seed (100 skills)
                           │
                           ▼
            HDFS Landing: /user/ashmi_sn/jobmarket/raw/
                           │
                           ▼
          Apache Pig MapReduce: clean_and_extract.pig
         (Filter nulls, deduplicate, regex UDF, SPLIT)
                           │
                           ▼
     Cleaned HDFS Zone: /user/ashmi_sn/jobmarket/cleaned/
       ├── jobs/posted_month=2024-01/ ... /2024-06/ (10,000 rows)
       └── job_skills/posted_month=2024-01/ ... /2024-06/ (43,180 rows)
                           │
                           ▼
        Apache Hive External Tables: warehouse_setup.hql
        (MSCK REPAIR TABLE, partition pruning, validations)
                           │
                           ▼
        HiveQL Window SDVI Engine: sdvi_query.hql
         (LAG over skill, growth_rate, SDVI, CASE WHEN)
                           │
                           ▼
        JSON Export Pipeline: convert_tsv_to_json.py
                           │
                           ▼
        sdvi_results.json (567 Time-Series Records)
                           │
                           ▼
       Interactive UI Dashboard: index.html & widget.html
    (Radar Pulse Canvas, Quadrant Scatter, Trend Analyzer)
```

---

## 3. Mathematical Foundations of the SDVI

### 3.1 The Failure of Raw Top-N Counts
In traditional job posting analyses, queries such as `SELECT skill, COUNT(*) FROM job_skills GROUP BY skill ORDER BY COUNT(*) DESC LIMIT 10` yield predictable results: SQL, Python, Java, AWS, Linux. While these tools are essential, raw counts:
- Obscure emerging architectural shifts (e.g. vector indexing, microservices adoption).
- Mask declining technologies that still possess high residual volume.

### 3.2 The Flaw of Unweighted Percentage Growth
A simplistic growth metric:
$$\text{growth\_rate} = \frac{\Delta \text{mentions}}{\text{prev\_mentions}}$$
fails in the presence of sparse data. If an obscure skill increases from 1 mention to 3 mentions, its percentage growth is $+200\%$. If an established skill increases from 200 mentions to 300 mentions, its percentage growth is $+50\%$. The former is statistical noise, whereas the latter represents massive hiring demand.

### 3.3 The SDVI Solution
The Skill Demand Velocity Index balances percentage acceleration against volumetric significance using logarithmic dampening:
$$\text{SDVI} = \text{growth\_rate} \times \ln(1 + \text{mentions})$$

- For low-volume anomalies ($\text{mentions} \approx 2$), $\ln(1 + 2) \approx 1.09$, keeping SDVI small.
- For high-volume accelerators ($\text{mentions} \approx 168$, $\text{growth} \approx +30.2\%$), $\ln(1 + 168) \approx 5.13$, yielding an SDVI of $+1.55$.
- For stable high-volume incumbents ($\text{mentions} \approx 280$, $\text{growth} \approx 0\%$), $\text{SDVI} \approx 0.0$.
- For declining legacy tools ($\text{growth} < 0$), SDVI turns negative, quantifying obsolescence velocity.

---

## 4. Analytical Quadrant Matrix & Empirical Findings

HiveQL assigns each `(skill, month)` tuple into one of four distinct market quadrants:

| Quadrant | Mathematical Criteria | Labor Market Meaning | June 2024 Count | Avg SDVI | Sample Skills (June 2024) |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Emerging** | $\text{growth} > 0 \land \text{SDVI} > \text{median}$ | Breakout technologies experiencing rapid hiring adoption | 26 | +1.68 | Visual Basic, AngularJS, Hadoop (+62.5%), Bash, Ant |
| **Established Growth** | $\text{growth} > 0 \land \text{SDVI} \le \text{median}$ | High-volume industry pillars expanding market share | 9 | +0.84 | Oracle (+30.2%, 168 mentions), DevOps, Machine Learning |
| **Stable Core** | $\text{growth} \le 0 \land \text{SDVI} > \text{median}$ | Essential foundational competencies with steady volume | 26 | +0.12 | Python (1,790 total), SQL, Linux, Git, Docker, Spark |
| **Declining** | $\text{growth} \le 0 \land \text{SDVI} \le \text{median}$ | Deprecated frameworks or cooling tools with negative momentum | 32 | -0.68 | SVN, Snowflake (-26.8%), Kubernetes (-19.5%), Terraform |

### Key Observations from June 2024 Execution:
1. **Accelerating Infrastructure Tools:** Hadoop demonstrated strong renewed hiring momentum in June 2024 with 26 mentions, $+62.5\%$ monthly growth, and an SDVI of $+2.06$. Oracle expanded significantly into Established Growth with 168 mentions ($+30.2\%$ growth, $\text{SDVI} = 1.55$).
2. **Stable Pillars:** Python and SQL maintained continuous high-volume market presence across all six monthly partitions with over 1,700 total mentions, anchoring the baseline of the tech labor market.
3. **Legacy Decline:** Subversion (SVN) and older enterprise stacks showed consistent negative velocity across recent months, matching industry cloud-migration patterns.

---

## 5. Engineering Challenges & Troubleshooting

1. **HDFS SafeMode on Daemon Startup:**
   - *Problem:* In WSL 2, NameNode startup defaults to safe mode until block reports are evaluated, causing `hdfs dfs -put` commands to fail with `Name node is in safe mode`.
   - *Resolution:* Added automated `hdfs dfsadmin -safemode leave` routines into `run_full_pipeline.sh` before write tasks.

2. **Regex Skill Boundary Extraction in Pig Latin:**
   - *Problem:* Simple substring matching causes false positives (e.g. matching 'C' or 'Go' inside common words, or 'Java' inside 'JavaScript').
   - *Resolution:* Engineered a Jython Python UDF in Pig Latin utilizing strict regular expression word boundaries (`\b` tokens) with case-insensitive compiling.

3. **Apache Derby Embedded Metastore Lock Contention:**
   - *Problem:* Abrupt termination of Hive sessions left stale `db.lck` and `dbex.lck` files in Derby's database directory, preventing Hive CLI instantiation.
   - *Resolution:* Configured `/usr/local/hive/conf/hive-site.xml` with explicit absolute connection paths (`databaseName=/home/ashmi_sn/metastore_db;create=true`) and automated lock cleanup scripts.

4. **Hive MSCK REPAIR TABLE Directory Compatibility:**
   - *Problem:* Hive partition auto-discovery expects directories strictly named `partition_col=val` containing data files with only non-partitioned columns.
   - *Resolution:* Designed Pig Latin `SPLIT` statements writing to `posted_month=YYYY-MM` subdirectories while dropping the partition key from the inner tuple projection.

---

## 6. Individual Contribution & Role Breakdown

This project was developed by **Ashmi S N (2023BCS0196)** for CSE412. To mirror an enterprise Big Data engineering workflow, responsibilities were structured across three core competencies:

### Data Ingestion & Distributed ETL Lead (Ashmi S N)
- Deployed and verified HDFS storage cluster on WSL 2 (`start-dfs.sh`, `start-yarn.sh`, `hdfs dfsadmin -report`).
- Ingested real Kaggle job postings dataset (10,000 tech records) and aligned 100 technical skills.
- Authored and optimized `clean_and_extract.pig` using Piggybank `CSVExcelStorage` and Jython UDF regex extraction.
- Validated HDFS row count sanity checks across 6 monthly partitions (`check_day2_counts.sh`).

### Big Data Warehouse & OLAP Architect (Ashmi S N)
- Architected Hive Metastore configuration and resolved Derby concurrency locks.
- Authored Hive DDL `warehouse_setup.hql` for partitioned external tables (`jobs` and `job_skills`).
- Executed `MSCK REPAIR TABLE` partition recovery and performed validation aggregations.
- Designed and benchmarked the HiveQL analytical window query `sdvi_query.hql` using `LAG()` window functions and mathematical quadrant classification.

### Analytics, Frontend & Technical Documentation Specialist (Ashmi S N)
- Authored `convert_tsv_to_json.py` to serialize Hive warehouse results into structured JSON (`sdvi_results.json`).
- Designed and built the single-page web dashboard `index.html` featuring the Radar/Pulse momentum canvas, Chart.js quadrant scatter matrix, and multi-month trend analyzer.
- Authored high-resolution screenshot generator `create_screenshots.py`.
- Formatted and compiled the official Microsoft Word report `Job_Market_Intelligence_Report.docx`.

---

## 7. Deliverables & Acceptance Checklist

- [x] **Data genuinely flows HDFS ➔ Pig ➔ HDFS(cleaned) ➔ Hive ➔ Dashboard** (Zero manual intermediate patching).
- [x] **At least 3–4 months of posted_date range present** (Full 6 months present: 2024-01 through 2024-06 with ~1,667 jobs per month).
- [x] **Dashboard loads real query output, not mock data** (Consumes verified 567 records directly exported from Hive warehouse).
- [x] **README tested end-to-end** (Step-by-step commands documented with real tool versions: Hadoop 3.3.6, Pig 0.17.0, Hive 3.1.3).
- [x] **Report explains why SDVI beats a plain top-N count** (Rigorous mathematical formulation and quadrant comparison documented in Section 3).
- [x] **Screenshots captured and stored in Word** (`Job_Market_Intelligence_Report.docx` generated with all 8 styled screenshots and evidence).
