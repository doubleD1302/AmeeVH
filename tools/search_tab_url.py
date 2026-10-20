with open(r'c:\YostarGames\StellaSora_EN\StellaSora_Data\il2cpp_data\Metadata\global-metadata.dat', 'rb') as f:
    data = f.read()

import re
print("Searching case-insensitive 'downloadstore'...")
m = re.search(rb'downloadstore', data, re.I)
if m:
    print("Found at:", m.start())
else:
    print("Not found in metadata!")
