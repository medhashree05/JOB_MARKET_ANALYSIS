import json
import os

def convert_tsv_to_json(tsv_path="hive_sdvi_raw.tsv", json_path="sdvi_results.json"):
    if not os.path.exists(tsv_path):
        print(f"Error: {tsv_path} not found.")
        return

    records = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("WARN") or line.startswith("SLF4J") or line.startswith("Logging") or line.startswith("Hive Session") or line.startswith("OK") or line.startswith("Time taken"):
                continue
            parts = line.split("\t")
            if len(parts) == 6:
                skill, month, mentions, growth_rate, sdvi, quadrant = parts
                try:
                    records.append({
                        "skill": skill,
                        "month": month,
                        "mentions": int(mentions),
                        "growth_rate": round(float(growth_rate), 4),
                        "sdvi": round(float(sdvi), 4),
                        "quadrant": quadrant
                    })
                except ValueError:
                    continue

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Successfully converted {len(records)} SDVI records to '{json_path}'.")

if __name__ == "__main__":
    convert_tsv_to_json()
