import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import is_valid_token_preservation, TOKEN_REGEX

trans_path = ROOT / "work" / "batches" / "batch_10k_b3_partC_translated.json"
orig_path = ROOT / "work" / "batches" / "batch_10k_b3_partC.json"

orig = json.load(open(orig_path, encoding='utf-8'))
trans = json.load(open(trans_path, encoding='utf-8'))

# For engine bytecode strings, restore orig verbatim
trans["STm08_13.91"] = orig["STm08_13.91"]

# For ruby tags, preserve exact token structure:
# STm08_16_b.36: tokens are ['==W==', '==W==', '<r=·>special</r>', '<r=·>steel</r>']
trans["STm08_16_b.36"] = "Quyền Trượng Tử Thần được làm bằng thép đặc biệt, đúng vậy... ==W== Khoan đã. ==W== Biết tên là một chuyện, nhưng làm sao bạn biết nó được làm từ <r=·>special</r> <r=·>steel</r>?"

# STm08_16_b.40: tokens are ['==W==', '<r=cloak>skin</r>']
trans["STm08_16_b.40"] = "Bình tĩnh nào. ==W== Sau cuộc trò chuyện của chúng tôi, cô ta trườn đi như một con rắn. Chẳng để lại gì ngoài <r=cloak>skin</r> kinh tởm của ả."

# STm08_17_a.126: tokens are ['cu<r=contradictory></r>te', '==W==']
trans["STm08_17_a.126"] = "Taffett, từ khi nào mà em lại trở nên cu<r=contradictory></r>te như thế hả? ==W=="

# STm08_19_b.199: tokens are ['<r=My... My tongue...>Cough... Cough...</r>', '==W==', '<r=N-No...>Ahh</r>', '==W==', "<r=She won't listen to a word...>ugh</r>"]
trans["STm08_19_b.199"] = "<r=My... My tongue...>Cough... Cough...</r> ==W== <r=N-No...>Ahh</r>... ==W== Hự, <r=She won't listen to a word...>ugh</r>..."

# Now verify all 3333 lines
mismatches = []
for k, o in orig.items():
    t = trans.get(k, "")
    if not is_valid_token_preservation(o, t):
        mismatches.append(k)

print(f"Token preservation mismatches: {len(mismatches)}")
if len(mismatches) == 0:
    print("SUCCESS: 100.0% TOKEN PRESERVATION ACHIEVED (3333/3333)!")
    with open(trans_path, 'w', encoding='utf-8') as f:
        json.dump(trans, f, ensure_ascii=False, indent=2)
    print("Saved clean file.")
