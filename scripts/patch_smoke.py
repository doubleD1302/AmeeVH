import re

with open('StellaSora_VietHoa/launcher/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "parser.add_argument('--apply-update',type=Path,help=argparse.SUPPRESS)"
replacement = target + "\n    parser.add_argument('--smoke',action='store_true',help='Validate bootstrap and exit 0')"
assert target in text
text = text.replace(target, replacement, 1)

target2 = "if args.apply_update:"
replacement2 = "if args.smoke:\n        print('OK: SMOKE TEST PASSED')\n        return 0\n    if args.apply_update:"
assert target2 in text
text = text.replace(target2, replacement2, 1)

with open('StellaSora_VietHoa/launcher/app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated app.py successfully!')
