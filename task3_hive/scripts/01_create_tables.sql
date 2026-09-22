-- TASK 3: Hive tables for the Pig-processed job market data

CREATE DATABASE IF NOT EXISTS jobmarket;
USE jobmarket;

-- Recreate metadata when the Pig CSV format changes; external data is kept.
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS job_skills;
DROP TABLE IF EXISTS job_locations;
DROP TABLE IF EXISTS job_salary;
DROP TABLE IF EXISTS salary_by_location;
DROP TABLE IF EXISTS time_based;
DROP TABLE IF EXISTS skill_trends;
DROP TABLE IF EXISTS skills_demand;

CREATE EXTERNAL TABLE IF NOT EXISTS jobs (
    job_id STRING,
    job_title STRING,
    company_name STRING,
    company_id STRING,
    location STRING,
    location_raw STRING,
    currency STRING,
    min_salary DOUBLE,
    max_salary DOUBLE,
    avg_salary DOUBLE,
    experience_raw STRING,
    min_experience DOUBLE,
    max_experience DOUBLE,
    skills STRING,
    posted_raw STRING,
    reviews_count DOUBLE,
    rating DOUBLE
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/jobmarket/processed/jobs';

CREATE EXTERNAL TABLE IF NOT EXISTS job_skills (
    job_id STRING,
    job_title STRING,
    location STRING,
    currency STRING,
    skill STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/jobmarket/processed/skills';

CREATE EXTERNAL TABLE IF NOT EXISTS job_locations (
    location STRING,
    job_count BIGINT
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/jobmarket/processed/location';

CREATE EXTERNAL TABLE IF NOT EXISTS job_salary (
    job_title STRING,
    currency STRING,
    job_count BIGINT,
    min_avg_salary DOUBLE,
    max_avg_salary DOUBLE,
    mean_salary DOUBLE
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/jobmarket/processed/salary';

CREATE EXTERNAL TABLE IF NOT EXISTS salary_by_location (
    location STRING,
    currency STRING,
    job_count BIGINT,
    mean_salary DOUBLE
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/jobmarket/processed/salary_location';

CREATE EXTERNAL TABLE IF NOT EXISTS time_based (
    recency_bucket STRING,
    job_count BIGINT
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/jobmarket/processed/time_based';

-- This table is populated by 02_build_skill_trends.sql.
CREATE TABLE IF NOT EXISTS skill_trends (
    skill STRING,
    period STRING,
    job_count BIGINT,
    previous_period_count BIGINT,
    growth_pct DOUBLE
)
STORED AS TEXTFILE;

-- Optional Pig aggregate, useful for a fast top-skills report.
CREATE EXTERNAL TABLE IF NOT EXISTS skills_demand (
    skill STRING,
    job_count BIGINT
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/jobmarket/processed/skills_demand';

SHOW TABLES;
