#!/usr/bin/env python3
import json

log_path = r"C:\Users\chann\.gemini\antigravity\brain\6b487742-db6a-481a-9efb-06d717951fbf\.system_generated\logs\transcript.jsonl"
with open(log_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines[-8:]:
    d = json.loads(line)
    step = d.get("step_index")
    typ = d.get("type")
    content = str(d.get("content", ""))[:250].replace("\n", " ")
    calls = d.get("tool_calls", [])
    print(f"=== Step {step} [{typ}] ===")
    if calls:
        for c in calls:
            print(f"  Call: {c.get('name')}, args: {str(c.get('args'))[:200]}")
    if content:
        print(f"  Content: {content[:200]}")
