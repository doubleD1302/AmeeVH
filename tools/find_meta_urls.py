import re

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_Data\il2cpp_data\Metadata\global-metadata.dat', 'rb') as f:
    meta = f.read()

matches = re.findall(rb'https?://[^\x00\s"\'<>]+', meta)
for m in sorted(set(matches)):
    print(m.decode('latin1', errors='ignore'))
