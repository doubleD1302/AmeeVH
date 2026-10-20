import json
import re

TOKEN_REGEXES = [
    r"==[A-Z0-9_]+==",
    r"\{\d+\}",
    r"&Param\d+&",
    r"<color=[^>]+>",
    r"</color>",
    r"<r=[^>]+>",
    r"</r>",
    r"##[^#]+#[0-9]+#"
]

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))
print(f"Total items: {len(data)}")

tokens_found = []
for it in data:
    en = it.get('en', '')
    zh = it.get('zh', '')
    for r in TOKEN_REGEXES:
        m_en = re.findall(r, en)
        m_zh = re.findall(r, zh)
        if m_en or m_zh:
            tokens_found.append((it['key'], r, m_en, m_zh))

print(f"Items with tokens: {len(tokens_found)}")
for k, r, m_en, m_zh in tokens_found:
    print(f"[{k}] Regex {r}: EN={m_en}, ZH={m_zh}")
