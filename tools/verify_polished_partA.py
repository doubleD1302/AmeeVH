import json
import re

with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA.json', 'r', encoding='utf-8') as f:
    src = json.load(f)
with open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/batch_10k_b3_partA_translated.json', 'r', encoding='utf-8') as f:
    dst = json.load(f)

print(f"Total keys: {len(dst)}")
assert len(dst) == 3334

forbidden_checks = [
    ('Cự Thạch', 'cự thạch'),
    ('Liên Hợp Thu Hoạch', 'liên hợp thu hoạch'),
    ('Thu Hoạch Liên Hợp', 'thu hoạch liên hợp'),
    ('Hiệp hội Ngôi sao', 'hiệp hội ngôi sao'),
    ('Dân người Novian', 'dân người novian'),
    ('người Dân người', 'người dân người'),
    ('Nhà máy thông minh', 'nhà máy thông minh'),
    ('xe tăng', 'xe tăng'),
    ('giải nén', 'giải nén'),
    ('bánh mì nướng', 'bánh mì nướng'),
    ('tầng nó', 'tầng nó'),
    ('cắt theo đuổi', 'cắt theo đuổi'),
    ('ở trên đó', 'ở trên đó'),
    ('cái chết được đúc', 'cái chết được đúc'),
    ('làm cứng tôi', 'làm cứng tôi'),
    ('sự quyến rũ đó trên điện thoại', 'sự quyến rũ đó trên điện thoại'),
    ('anh là của em', 'anh là của em'),
    ('phù hợp với chính mình', 'phù hợp với chính mình'),
    ('đã qua đời từ lâu', 'đã qua đời từ lâu'),
]

any_err = False
for name, term in forbidden_checks:
    matches = [k for k, v in dst.items() if term in v.lower()]
    if matches:
        print(f"FAILED: Found {len(matches)} occurrences of '{term}': {matches[:3]}")
        any_err = True

if not any_err:
    print("ALL FORBIDDEN CALQUE CHECKS PASSED: 0 errors found!")

# Token check
token_errs = 0
for k, orig in src.items():
    v = dst[k]
    # Check ==W==
    if len(re.findall(r'==W==', orig)) != len(re.findall(r'==W==', v)):
        print(f"Token error ==W== in {k}")
        token_errs += 1
    # Check ==PLAYER_NAME==
    if len(re.findall(r'==PLAYER_NAME==', orig)) != len(re.findall(r'==PLAYER_NAME==', v)):
        print(f"Token error ==PLAYER_NAME== in {k}")
        token_errs += 1

print(f"Token errors: {token_errs}")
