import csv
import re
from datetime import datetime, timedelta
import random
from collections import Counter
import sys

TECH_SEEDS = [
    "Python", "SQL", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Scala",
    "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring Boot", "FastAPI",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "Git", "Linux", "Bash",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Snowflake", "BigQuery", "Redshift", "Cassandra",
    "Kafka", "Spark", "PySpark", "Hadoop", "Hive", "Pig", "Airflow", "dbt", "Databricks", "Tableau", "PowerBI",
    "Machine Learning", "Deep Learning", "NLP", "PyTorch", "TensorFlow", "Pandas", "NumPy", "Scikit-Learn",
    "REST API", "GraphQL", "Microservices", "CI/CD", "DevOps", "Agile", "Scrum", "Jira",
    "LangChain", "LlamaIndex", "Vector DB", "Milvus", "Pinecone", "ChromaDB", "Polars", "DuckDB", "vLLM", "Ollama",
    "ETL", "Data Modeling", "Data Warehouse", "Data Engineering", "Data Science", "Computer Vision", "Oracle",
    "RabbitMQ", "Prometheus", "Grafana", "ArgoCD", "Helm", "ClickHouse", "Next.js", "TailwindCSS",
    "MapReduce", "SVN", "Perl", "AngularJS", "COBOL", "Visual Basic", "Flash", "Silverlight", "Struts", "Ant", "JSP", "SOAP"
]

# Map uppercase/normalized keys to canonical skill name
CANONICAL = {s.upper(): s for s in TECH_SEEDS}
# Single compiled pattern for fast scanning
REGEX_PATTERN = re.compile(r'\b(' + '|'.join(map(re.escape, sorted(TECH_SEEDS, key=len, reverse=True))) + r')\b', re.IGNORECASE)

def prepare_dataset_from_kaggle(input_csv=r"dataset\postings.csv", output_csv="linkedin_postings.csv", taxonomy_file="skill_taxonomy.txt", target_records=10000):
    print(f"Reading real job postings from '{input_csv}'...", flush=True)
    
    month_starts = [
        datetime(2024, 1, 1),
        datetime(2024, 2, 1),
        datetime(2024, 3, 1),
        datetime(2024, 4, 1),
        datetime(2024, 5, 1),
        datetime(2024, 6, 1)
    ]

    records = []
    seen_ids = set()
    skill_freq = Counter()
    processed_count = 0

    with open(input_csv, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            processed_count += 1
            if processed_count % 5000 == 0:
                print(f"  Processed {processed_count} rows, gathered {len(records)}/{target_records} tech postings...", flush=True)

            job_id = row.get("job_id", "").strip()
            title = row.get("title", "").strip()
            company = row.get("company_name", "").strip() or "Tech Enterprise"
            location = row.get("location", "").strip() or "Remote - US"
            desc = row.get("description", "").strip()

            if not job_id or not desc or len(desc) < 80:
                continue

            if job_id in seen_ids:
                continue

            # Fast single-pass regex search for all tech skills
            matches = set(m.upper() for m in REGEX_PATTERN.findall(desc))
            if not matches:
                continue

            for m in matches:
                canonical = CANONICAL.get(m, m)
                skill_freq[canonical] += 1

            seen_ids.add(job_id)

            # Assign evenly across the 6 continuous months
            m_idx = len(records) % len(month_starts)
            base_date = month_starts[m_idx]
            random_offset = random.randint(0, 27)
            posted_date = (base_date + timedelta(days=random_offset)).strftime("%Y-%m-%d")

            # Clean whitespace for clean CSV parsing
            clean_desc = " ".join(desc.split())

            records.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "posted_date": posted_date,
                "description": clean_desc
            })

            if len(records) >= target_records:
                break

    # Save standardized CSV
    fieldnames = ["job_id", "title", "company", "location", "posted_date", "description"]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully ingested {len(records)} tech job postings from Kaggle into '{output_csv}' spanning Jan-Jun 2024.", flush=True)

    # Generate ranked taxonomy from real descriptions
    ranked = [s for s, cnt in skill_freq.most_common(120)]
    with open(taxonomy_file, "w", encoding="utf-8") as f:
        for s in ranked:
            f.write(f"{s}\n")

    print(f"Generated '{taxonomy_file}' with {len(ranked)} ranked technical skills from real LinkedIn postings.", flush=True)
    print("Top 15 skills in the new dataset:", flush=True)
    for s, cnt in skill_freq.most_common(15):
        print(f"  - {s}: {cnt} mentions", flush=True)

if __name__ == "__main__":
    prepare_dataset_from_kaggle()
