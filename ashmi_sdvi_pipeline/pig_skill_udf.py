import re

SKILLS = []
try:
    with open('/mnt/c/Users/Ashmi_SN/Desktop/bigdata/skill_taxonomy.txt', 'r') as f:
        SKILLS = [line.strip() for line in f if line.strip()]
except Exception as e:
    # fallback
    pass

@outputSchema("skills:bag{t:(skill:chararray)}")
def extract_skills(description):
    if not description:
        return []
    matched = []
    for s in SKILLS:
        pattern = r'\b' + re.escape(s) + r'\b'
        if re.search(pattern, description, re.I):
            matched.append((s,))
    return matched
