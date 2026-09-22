-- Build skill demand by period and calculate growth.
-- The source dataset mostly contains relative dates (for example, "6 Days Ago").
-- Those rows remain in the 'unknown' period and are excluded from growth ranking.

USE jobmarket;

WITH skill_period_counts AS (
    SELECT
        LOWER(TRIM(s.skill)) AS skill,
        CASE
            WHEN j.posted_raw RLIKE '.*[0-9]{4}.*'
                THEN regexp_extract(j.posted_raw, '([0-9]{4})', 1)
            WHEN j.posted_raw RLIKE ".*'[0-9]{2}.*"
                THEN CONCAT('20', regexp_extract(j.posted_raw, "'([0-9]{2})", 1))
            ELSE 'unknown'
        END AS period,
        COUNT(DISTINCT s.job_id) AS job_count
    FROM job_skills s
    JOIN jobs j ON s.job_id = j.job_id
    WHERE s.skill IS NOT NULL AND TRIM(s.skill) <> ''
    GROUP BY
        LOWER(TRIM(s.skill)),
        CASE
            WHEN j.posted_raw RLIKE '.*[0-9]{4}.*'
                THEN regexp_extract(j.posted_raw, '([0-9]{4})', 1)
            WHEN j.posted_raw RLIKE ".*'[0-9]{2}.*"
                THEN CONCAT('20', regexp_extract(j.posted_raw, "'([0-9]{2})", 1))
            ELSE 'unknown'
        END
),
with_previous AS (
    SELECT
        skill,
        period,
        job_count,
        LAG(job_count, 1, 0) OVER (PARTITION BY skill ORDER BY period) AS previous_period_count
    FROM skill_period_counts
)
INSERT OVERWRITE TABLE skill_trends
SELECT
    skill,
    period,
    job_count,
    previous_period_count,
    CASE
        WHEN previous_period_count = 0 THEN NULL
        ELSE ROUND(100.0 * (job_count - previous_period_count) / previous_period_count, 2)
    END AS growth_pct
FROM with_previous;
