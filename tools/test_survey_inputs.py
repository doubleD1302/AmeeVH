import json
import os
import re

# Paths
root = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
master_glossary_path = os.path.join(root, "config", "master_glossary.json")
candidates_path = os.path.join(root, "work", "candidates_survey.json")
skill_names_translated_path = os.path.join(root, "work", "batches", "skill_names_translated.json")

with open(master_glossary_path, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

current_terms = master_glossary.get("terms", {})
current_forbidden = master_glossary.get("forbidden", {})

with open(candidates_path, "r", encoding="utf-8") as f:
    candidates = json.load(f)

with open(skill_names_translated_path, "r", encoding="utf-8") as f:
    skills_translated = json.load(f)

print(f"Initial terms: {len(current_terms)}, Forbidden: {len(current_forbidden)}")
print(f"Candidates to process: {len(candidates)}")
print(f"Pre-translated skills: {len(skills_translated)}")
