REGISTER '/usr/local/pig/lib/piggybank.jar';
DEFINE CSVLoader org.apache.pig.piggybank.storage.CSVExcelStorage(',', 'NO_MULTILINE', 'UNIX', 'SKIP_INPUT_HEADER');
REGISTER '/mnt/c/Users/Ashmi_SN/Desktop/bigdata/pig_skill_udf.py' USING jython AS myfuncs;

-- 1. Load raw CSV from HDFS
raw_postings = LOAD '/user/ashmi_sn/jobmarket/raw/linkedin_postings.csv' USING CSVLoader() AS (
    job_id:chararray,
    title:chararray,
    company:chararray,
    location:chararray,
    posted_date:chararray,
    description:chararray
);

-- 2. Filter null/malformed rows and header
filtered_postings = FILTER raw_postings BY 
    (job_id IS NOT NULL) AND (job_id != '') AND (job_id != 'job_id') AND
    (posted_date IS NOT NULL) AND (posted_date != '') AND
    (description IS NOT NULL) AND (description != '');

-- 3. Deduplicate
dedup_postings = DISTINCT filtered_postings;

-- 4. Normalize location to lowercase and posted_date to yyyy-MM
cleaned_jobs = FOREACH dedup_postings GENERATE
    job_id,
    title,
    company,
    LOWER(TRIM(location)) AS location,
    posted_date,
    SUBSTRING(posted_date, 0, 7) AS posted_month,
    description;

-- 5. Extract skills from description using skill_taxonomy via UDF
job_skills_raw = FOREACH cleaned_jobs GENERATE
    job_id,
    posted_month,
    FLATTEN(myfuncs.extract_skills(description)) AS skill;

job_skills = FILTER job_skills_raw BY skill IS NOT NULL AND skill != '';

-- 6. Split cleaned jobs by partition (posted_month)
SPLIT cleaned_jobs INTO 
    j_2024_01 IF posted_month == '2024-01',
    j_2024_02 IF posted_month == '2024-02',
    j_2024_03 IF posted_month == '2024-03',
    j_2024_04 IF posted_month == '2024-04',
    j_2024_05 IF posted_month == '2024-05',
    j_2024_06 IF posted_month == '2024-06';

j_out_01 = FOREACH j_2024_01 GENERATE job_id, title, company, location, posted_date;
j_out_02 = FOREACH j_2024_02 GENERATE job_id, title, company, location, posted_date;
j_out_03 = FOREACH j_2024_03 GENERATE job_id, title, company, location, posted_date;
j_out_04 = FOREACH j_2024_04 GENERATE job_id, title, company, location, posted_date;
j_out_05 = FOREACH j_2024_05 GENERATE job_id, title, company, location, posted_date;
j_out_06 = FOREACH j_2024_06 GENERATE job_id, title, company, location, posted_date;

STORE j_out_01 INTO '/user/ashmi_sn/jobmarket/cleaned/jobs/posted_month=2024-01' USING PigStorage(',');
STORE j_out_02 INTO '/user/ashmi_sn/jobmarket/cleaned/jobs/posted_month=2024-02' USING PigStorage(',');
STORE j_out_03 INTO '/user/ashmi_sn/jobmarket/cleaned/jobs/posted_month=2024-03' USING PigStorage(',');
STORE j_out_04 INTO '/user/ashmi_sn/jobmarket/cleaned/jobs/posted_month=2024-04' USING PigStorage(',');
STORE j_out_05 INTO '/user/ashmi_sn/jobmarket/cleaned/jobs/posted_month=2024-05' USING PigStorage(',');
STORE j_out_06 INTO '/user/ashmi_sn/jobmarket/cleaned/jobs/posted_month=2024-06' USING PigStorage(',');

-- 7. Split job skills by partition (posted_month)
SPLIT job_skills INTO 
    s_2024_01 IF posted_month == '2024-01',
    s_2024_02 IF posted_month == '2024-02',
    s_2024_03 IF posted_month == '2024-03',
    s_2024_04 IF posted_month == '2024-04',
    s_2024_05 IF posted_month == '2024-05',
    s_2024_06 IF posted_month == '2024-06';

s_out_01 = FOREACH s_2024_01 GENERATE job_id, skill;
s_out_02 = FOREACH s_2024_02 GENERATE job_id, skill;
s_out_03 = FOREACH s_2024_03 GENERATE job_id, skill;
s_out_04 = FOREACH s_2024_04 GENERATE job_id, skill;
s_out_05 = FOREACH s_2024_05 GENERATE job_id, skill;
s_out_06 = FOREACH s_2024_06 GENERATE job_id, skill;

STORE s_out_01 INTO '/user/ashmi_sn/jobmarket/cleaned/job_skills/posted_month=2024-01' USING PigStorage(',');
STORE s_out_02 INTO '/user/ashmi_sn/jobmarket/cleaned/job_skills/posted_month=2024-02' USING PigStorage(',');
STORE s_out_03 INTO '/user/ashmi_sn/jobmarket/cleaned/job_skills/posted_month=2024-03' USING PigStorage(',');
STORE s_out_04 INTO '/user/ashmi_sn/jobmarket/cleaned/job_skills/posted_month=2024-04' USING PigStorage(',');
STORE s_out_05 INTO '/user/ashmi_sn/jobmarket/cleaned/job_skills/posted_month=2024-05' USING PigStorage(',');
STORE s_out_06 INTO '/user/ashmi_sn/jobmarket/cleaned/job_skills/posted_month=2024-06' USING PigStorage(',');
