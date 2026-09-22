-- ============================================================
-- TASK 2: JOB MARKET AGGREGATION USING APACHE PIG
-- ============================================================

REGISTER '/usr/local/pig/lib/piggybank.jar';

-- ============================================================
-- 1. LOAD CLEANED DATA
-- ============================================================

jobs_raw = LOAD '/jobmarket/cleaned/jobs_cleaned.csv'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',')
    AS (
        job_id:chararray,
        job_title:chararray,
        company_name:chararray,
        company_id:chararray,
        location:chararray,
        location_raw:chararray,
        currency:chararray,
        min_salary:double,
        max_salary:double,
        avg_salary:double,
        experience_raw:chararray,
        min_experience:double,
        max_experience:double,
        skills:chararray,
        posted_raw:chararray,
        reviews_count:double,
        rating:double
    );

-- Remove CSV header
jobs = FILTER jobs_raw BY job_id != 'job_id';

-- ============================================================
-- 2. NORMALIZE JOB DATA
-- ============================================================

jobs_normalized = FOREACH jobs GENERATE
    job_id,
    LOWER(TRIM(job_title)) AS job_title,
    company_name,
    company_id,
    LOWER(TRIM(location)) AS location,
    location_raw,
    currency,
    min_salary,
    max_salary,
    avg_salary,
    experience_raw,
    min_experience,
    max_experience,
    skills,
    posted_raw,
    reviews_count,
    rating;

STORE jobs_normalized
    INTO '/jobmarket/processed/jobs'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',');

-- ============================================================
-- 3. CREATE JOB-SKILL RECORDS
-- ============================================================

skills_source = FILTER jobs BY
    skills IS NOT NULL AND
    skills != '' AND
    LOWER(TRIM(skills)) != 'not specified';

-- Split comma-separated skills into individual values
skills_split = FOREACH skills_source GENERATE
    job_id,
    LOWER(TRIM(job_title)) AS job_title,
    LOWER(TRIM(location)) AS location,
    currency,
    FLATTEN(TOKENIZE(skills, ',')) AS skill;

-- Clean individual skill values
skills_clean = FOREACH skills_split GENERATE
    job_id,
    job_title,
    location,
    currency,
    LOWER(TRIM(skill)) AS skill;

-- Remove empty skill values
skills_clean = FILTER skills_clean BY
    skill IS NOT NULL AND skill != '';

-- Remove duplicate skill mentions within the same job
skills_unique = DISTINCT skills_clean;

STORE skills_unique
    INTO '/jobmarket/processed/skills'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',');

-- ============================================================
-- 4. SKILL DEMAND AGGREGATION
-- ============================================================

skill_group = GROUP skills_unique BY skill;

skill_demand = FOREACH skill_group GENERATE
    group AS skill,
    COUNT(skills_unique) AS job_count;

skill_demand = ORDER skill_demand BY job_count DESC;

STORE skill_demand
    INTO '/jobmarket/processed/skills_demand'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',');

-- ============================================================
-- 5. LOCATION DEMAND AGGREGATION
-- ============================================================

location_group = GROUP jobs BY location;

location_demand = FOREACH location_group GENERATE
    LOWER(TRIM(group)) AS location,
    COUNT(jobs) AS job_count;

location_demand = ORDER location_demand BY job_count DESC;

STORE location_demand
    INTO '/jobmarket/processed/location'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',');

-- ============================================================
-- 6. SALARY AGGREGATION BY ROLE
-- ============================================================

salary_jobs = FILTER jobs BY
    avg_salary IS NOT NULL AND
    avg_salary > 0 AND
    currency IS NOT NULL;

role_salary_group = GROUP salary_jobs BY
    (job_title, currency);

role_salary = FOREACH role_salary_group GENERATE
    LOWER(TRIM(group.job_title)) AS job_title,
    group.currency AS currency,
    COUNT(salary_jobs) AS job_count,
    MIN(salary_jobs.avg_salary) AS min_avg_salary,
    MAX(salary_jobs.avg_salary) AS max_avg_salary,
    AVG(salary_jobs.avg_salary) AS mean_salary;

STORE role_salary
    INTO '/jobmarket/processed/salary'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',');

-- ============================================================
-- 7. SALARY BY LOCATION
-- ============================================================

location_salary_group = GROUP salary_jobs BY
    (location, currency);

location_salary = FOREACH location_salary_group GENERATE
    LOWER(TRIM(group.location)) AS location,
    group.currency AS currency,
    COUNT(salary_jobs) AS job_count,
    AVG(salary_jobs.avg_salary) AS mean_salary;

STORE location_salary
    INTO '/jobmarket/processed/salary_location'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',');

-- ============================================================
-- 8. TIME / RECENCY BUCKETS
-- ============================================================

time_data = FOREACH jobs GENERATE
    job_id,
    posted_raw,
    (
       CASE
    WHEN posted_raw IS NULL OR TRIM(posted_raw) == '' THEN 'Unknown'
    WHEN LOWER(posted_raw) MATCHES '.*today.*' THEN '0-1 Days'
    WHEN LOWER(posted_raw) MATCHES '.*day.*' THEN '1-7 Days'
    WHEN LOWER(posted_raw) MATCHES '.*week.*' THEN '7-30 Days'
    WHEN LOWER(posted_raw) MATCHES '.*month.*' THEN '30+ Days'
    ELSE 'Unknown'
END
    ) AS recency_bucket;

time_group = GROUP time_data BY recency_bucket;

time_demand = FOREACH time_group GENERATE
    group AS recency_bucket,
    COUNT(time_data) AS job_count;

STORE time_demand
    INTO '/jobmarket/processed/time_based'
    USING org.apache.pig.piggybank.storage.CSVExcelStorage(',');

-- ============================================================
-- END OF TASK 2
-- ============================================================
