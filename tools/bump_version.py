with open('launcher/launcher_pc.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"version": "0.4.0"', '"version": "0.7.0"')

with open('launcher/launcher_pc.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated launcher_pc.py to 0.7.0")
