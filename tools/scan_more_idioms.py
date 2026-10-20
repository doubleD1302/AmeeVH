import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

idiom_list = [
    r'die is cast', r'stiff me', r'beat.*punch', r'phone charm|that charm',
    r'anything but', r'pull.*strings', r'hold the line', r'cold feet',
    r'face the music', r'spill the beans', r'bite the bullet',
    r'cut corners', r'call it a day', r'break a leg', r'under the weather',
    r'hit the sack', r'piece of cake', r'on the fence', r'at the drop of a hat',
    r'see eye to eye', r'burn bridges', r'water under the bridge',
    r'elephant in the room', r'cat.*bag', r'barking up', r'cost an arm',
    r'in a nutshell', r'read between the lines', r'stab.*back',
    r'kick the bucket', r'blow up', r'blow smoke', r'ring a bell',
    r'rule of thumb', r'shoot the breeze', r'skating on thin ice',
    r'sour grapes', r'take it with a grain of salt', r'tip of the iceberg',
    r'through thick and thin', r'throw under the bus', r'turn a blind eye',
    r'up in the air', r'word of mouth', r'your guess is as good as mine',
    r'cross that bridge', r'devil\'s advocate', r'fit as a fiddle',
    r'head over heels', r'keep.*at bay', r'leave no stone unturned',
    r'make ends meet', r'off the hook', r'pull somebody\'s leg',
    r'rain check', r'spill.*guts', r'take for granted',
    r'throw in the towel', r'under the table', r'out of the woods',
    r'neck of the woods', r'back to square one', r'bad blood',
    r'behind closed doors', r'by the skin of', r'cut to the chase',
    r'draw the line', r'get cold feet', r'give.*cold shoulder',
    r'in the same boat', r'jump the gun', r'keep.*chin up',
    r'kill two birds', r'let the cat out', r'miss the boat',
    r'no brainer', r'on the same page', r'play devil', r'pull yourself together',
    r'safe and sound', r'second thoughts', r'skeleton in', r'take a hike',
    r'the last straw', r'through the grapevine', r'under someone\'s nose',
    r'wash hands of', r'zero tolerance'
]

print("SEARCHING FOR EXTENSIVE IDIOMS IN PART A SOURCE:")
found_count = 0
for pat in idiom_list:
    reg = re.compile(r'\b(?:' + pat + r')\b', re.IGNORECASE)
    matches = []
    for k, v in src.items():
        if reg.search(v):
            matches.append((k, v, dst.get(k, '')))
    if matches:
        found_count += len(matches)
        print(f"\n[Idiom match: {pat} ({len(matches)})]")
        for m in matches:
            print(f"  {m[0]}:")
            print(f"    EN: {m[1]}")
            print(f"    VI: {m[2]}")

print(f"\nTotal idiom matches found: {found_count}")
