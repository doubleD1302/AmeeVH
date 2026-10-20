with open(r'C:\YostarGames\StellaSora_EN_Gamelauncher\resources\app.asar', 'rb') as f:
    data = f.read()

idx = data.find(b'requestManifestUrl')
if idx != -1:
    print(data[idx:idx+1500].decode('latin1', errors='ignore'))
