import json
import re

p3 = json.load(open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/pillar3_translated.json', encoding='utf-8'))
p4 = json.load(open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/pillar4_translated.json', encoding='utf-8'))

# List of English words that are NOT acceptable in translated text (common English words)
common_en_words = [
    'the', 'of', 'and', 'to', 'a', 'in', 'that', 'is', 'was', 'he', 'for', 'it', 'with', 'as', 'his', 'on', 'be', 'at',
    'by', 'i', 'this', 'had', 'not', 'are', 'but', 'from', 'or', 'have', 'an', 'they', 'which', 'one', 'you', 'were',
    'her', 'all', 'she', 'there', 'would', 'their', 'we', 'him', 'been', 'has', 'when', 'who', 'will', 'more', 'no',
    'if', 'out', 'so', 'said', 'what', 'up', 'its', 'about', 'into', 'than', 'them', 'can', 'only', 'other', 'new',
    'some', 'could', 'time', 'these', 'two', 'may', 'then', 'do', 'first', 'any', 'my', 'now', 'such', 'like', 'our',
    'over', 'man', 'me', 'even', 'most', 'made', 'after', 'also', 'did', 'many', 'before', 'must', 'through', 'back',
    'years', 'where', 'much', 'your', 'way', 'well', 'down', 'should', 'because', 'each', 'just', 'those', 'people',
    'mr', 'how', 'too', 'little', 'state', 'good', 'very', 'make', 'world', 'still', 'own', 'see', 'men', 'work',
    'long', 'get', 'here', 'between', 'both', 'life', 'being', 'under', 'never', 'day', 'same', 'another', 'know',
    'while', 'last', 'might', 'great', 'old', 'year', 'off', 'come', 'since', 'against', 'go', 'came', 'right', 'used',
    'take', 'three', 'himself', 'look', 'few', 'part'
]
en_word_re = re.compile(r'\b(' + '|'.join(common_en_words) + r')\b', re.IGNORECASE)

def find_english_in_data(pillar_name, data):
    print(f"=== Checking English in {pillar_name} ===")
    found = []
    for tbl, info in data.items():
        if tbl == "DiscIP":
            continue
        for k, v in info.get("entries", {}).items():
            matches = en_word_re.findall(v)
            if matches:
                # filter false positives like acronyms or single characters
                found.append((tbl, k, v, list(set(matches))))
    print(f"Found {len(found)} strings with English words in {pillar_name}")
    for tbl, k, v, m in found:
        print(f"[{tbl}.{k}] (words: {m}): {v}")
    return found

p3_en = find_english_in_data("Pillar 3", p3)
p4_en = find_english_in_data("Pillar 4", p4)
