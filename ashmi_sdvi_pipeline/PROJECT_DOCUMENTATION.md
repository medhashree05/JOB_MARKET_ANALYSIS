# Job Market Intelligence & Time-Series Skill Velocity Analysis
## A Unified Big Data Investigation: From Static Scrape Rectification to Temporal SDVI Modeling

**Course:** CSE412 — Big Data & Large-Scale Computing  
**Student:** Ashmi S N (2023BCS0196)  
**Track:** Batch ETL, Distributed Warehousing & OLAP Analytics (`HDFS ➔ Apache Pig ➔ Apache Hive ➔ Web Dashboard`)  
**Environment:** bigdata-lab (`Hadoop 3.3.6`, `Pig 0.17.0`, `Hive 3.1.3` on WSL 2 Ubuntu) | Python 3.12 | HTML5 Canvas / Chart.js  
**Datasets Analyzed:**  
1. **Indian Job Market Dataset (Naukri Scrape):** 97,679 cleaned records (single-point time snapshot with relative age strings).  
2. **Global LinkedIn Job Postings Dataset:** 10,000 cleaned tech records across 6 continuous calendar months (Jan–Jun 2024), 100 skills.  

---

## 1. Executive Summary & Problem Motivation

Standard hiring market analytics rely on static frequency metrics (`SELECT skill, COUNT(*) FROM job_skills GROUP BY skill ORDER BY COUNT(*) DESC`). In enterprise recruiting datasets, this produces two fundamental failures:
1. **Incumbent Inertia:** Ubiquitous foundational skills (such as SQL, Python, Java, and AWS) perpetually dominate top rankings due to massive historical adoption. Raw counts completely mask whether a skill is accelerating, plateauing, or entering structural obsolescence.
2. **The Percentage Distortion of Sparse Data:** Calculating unweighted growth ($\Delta \text{Count} / \text{PriorCount}$) severely overstates obscure tools. A skill growing from 1 mention to 3 mentions shows $+200\%$ growth, yet represents negligible real hiring impact.

This project delivers a unified Big Data engineering investigation. It begins by performing baseline aggregation and rigorous data-quality rectification on 97.6K Indian job postings (Phase I). After identifying that static relative age strings cannot support true temporal modeling, it transitions to a dedicated 6-month continuous dataset (Phase II). Using **HiveQL window functions (`LAG`)**, we formulate and compute the **Skill Demand Velocity Index (SDVI)** across 567 verified records, surfacing insights through an interactive **360° Radar Momentum Web Dashboard**.

---

## 2. Phase I: Baseline Aggregation & Rectification on Indian Job Market (97.6K Rows)

Phase I evaluated 97,679 cleaned postings. Querying this dataset in Apache Hive revealed high-volume macro patterns alongside critical data-quality anomalies:

### 2.1 Core Analytical Findings
- **Top Job Roles:** Application Developer (2,033) and Application Lead (1,346) accounted for more postings than the next 8 top roles combined, reflecting heavy enterprise application hiring.
- **Top Demanded Skills:** 'Screening' led at 996 mentions. The subsequent 9 unrelated skills (*curriculum development, vmc, editorial, test automation framework, recruitment management, p2p, release management, office management*) were all tied at exactly 99. Follow-up regex text filtering confirmed this was not raw text noise, but an upstream aggregation artifact.
- **Location Distribution:** Detected lexicographical text sorting where '99' ranked above '972' (Pune) and '966' (Jaipur) due to string storage of `job_count`.
- **Salary Ranking Outliers:** Unfiltered rankings placed 'Logistics and Warehouse Manager' at ₹9.75M based on a single posting ($n=1$).
- **Sample-Filtered Salary Rectification:** Applying `HAVING COUNT(*) >= 5` eliminated anomalies, revealing genuine top-paying clusters: Medical Oncologist (₹6.6M median, $n=7$), Cardiologist (₹6.2M), Gen AI Architect (₹3.75M), and AI Engineer (₹3.25M).

### 2.2 The Limiting Factor: The Time-Trend Caveat
An independent audit of Phase I's `skill_trends` table (44,021 rows) showed `period = 'unknown'` and unpopulated growth values. Recency queries showed **88.1% of postings were 1–7 days old** (*relative strings like '3 days ago'*), with only 0.6% older than 30 days. Because the scrape lacked true historical calendar timestamps, it was mathematically impossible to perform true period-over-period time-series differentiation.

