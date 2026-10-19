#!/usr/bin/env python3
import json

agents = [
    ("Translator 1", "2697e610-fa7b-4af6-b1fd-1edfe5385855"),
    ("Translator 2", "684e8fa1-5446-490a-854d-46eb74d2545d"),
    ("Translator 3", "9ccf923f-24bb-432d-9594-529660860b57"),
]

for label, cid in agents:
    log_path = rf"C:\Users\chann\.gemini\antigravity\brain\{cid}\.system_generated\logs\transcript.jsonl"
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"=== {label} ({cid[:8]}...) - Total lines: {len(lines)} ===")
        for line in lines[-4:]:
            d = json.loads(line)
            step = d.get("step_index")
            typ = d.get("type")
            calls = d.get("tool_calls", [])
            for c in calls:
                print(f"  Step {step}: tool={c.get('name')}, cmd={str(c.get('args', {}).get('CommandLine', ''))[:120]}")
            content = str(d.get("content", ""))[:120].replace("\n", " ")
            if content:
                print(f"  Step {step} content: {content}")
    except Exception as e:
        print(f"Error reading {label}: {e}")
