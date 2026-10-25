# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
rem = json.load(open(ROOT / "work/batches/remaining_lua_avg_cache.json", encoding="utf-8"))

idiom_indicators = [
    'bite the bullet', 'classic ', 'strike you', 'strikes you', 'singing your praises',
    'singing his praises', 'singing her praises', 'flashbang', 'smoke bomb', 'play along',
    'fair point', 'fit your ride', 'this is the spot', 'saved my skin', 'saved your skin',
    'you bet', 'run the numbers', 'play pretend', 'out of options', 'white lie',
    'wipe the floor', 'spill the beans', 'ring a bell', 'call it a day', 'under the weather',
    'piece of cake', 'break a leg', 'hit the sack', 'on thin ice', 'bite off more',
    'burn the midnight oil', 'once in a blue moon', 'see eye to eye', 'cost an arm',
    'ball is in your court', 'barking up the wrong tree', 'cry over spilled milk',
    'curiosity killed', 'actions speak louder', 'silver lining', 'hit the nail',
    'jump on the bandwagon', 'kill two birds', 'let the cat out', 'grain of salt',
    'taste of your own medicine', 'whole nine yards', 'wild goose chase', 'drop in the ocean',
    'butterflies in', 'cut corners', 'cold feet', 'benefit of the doubt', 'extra mile',
    'grapevine', 'in a nutshell', 'make ends meet', 'miss the boat', 'cup of tea',
    'cloud nine', 'out of the blue', 'devils advocate', 'pulling your leg', 'pulling my leg',
    'rain on', 'second to none', 'big picture', 'spit it out', 'stand your ground',
    'steal your thunder', 'last straw', 'thick and thin', 'time flies', 'under your nose',
    'up in the air', 'water under the bridge', 'wrap your head', 'zero in on',
    'no big deal', 'are you kidding', 'for real', 'cut it out', 'what a relief',
    'in hand', 'hands down', 'hands off', 'by the way', 'after all', 'to be honest',
    'as a matter of fact', 'long story short', 'give it a shot', 'have a blast',
    'hit the road', 'keep an eye', 'make sense', 'never mind', 'sleep on it',
    'take it easy', 'twenty-four seven', 'up to you', 'fed up', 'on the fence'
]

found = {}
for en, vi in rem.items():
    en_lower = en.lower()
    for ind in idiom_indicators:
        if ind in en_lower:
            found.setdefault(ind, []).append((en, vi))

print(f"Total idiom types detected: {len(found)}")
total_instances = sum(len(v) for v in found.values())
print(f"Total idiom occurrences in remaining cache: {total_instances}")
for ind, items in sorted(found.items(), key=lambda x: -len(x[1]))[:25]:
    print(f"  '{ind}': {len(items)} occurrences")
    sample_en, sample_vi = items[0]
    print(f"     EN: {sample_en}")
    print(f"     VI: {sample_vi}")
