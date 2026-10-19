#!/usr/bin/env python3
import json

with open("work/candidates_survey.json", "r", encoding="utf-8") as f:
    cand = json.load(f)

print(f"Total candidates: {len(cand)}")
for k, v in list(cand.items())[:20]:
    print(f"  {k:35} -> {v}")
