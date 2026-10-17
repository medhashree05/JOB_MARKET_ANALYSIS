#!/bin/bash
set -e

echo "=========================================================="
echo "   STARTING END-TO-END JOB MARKET INTELLIGENCE PIPELINE   "
echo "=========================================================="

echo ""
echo "[Step 1] Starting Hadoop HDFS and YARN daemons..."
/usr/local/hadoop/sbin/start-dfs.sh
/usr/local/hadoop/sbin/start-yarn.sh
sleep 4

echo "Waiting for NameNode and leaving safe mode..."
hdfs dfsadmin -safemode leave || true
sleep 2
jps

echo ""
echo "[Step 2] Landing new real Kaggle dataset into HDFS..."
hdfs dfs -mkdir -p /user/ashmi_sn/jobmarket/raw /user/ashmi_sn/jobmarket/cleaned/jobs /user/ashmi_sn/jobmarket/cleaned/job_skills /user/ashmi_sn/jobmarket/warehouse
hdfs dfs -put -f /mnt/c/Users/Ashmi_SN/Desktop/bigdata/linkedin_postings.csv /mnt/c/Users/Ashmi_SN/Desktop/bigdata/skill_taxonomy.txt /user/ashmi_sn/jobmarket/raw/
hdfs dfs -ls -h /user/ashmi_sn/jobmarket/raw/

echo ""
echo "[Step 3] Running Pig Latin cleaning & skill extraction (MapReduce)..."
hdfs dfs -rm -r -f /user/ashmi_sn/jobmarket/cleaned/jobs /user/ashmi_sn/jobmarket/cleaned/job_skills || true
pig -x mapreduce /mnt/c/Users/Ashmi_SN/Desktop/bigdata/clean_and_extract.pig

echo ""
echo "[Step 4] Running Day 2 sanity check row counts..."
bash /mnt/c/Users/Ashmi_SN/Desktop/bigdata/check_day2_counts.sh

echo ""
echo "[Step 5] Running Hive external partitioned warehouse setup..."
hive -f /mnt/c/Users/Ashmi_SN/Desktop/bigdata/warehouse_setup.hql

echo ""
echo "[Step 6] Running HiveQL Window SDVI query & quadrant classification..."
hive -f /mnt/c/Users/Ashmi_SN/Desktop/bigdata/sdvi_query.hql

echo ""
echo "[Step 7] Exporting SDVI results to JSON..."
hive -e "USE jobmarket_db; SET hive.cli.print.header=false; SELECT skill, month, mentions, growth_rate, sdvi, quadrant FROM sdvi_analysis WHERE month IS NOT NULL AND month != '' ORDER BY month ASC, sdvi DESC;" > /mnt/c/Users/Ashmi_SN/Desktop/bigdata/hive_sdvi_raw.tsv

echo ""
echo "=========================================================="
echo "       PIPELINE EXECUTION COMPLETED SUCCESSFULLY!         "
echo "=========================================================="
