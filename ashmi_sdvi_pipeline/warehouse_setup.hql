CREATE DATABASE IF NOT EXISTS jobmarket_db;
USE jobmarket_db;

-- 1. External table: jobs partitioned by posted_month
DROP TABLE IF EXISTS jobs;
CREATE EXTERNAL TABLE jobs (
    job_id STRING,
    title STRING,
    company STRING,
    location STRING,
    posted_date STRING
)
PARTITIONED BY (posted_month STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/ashmi_sn/jobmarket/cleaned/jobs';

-- 2. External table: job_skills partitioned by posted_month
DROP TABLE IF EXISTS job_skills;
CREATE EXTERNAL TABLE job_skills (
    job_id STRING,
    skill STRING
)
PARTITIONED BY (posted_month STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/ashmi_sn/jobmarket/cleaned/job_skills';

-- 3. Recover partitions from HDFS directory structure
MSCK REPAIR TABLE jobs;
MSCK REPAIR TABLE job_skills;

-- 4. Validation Query 1: Row counts per partition for jobs
SELECT 'VALIDATION_1_JOBS_PER_PARTITION' AS report_section;
SELECT posted_month, COUNT(*) AS job_count 
FROM jobs 
GROUP BY posted_month 
ORDER BY posted_month;

-- 5. Validation Query 2: Row counts per partition for job_skills
SELECT 'VALIDATION_2_SKILLS_PER_PARTITION' AS report_section;
SELECT posted_month, COUNT(*) AS skill_mention_count 
FROM job_skills 
GROUP BY posted_month 
ORDER BY posted_month;

-- 6. Validation Query 3: Distinct skill count
SELECT 'VALIDATION_3_DISTINCT_SKILLS' AS report_section;
SELECT COUNT(DISTINCT skill) AS total_unique_skills 
FROM job_skills;

-- 7. Preview: Top 10 overall most frequent skills
SELECT 'TOP_10_OVERALL_SKILLS' AS report_section;
SELECT skill, COUNT(*) AS total_mentions
FROM job_skills
GROUP BY skill
ORDER BY total_mentions DESC
LIMIT 10;
