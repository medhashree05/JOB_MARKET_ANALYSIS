-- TASK 3: Screenshot-ready Hive result sets
-- Run from WSL with: hive -S -f task3_hive/scripts/04_screenshot_queries.sql
USE jobmarket;

-- SCREENSHOT 1: Hive tables and row counts
SELECT 'jobs' AS table_name, COUNT(*) AS row_count FROM jobs
UNION ALL SELECT 'job_skills', COUNT(*) FROM job_skills
UNION ALL SELECT 'skills_demand', COUNT(*) FROM skills_demand
UNION ALL SELECT 'job_locations', COUNT(*) FROM job_locations
UNION ALL SELECT 'job_salary', COUNT(*) FROM job_salary
UNION ALL SELECT 'salary_by_location', COUNT(*) FROM salary_by_location
UNION ALL SELECT 'time_based', COUNT(*) FROM time_based
UNION ALL SELECT 'skill_trends', COUNT(*) FROM skill_trends;

-- SCREENSHOT 2: Top job roles
SELECT job_title, COUNT(*) AS job_count
FROM jobs
WHERE job_title IS NOT NULL AND TRIM(job_title) <> ''
GROUP BY job_title
ORDER BY job_count DESC
LIMIT 10;

-- SCREENSHOT 3: Top demanded skills
SELECT skill, job_count
FROM skills_demand
WHERE skill IS NOT NULL AND TRIM(skill) <> ''
ORDER BY job_count DESC
LIMIT 10;

-- SCREENSHOT 4: Job demand by location
SELECT location, job_count
FROM job_locations
WHERE location IS NOT NULL AND TRIM(location) <> ''
ORDER BY job_count DESC
LIMIT 10;

-- SCREENSHOT 5: Average salary by role
SELECT job_title, currency, job_count,
       ROUND(mean_salary, 2) AS average_salary,
       ROUND(min_avg_salary, 2) AS minimum_salary,
       ROUND(max_avg_salary, 2) AS maximum_salary
FROM job_salary
WHERE mean_salary IS NOT NULL
ORDER BY mean_salary DESC
LIMIT 10;

-- SCREENSHOT 6: Average salary by location
SELECT location, currency, job_count,
       ROUND(mean_salary, 2) AS average_salary
FROM salary_by_location
WHERE mean_salary IS NOT NULL
ORDER BY mean_salary DESC
LIMIT 10;

-- SCREENSHOT 7: Skill and role combinations
SELECT job_title, skill, COUNT(DISTINCT job_id) AS job_count
FROM job_skills
WHERE job_title IS NOT NULL AND TRIM(job_title) <> ''
  AND skill IS NOT NULL AND TRIM(skill) <> ''
GROUP BY job_title, skill
ORDER BY job_count DESC
LIMIT 15;

-- SCREENSHOT 8: Posting recency
SELECT recency_bucket, job_count
FROM time_based
ORDER BY job_count DESC;

-- SCREENSHOT 9: Emerging skills with explicit years only
SELECT skill, period, job_count, previous_period_count, growth_pct
FROM skill_trends
WHERE period <> 'unknown'
  AND previous_period_count > 0
  AND growth_pct > 0
ORDER BY growth_pct DESC, job_count DESC
LIMIT 15;

-- SCREENSHOT 10: Final data-quality checks
SELECT 'jobs_without_title' AS check_name, COUNT(*) AS issue_count
FROM jobs
WHERE job_title IS NULL OR TRIM(job_title) = ''
UNION ALL
SELECT 'jobs_without_location', COUNT(*)
FROM jobs
WHERE location IS NULL OR TRIM(location) = ''
UNION ALL
SELECT 'jobs_with_invalid_salary', COUNT(*)
FROM jobs
WHERE avg_salary IS NOT NULL AND avg_salary < 0
UNION ALL
SELECT 'duplicate_job_ids', COUNT(*) - COUNT(DISTINCT job_id)
FROM jobs;

-- FURTHER ANALYSIS A: Top hiring companies
SELECT company_name, COUNT(*) AS job_count
FROM jobs
WHERE company_name IS NOT NULL AND TRIM(company_name) <> ''
GROUP BY company_name
ORDER BY job_count DESC
LIMIT 15;

-- FURTHER ANALYSIS B: Experience-level demand
SELECT experience_raw, COUNT(*) AS job_count
FROM jobs
WHERE experience_raw IS NOT NULL AND TRIM(experience_raw) <> ''
GROUP BY experience_raw
ORDER BY job_count DESC
LIMIT 15;

-- FURTHER ANALYSIS C: Salary by currency
SELECT currency, COUNT(*) AS job_count,
       ROUND(AVG(avg_salary), 2) AS average_salary,
       ROUND(MIN(avg_salary), 2) AS minimum_salary,
       ROUND(MAX(avg_salary), 2) AS maximum_salary
FROM jobs
WHERE currency IS NOT NULL AND avg_salary IS NOT NULL
GROUP BY currency
ORDER BY job_count DESC;

-- FURTHER ANALYSIS D: Skills required by the most roles
SELECT skill, COUNT(DISTINCT job_title) AS distinct_roles,
       COUNT(DISTINCT job_id) AS job_count
FROM job_skills
WHERE skill IS NOT NULL AND TRIM(skill) <> ''
GROUP BY skill
ORDER BY distinct_roles DESC, job_count DESC
LIMIT 15;

-- FURTHER ANALYSIS E: Role demand by location
SELECT job_title, location, COUNT(*) AS job_count
FROM jobs
WHERE job_title IS NOT NULL AND location IS NOT NULL
GROUP BY job_title, location
ORDER BY job_count DESC
LIMIT 20;
