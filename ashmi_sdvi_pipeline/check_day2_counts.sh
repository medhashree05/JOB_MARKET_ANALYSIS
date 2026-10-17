#!/bin/bash
echo "========================================================"
echo "          DAY 2 PIG LATIN SANITY CHECK & ROW COUNTS     "
echo "========================================================"
echo ""
echo "[1] Cleaned Jobs Partitions in HDFS:"
hdfs dfs -ls /user/ashmi_sn/jobmarket/cleaned/jobs
echo ""
echo "[2] Cleaned Job Skills Partitions in HDFS:"
hdfs dfs -ls /user/ashmi_sn/jobmarket/cleaned/job_skills
echo ""
echo "[3] Row counts per partition (Jobs Table):"
for dir in $(hdfs dfs -ls /user/ashmi_sn/jobmarket/cleaned/jobs | grep posted_month | awk '{print $8}'); do
    cnt=$(hdfs dfs -cat $dir/part* 2>/dev/null | wc -l)
    month=$(basename $dir)
    echo "  Partition: $month  -->  $cnt jobs"
done
total_jobs=$(hdfs dfs -cat /user/ashmi_sn/jobmarket/cleaned/jobs/*/part* 2>/dev/null | wc -l)
echo "  TOTAL CLEANED JOBS: $total_jobs"
echo ""
echo "[4] Row counts per partition (Job Skills Table):"
for dir in $(hdfs dfs -ls /user/ashmi_sn/jobmarket/cleaned/job_skills | grep posted_month | awk '{print $8}'); do
    cnt=$(hdfs dfs -cat $dir/part* 2>/dev/null | wc -l)
    month=$(basename $dir)
    echo "  Partition: $month  -->  $cnt skill mentions"
done
total_skills=$(hdfs dfs -cat /user/ashmi_sn/jobmarket/cleaned/job_skills/*/part* 2>/dev/null | wc -l)
echo "  TOTAL EXTRACTED SKILL MENTIONS: $total_skills"
echo ""
echo "[5] Sample rows from Cleaned Jobs:"
hdfs dfs -cat /user/ashmi_sn/jobmarket/cleaned/jobs/posted_month=2024-01/part* 2>/dev/null | head -n 3
echo ""
echo "[6] Sample rows from Cleaned Job Skills:"
hdfs dfs -cat /user/ashmi_sn/jobmarket/cleaned/job_skills/posted_month=2024-01/part* 2>/dev/null | head -n 5
echo "========================================================"
