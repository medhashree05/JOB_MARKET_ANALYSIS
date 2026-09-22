-- TASK 3: Job market intelligence queries
USE jobmarket;

-- 1. Most demanded job roles (computed from normalized jobs)
SELECT job_title, COUNT(*) AS job_count
FROM jobs
WHERE job_title IS NOT NULL AND TRIM(job_title) <> ''
GROUP BY job_title
ORDER BY job_count DESC
LIMIT 20;

-- 2. Most demanded skills
SELECT skill, job_count
FROM skills_demand
WHERE skill IS NOT NULL AND TRIM(skill) <> ''
ORDER BY job_count DESC
LIMIT 20;

-- 3. Job demand by location
SELECT location, job_count
FROM job_locations
WHERE location IS NOT NULL AND TRIM(location) <> ''
ORDER BY job_count DESC
LIMIT 20;

-- 4. Salary by job role, retaining currency to avoid mixing INR and USD
SELECT job_title, currency, job_count,
       ROUND(mean_salary, 2) AS average_salary,
       ROUND(min_avg_salary, 2) AS minimum_salary,
       ROUND(max_avg_salary, 2) AS maximum_salary
FROM job_salary
WHERE mean_salary IS NOT NULL
ORDER BY mean_salary DESC
LIMIT 20;

-- 5. Salary by location and currency
SELECT location, currency, job_count, ROUND(mean_salary, 2) AS average_salary
FROM salary_by_location
WHERE mean_salary IS NOT NULL
ORDER BY mean_salary DESC
LIMIT 20;

-- 6. Skill + job role relationships
SELECT s.job_title, s.skill, COUNT(DISTINCT s.job_id) AS job_count
FROM job_skills s
WHERE s.job_title IS NOT NULL AND s.skill IS NOT NULL
GROUP BY s.job_title, s.skill
ORDER BY job_count DESC
LIMIT 50;

-- 7. Posting recency distribution
SELECT recency_bucket, job_count
FROM time_based
ORDER BY job_count DESC;

-- 8. Skill demand over available explicit time periods.
-- Rows with relative dates are retained as 'unknown' but excluded here.
SELECT skill, period, job_count, previous_period_count, growth_pct
FROM skill_trends
WHERE period <> 'unknown'
ORDER BY period, job_count DESC;

-- 9. Emerging skills: positive growth in an explicit period.
SELECT skill, period, job_count, previous_period_count, growth_pct
FROM skill_trends
WHERE period <> 'unknown'
  AND previous_period_count > 0
  AND growth_pct > 0
ORDER BY growth_pct DESC, job_count DESC
LIMIT 25;

-- 10. Data quality checks
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
