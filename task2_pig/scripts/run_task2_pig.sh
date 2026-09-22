#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

: "${JAVA_HOME:=/usr/lib/jvm/java-8-openjdk-amd64}"
: "${HADOOP_HOME:=/usr/local/hadoop}"
: "${PIG_HOME:=/usr/local/pig}"
export JAVA_HOME HADOOP_HOME PIG_HOME
export PATH="$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PIG_HOME/bin:$PATH"

export HADOOP_CONF_DIR="${HADOOP_CONF_DIR:-$HADOOP_HOME/etc/hadoop}"
export HADOOP_OPTS="${HADOOP_OPTS:-} -Dmapreduce.jobhistory.address=localhost:10020 -Dmapreduce.jobhistory.webapp.address=localhost:19888"

command -v hdfs >/dev/null 2>&1 || { echo "ERROR: hdfs is not on PATH." >&2; exit 1; }
[[ -x "$PIG_HOME/bin/pig" ]] || { echo "ERROR: Pig launcher not found at $PIG_HOME/bin/pig." >&2; exit 1; }

if ! hdfs dfs -test -e /jobmarket/cleaned/jobs_cleaned.csv; then
	echo "ERROR: missing /jobmarket/cleaned/jobs_cleaned.csv. Run Task 1 first." >&2
	exit 1
fi

if command -v jps >/dev/null 2>&1 && ! jps | grep -q 'JobHistoryServer'; then
	if [[ -x "$HADOOP_HOME/bin/mapred" ]]; then
		echo ">>> Starting MapReduce JobHistoryServer ..."
		"$HADOOP_HOME/bin/mapred" --daemon start historyserver
	elif [[ -x "$HADOOP_HOME/sbin/mr-jobhistory-daemon.sh" ]]; then
		echo ">>> Starting MapReduce JobHistoryServer ..."
		"$HADOOP_HOME/sbin/mr-jobhistory-daemon.sh" start historyserver
	fi
fi

if command -v jps >/dev/null 2>&1 && ! jps | grep -q 'JobHistoryServer'; then
	echo "ERROR: JobHistoryServer is not running; Pig may retry localhost:10020." >&2
	exit 1
fi

echo ">>> Replacing Task 2 outputs ..."
hdfs dfs -rm -r -f /jobmarket/processed >/dev/null 2>&1 || true

echo ">>> Running Pig ..."
"$PIG_HOME/bin/pig" -x mapreduce -stop_on_failure "$PROJECT_ROOT/task2_pig/scripts/task2_jobmarket.pig"

for output_dir in jobs skills skills_demand location salary salary_location time_based; do
	if ! hdfs dfs -test -e "/jobmarket/processed/$output_dir/_SUCCESS"; then
		echo "ERROR: Pig did not complete /jobmarket/processed/$output_dir. Do not run Hive." >&2
		exit 1
	fi
done

echo ">>> Task 2 outputs:"
hdfs dfs -ls /jobmarket/processed