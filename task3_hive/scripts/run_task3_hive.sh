#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${HADOOP_HOME:-}" && -d /usr/local/hadoop ]]; then
	export HADOOP_HOME=/usr/local/hadoop
fi
if [[ -z "${HIVE_HOME:-}" && -d /usr/local/hive ]]; then
	export HIVE_HOME=/usr/local/hive
fi
if [[ -n "${HADOOP_HOME:-}" ]]; then
	export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"
fi
if [[ -n "${HIVE_HOME:-}" ]]; then
	export PATH="$HIVE_HOME/bin:$PATH"
fi

export HADOOP_CONF_DIR="${HADOOP_CONF_DIR:-${HADOOP_HOME:-/usr/local/hadoop}/etc/hadoop}"

command -v hive >/dev/null 2>&1 || {
	echo "ERROR: hive is not on PATH. Set HIVE_HOME and PATH first." >&2
	exit 1
}
command -v hdfs >/dev/null 2>&1 || {
	echo "ERROR: hdfs is not on PATH. Set HADOOP_HOME and PATH first." >&2
	exit 1
}

for input_dir in jobs skills skills_demand location salary salary_location time_based; do
	if ! hdfs dfs -test -d "/jobmarket/processed/$input_dir"; then
		echo "ERROR: missing HDFS input /jobmarket/processed/$input_dir. Run Task 2 first." >&2
		exit 1
	fi
done

# The processed directories must already exist in HDFS after Task 2.
hive -f "$SCRIPT_DIR/01_create_tables.sql" || {
	echo "Task 3 failed while creating Hive tables." >&2
	exit 1
}
hive -f "$SCRIPT_DIR/02_build_skill_trends.sql" || {
	echo "Task 3 failed while building skill trends." >&2
	exit 1
}
hive -f "$SCRIPT_DIR/03_analysis.sql" || {
	echo "Task 3 failed while running analysis queries." >&2
	exit 1
}
