#!/usr/bin/env bash
set -euo pipefail

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Environment configuration
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export HIVE_HOME=/usr/local/hive

export PATH="$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin:$PATH"

export HADOOP_CONF_DIR="$HADOOP_HOME/etc/hadoop"

# Hive Beeline executable
BEELINE="$HIVE_HOME/bin/beeline"

# HiveServer2 JDBC connection
JDBC_URL="jdbc:hive2://localhost:10000/default"

# Check Beeline exists
if [[ ! -x "$BEELINE" ]]; then
    echo "ERROR: Hive Beeline not found at $BEELINE" >&2
    exit 1
fi

# Check HDFS command exists
command -v hdfs >/dev/null 2>&1 || {
    echo "ERROR: HDFS command not found." >&2
    exit 1
}

# Check HiveServer2 connection
echo "Checking HiveServer2 connection..."

"$BEELINE" -u "$JDBC_URL" -e "SHOW DATABASES;" || {
    echo "ERROR: Cannot connect to HiveServer2."
    echo "Make sure HiveServer2 is running on localhost:10000."
    exit 1
}

# Check Task 2 HDFS inputs
echo "Checking Task 2 HDFS outputs..."

for input_dir in jobs skills skills_demand location salary salary_location time_based; do
    if ! hdfs dfs -test -d "/jobmarket/processed/$input_dir"; then
        echo "ERROR: Missing HDFS input /jobmarket/processed/$input_dir"
        echo "Run Task 2 first."
        exit 1
    fi
done

echo "All Task 2 HDFS directories found."

# --------------------------------------------------
# STEP 1: Create Hive tables
# --------------------------------------------------

echo "STEP 1: Creating Hive tables..."

"$BEELINE" \
    -u "$JDBC_URL" \
    -f "$SCRIPT_DIR/01_create_tables.sql" || {
        echo "Task 3 failed while creating Hive tables." >&2
        exit 1
    }

echo "Hive tables created successfully."

# --------------------------------------------------
# STEP 2: Build skill trends
# --------------------------------------------------

echo "STEP 2: Building skill trends..."

"$BEELINE" \
    -u "$JDBC_URL" \
    -f "$SCRIPT_DIR/02_build_skill_trends.sql" || {
        echo "Task 3 failed while building skill trends." >&2
        exit 1
    }

echo "Skill trends built successfully."

# --------------------------------------------------
# STEP 3: Run analysis queries
# --------------------------------------------------

echo "STEP 3: Running analysis queries..."

"$BEELINE" \
    -u "$JDBC_URL" \
    -f "$SCRIPT_DIR/03_analysis.sql" || {
        echo "Task 3 failed while running analysis queries." >&2
        exit 1
    }

echo "All Task 3 Hive operations completed successfully."
