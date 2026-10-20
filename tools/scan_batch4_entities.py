import json
import os
import re
from collections import Counter

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
b4_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b4.json")
with open(b4_path, "r", encoding="utf-8") as f:
    b4 = json.load(f)

# Find capitalized multi-word phrases and common named entities
entities = Counter()
for k, text in b4.items():
    # Find phrases of 2-3 capitalized words
    matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", text)
    for m in matches:
        if m not in ("I have", "I am", "I will", "You are", "We will", "They are", "It is", "There is", "That is"):
            entities[m] += 1

print("Top 40 multi-word entities in Batch 4:")
for entity, count in entities.most_common(40):
    print(f"  {entity}: {count}")

single_words = Counter()
for k, text in b4.items():
    words = re.findall(r"\b[A-Z][a-z]{3,}\b", text)
    for w in words:
        if w not in ("This", "That", "What", "When", "Where", "Have", "There", "Then", "Just", "Well", "Look", "Come", "Wait", "Yeah", "Right"):
            single_words[w] += 1

print("\nTop 40 single word capitalized terms in Batch 4:")
for w, count in single_words.most_common(40):
    print(f"  {w}: {count}")
