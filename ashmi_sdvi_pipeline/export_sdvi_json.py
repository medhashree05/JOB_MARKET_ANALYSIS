import subprocess
import json
import os

def export_sdvi_json():
    hql = """
    USE jobmarket_db;
    SET hive.cli.print.header=false;
    SELECT skill, month, mentions, growth_rate, sdvi, quadrant 
    FROM sdvi_analysis 
    WHERE month IS NOT NULL AND month != ''
    ORDER BY month ASC, sdvi DESC;
    """
    
    cmd = ["wsl.exe", "bash", "-lic", f'hive -e "{hql}"']
    print("Running Hive export query...")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    records = []
    for line in result.stdout.strip().split("\n"):
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

    output_path = r"c:\Users\Ashmi_SN\Desktop\bigdata\sdvi_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Successfully exported {len(records)} SDVI records to {output_path}")
    
    # Print sample
    if records:
        print("Sample record:")
        print(json.dumps(records[0], indent=2))
        
        # Quadrant summary
        from collections import Counter
        quads = Counter(r["quadrant"] for r in records if r["month"] == "2024-06")
        print("\nJune 2024 quadrant distribution:")
        for q, count in quads.items():
            print(f"  - {q}: {count}")

if __name__ == "__main__":
    export_sdvi_json()
