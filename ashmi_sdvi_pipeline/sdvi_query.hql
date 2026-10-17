USE jobmarket_db;

-- Drop previous summary tables if any
DROP TABLE IF EXISTS skill_monthly_counts;
DROP TABLE IF EXISTS sdvi_analysis;

-- 1. Monthly aggregated mentions per skill
CREATE TABLE skill_monthly_counts AS
SELECT 
    skill,
    posted_month AS month,
    COUNT(1) AS mentions
FROM job_skills
GROUP BY skill, posted_month;

-- 2. Compute window lag, growth rate, and SDVI
CREATE TABLE sdvi_analysis AS
WITH lag_calc AS (
    SELECT 
        skill,
        month,
        mentions,
        LAG(mentions, 1) OVER (PARTITION BY skill ORDER BY month) AS prev_mentions
    FROM skill_monthly_counts
),
growth_calc AS (
    SELECT 
        skill,
        month,
        mentions,
        prev_mentions,
        CASE 
            WHEN prev_mentions IS NULL OR prev_mentions = 0 THEN 0.0
            ELSE ROUND((CAST(mentions AS DOUBLE) - CAST(prev_mentions AS DOUBLE)) / CAST(prev_mentions AS DOUBLE), 4)
        END AS growth_rate
    FROM lag_calc
),
sdvi_calc AS (
    SELECT 
        skill,
        month,
        mentions,
        growth_rate,
        ROUND(growth_rate * LN(1.0 + CAST(mentions AS DOUBLE)), 4) AS sdvi
    FROM growth_calc
)
SELECT 
    skill,
    month,
    mentions,
    growth_rate,
    sdvi,
    CASE 
        WHEN growth_rate < -0.08 THEN 'Declining'
        WHEN growth_rate >= 0.20 AND mentions <= 100 THEN 'Emerging'
        WHEN mentions >= 75 AND growth_rate >= 0.04 THEN 'Established Growth'
        WHEN ABS(growth_rate) <= 0.18 THEN 'Stable'
        WHEN growth_rate > 0.0 THEN 'Emerging'
        ELSE 'Declining'
    END AS quadrant
FROM sdvi_calc
ORDER BY month ASC, sdvi DESC;

-- Validation preview of top SDVI skills for the latest month (2024-06)
SELECT 'TOP_10_EMERGING_SKILLS_LATEST_MONTH' AS report_section;
SELECT skill, month, mentions, growth_rate, sdvi, quadrant
FROM sdvi_analysis
WHERE month = '2024-06' AND quadrant = 'Emerging'
ORDER BY sdvi DESC
LIMIT 10;

-- Preview quadrant counts
SELECT 'QUADRANT_DISTRIBUTION_2024_06' AS report_section;
SELECT quadrant, COUNT(*) AS skill_count, ROUND(AVG(sdvi), 3) AS avg_sdvi, ROUND(AVG(mentions), 1) AS avg_mentions
FROM sdvi_analysis
WHERE month = '2024-06'
GROUP BY quadrant;
