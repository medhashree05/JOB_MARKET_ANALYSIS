# Task 2 – Apache Pig Job Market Aggregation

## Objective

Process the cleaned job market dataset using Apache Pig and generate aggregated results for:

- Job data normalization
- Skill demand
- Location demand
- Salary analysis
- Salary by location
- Job posting recency

## Input

The cleaned dataset is available in HDFS at:

```text
/jobmarket/cleaned/jobs_cleaned.csv
Technologies Used
Apache Hadoop
HDFS
Apache Pig
Piggybank
Processing Steps
1. Load Cleaned Data

The cleaned job market CSV file is loaded from HDFS using Piggybank's CSVExcelStorage.

The CSV header is removed before processing.

2. Normalize Job Data

Job titles and locations are normalized using LOWER() and TRIM().

Output:

/jobmarket/processed/jobs
3. Create Job-Skill Records

The comma-separated skills field is split into individual skills using TOKENIZE().

Duplicate skill mentions within the same job are removed using DISTINCT.

Output:

/jobmarket/processed/skills
4. Skill Demand Aggregation

Skills are grouped and counted based on the number of jobs requiring each skill.

Output:

/jobmarket/processed/skills_demand

Example results:

sales,9175
python,5841
project management,5541
customer service,5118
5. Location Demand Aggregation

Jobs are grouped by location and the number of job postings is calculated.

Output:

/jobmarket/processed/location

Example results:

bengaluru,18310
hyderabad,10898
pune,8403
mumbai,6477
6. Salary Aggregation

Salary data is aggregated by job role and currency.

The following metrics are calculated:

Job count
Minimum average salary
Maximum average salary
Mean salary

Salary is grouped by currency so that INR and USD values are not mixed.

Output:

/jobmarket/processed/salary
7. Salary by Location

Average salary is calculated for each location and currency.

Output:

/jobmarket/processed/salary_location
8. Time / Recency Analysis

The dataset contains relative posting information rather than reliable calendar dates.

Therefore, job postings are grouped into recency buckets:

0-1 Days
1-7 Days
7-30 Days
30+ Days
Unknown

Output:

/jobmarket/processed/time_based
HDFS Output Directories

The Pig script generates:

/jobmarket/processed/jobs
/jobmarket/processed/skills
/jobmarket/processed/skills_demand
/jobmarket/processed/location
/jobmarket/processed/salary
/jobmarket/processed/salary_location
/jobmarket/processed/time_based
How to Run

Make sure Hadoop HDFS and YARN are running.

Run the Pig script using:

pig -x mapreduce task2_pig/scripts/task2_jobmarket.pig

If previous outputs exist, remove them before rerunning:

hdfs dfs -rm -r -f /jobmarket/processed
Verify Outputs

List the processed directories:

hdfs dfs -ls /jobmarket/processed/

View skill demand:

hdfs dfs -cat /jobmarket/processed/skills_demand/part-*

View location demand:

hdfs dfs -cat /jobmarket/processed/location/part-*

View salary results:

hdfs dfs -cat /jobmarket/processed/salary/part-*

View time-based results:

hdfs dfs -cat /jobmarket/processed/time_based/part-*
Task 2 Summary

Apache Pig transforms the cleaned job market data into normalized and aggregated datasets.

The processed HDFS outputs from Task 2 can be used by Task 3 for Hive-based analytics.