### 2.3 Phase I Data-Quality Rectification Summary

| Data-Quality Issue | Status | Resolution / Diagnostic Evidence |
| :--- | :---: | :--- |
| **Duplicate job_id in jobs** | **RESOLVED** | Re-verification confirmed 97,679 rows with 0 duplicate IDs (cleaned from earlier 97,715 run with 6 duplicates). |
| **Salary Outliers ($n=1$)** | **RESOLVED** | `WHERE job_count >= 5` eliminated anomalies, elevating credible medical and Gen AI roles. |
| **Lexicographical Sort in Locations** | **DOCUMENTED** | Identified string typing of `job_count`; corrected via integer casting. |
| **Tied-99 Skill Cluster** | **PROVEN AGGREGATION BUG** | Text cleaning retained the tie, isolating the issue upstream in Pig/Hive aggregation logic. |
| **Historical Time-Series Analytics** | **UNSUPPORTED IN SCRAPE** | Relative posting age strings prevented true temporal modeling; necessitated Phase II. |

---

## 3. Phase II: Formulation of the Skill Demand Velocity Index (SDVI)

To achieve true temporal intelligence, Phase II ingested 10,000 tech postings spanning 6 contiguous calendar months (Jan 2024 to Jun 2024) across 100 standardized skills.

### 3.1 Mathematical Formulation
$$\text{growth\_rate} = \frac{\text{Mentions}_t - \text{Mentions}_{t-1}}{\text{Mentions}_{t-1}}$$
$$\text{SDVI} = \text{growth\_rate} \times \ln(1 + \text{Mentions}_t)$$

### 3.2 Analytical Dynamics
- **Low-volume noise ($2 \rightarrow 4$ mentions, $+100\%$):** Scaled by $\ln(1+4) = 1.61 \rightarrow \text{SDVI} = 1.61$ (dampened).
- **High-volume breakout ($100 \rightarrow 150$ mentions, $+50\%$):** Scaled by $\ln(1+150) = 5.01 \rightarrow \text{SDVI} = 2.51$ (promoted).
- **Stable incumbents (300 mentions, $0\%$ growth):** $\text{growth} = 0.0 \rightarrow \text{SDVI} = 0.00$.
- **Cooling/legacy tools (negative growth):** Yields strictly negative SDVI, measuring obsolescence velocity.

---

## 4. Distributed Pipeline Architecture & Execution

The end-to-end pipeline operates across three genuinely integrated distributed tools on WSL 2 (`Hadoop 3.3.6`, `Pig 0.17.0`, `Hive 3.1.3`):

```
[Raw Postings CSV (10,000 rows) + Taxonomy Seed (100 skills)]
                           │
                           ▼
            HDFS Storage: /user/ashmi_sn/jobmarket/raw/
                           │
                           ▼
          Apache Pig MapReduce: clean_and_extract.pig
         (Deduplicate, null filter, Jython regex UDF, SPLIT)
                           │
                           ▼
     Cleaned HDFS Zone: /user/ashmi_sn/jobmarket/cleaned/
       ├── jobs/posted_month=2024-01/ ... /2024-06/ (10,000 rows)
       └── job_skills/posted_month=2024-01/ ... /2024-06/ (43,180 mentions)
                           │
                           ▼
        Apache Hive External Tables: warehouse_setup.hql
        (MSCK REPAIR TABLE, partition discovery, validations)
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
       Interactive UI Dashboard: index.html
    (Radar Pulse Canvas, Quadrant Scatter, Trend Analyzer)
```

### Key Implementation Milestones
1. **HDFS Storage:** Automated safe-mode clearing (`hdfs dfsadmin -safemode leave`) and loaded raw data to `/user/ashmi_sn/jobmarket/raw/`.
2. **Apache Pig MapReduce:** Executed `clean_and_extract.pig`. Utilized a Jython Python UDF (`pig_skill_udf.py`) with strict regex word boundaries (`\b`) to eliminate false positives (*preventing 'C' or 'Go' from matching within general text*). Partitioned output across 6 monthly directories.
3. **Apache Hive Warehousing:** External tables partitioned by `posted_month`. `MSCK REPAIR TABLE` registered all 6 partitions.
4. **HiveQL Windowed OLAP:** Evaluated `LAG(mentions, 1) OVER (PARTITION BY skill ORDER BY month)` to calculate growth rate, SDVI, and quadrant classification. Exported 567 verified analytical records.

---

## 5. Empirical Findings & Interactive UI Dashboard

### 5.1 Analytical Quadrant Matrix (June 2024 Snapshot)

| Quadrant | Criteria | Market Significance | June 2024 Count | Representative Skills |
| :--- | :--- | :--- | :---: | :--- |
| **Emerging** | $\text{growth} > 0 \land \text{SDVI} > \text{median}$ | Rapid breakout adoption | 26 | Hadoop (+62.5%, SDVI 2.06), Bash (+50%), Visual Basic, AngularJS, Ant |
| **Established Growth** | $\text{growth} > 0 \land \text{SDVI} \le \text{median}$ | High-volume expanding pillars | 9 | Oracle (+30.2%, 168 mentions, SDVI 1.55), DevOps, Machine Learning |
| **Stable Core** | $\text{growth} \le 0 \land \text{SDVI} > \text{median}$ | Core enterprise baseline | 26 | Python (1,790 total), SQL (1,842), Linux, Docker, Spark, Git |
| **Declining** | $\text{growth} \le 0 \land \text{SDVI} \le \text{median}$ | Cooling or legacy stacks | 32 | Snowflake (-26.8%, SDVI -0.92), Kubernetes (-19.5%), SVN, Terraform |

### 5.2 Standalone Web Dashboard (`index.html`)
The single-page dashboard embeds the 567 records and provides:
- **360° Radar Momentum Pulse Canvas:** Pulsing blips sized by SDVI magnitude and color-coded by quadrant.
- **Quadrant Scatter Matrix:** Logarithmic job mentions plotted against SDVI.
- **Top Velocity Leaderboard:** Ranked ranking of accelerating technologies with animated progress bars.
- **Multi-Month Trend Analyzer:** Historical trajectory tracking for key technologies (*Hadoop, Python, AWS, Docker, Spark, React, Kubernetes, Snowflake*).

---

## 6. Comparative Synthesis: Two Datasets, One Cohesive Solution

| Dimension | Phase I: Indian Job Market (97.6K Scrape) | Phase II: Global Time-Series (10K / 567 SDVI) |
| :--- | :--- | :--- |
| **Data Nature** | 97,679 postings; single time snapshot with relative age strings. | 10,000 tech postings; partitioned across 6 continuous calendar months. |
| **Analytical Scope** | Macro volume: Top roles, raw demand, and sample-filtered salary distributions. | Time-series velocity: Month-over-month growth, SDVI scores, and quadrant assignment. |
| **Hive Techniques** | Standard SQL aggregations (`GROUP BY`, `HAVING`, `percentile_approx`). | OLAP window functions (`LAG() OVER (PARTITION BY skill ORDER BY month)`). |
| **Key Insight** | Identifies current hiring concentrations (Medical oncology ₹6.6M, Gen AI ₹3.75M). | Identifies forward-looking momentum (Hadoop, Oracle expanding; Snowflake, SVN cooling). |
| **Engineering Takeaway** | Demonstrates the vulnerability of raw counts to ties and lack of temporal depth. | Proves that SDVI balances volumetric mass with velocity to isolate true tech adoption trends. |

---

## 7. Deliverables & Acceptance Checklist

- [x] **Genuine 3-Tool Pipeline Integration:** Data flows HDFS ➔ Pig (MapReduce) ➔ HDFS (cleaned) ➔ Hive ➔ JSON ➔ UI Dashboard with zero manual patching.
- [x] **Analytical Depth Beyond Plain Counts:** Identified failure modes of static scrapes and formulated mathematical SDVI via Hive window functions.
- [x] **End-to-End Reproducibility:** Entire workflow automated via `run_full_pipeline.sh` inside WSL 2 Ubuntu on Hadoop 3.3.6, Pig 0.17.0, and Hive 3.1.3.
- [x] **Interactive Presentation Layer:** `index.html` renders all 567 verified records with radar canvas, scatter plot, and multi-month trends.
- [x] **Verified Documentation:** `Job_Market_Intelligence_Master_Report.docx` and `PROJECT_DOCUMENTATION.md` compile all query proofs, schemas, and analytical tables.
