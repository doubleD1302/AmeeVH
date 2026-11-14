"""Assemble the hand-written Vietnamese for the 2.1.0 'Chờ dịch' dialogue rows into pending_vi.jsonl."""
import collections, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]
DELIVERY = ROOT / "translations/2.1.0/Van_ban_EN_VI.jsonl"
import story_16, story_17_a, story_17_b, story_18_a, story_18_b, story_19

SCENES = {"STm10001_16": [story_16], "STm10001_17": [story_17_a, story_17_b],
          "STm10001_18": [story_18_a, story_18_b], "STm10001_19": [story_19]}
rows = [json.loads(l) for l in DELIVERY.read_text(encoding="utf-8").splitlines() if l.strip()]
def key(r):
    p = r["id"].split(":", 3); m = re.match(r"command/(\d+)/param/(\d+)", p[3])
    return (p[2], int(m.group(1)), int(m.group(2))) if m else (p[2], 10**9, 0)
by = collections.defaultdict(list)
for r in rows:
    if ":lua:" in r["id"]:
        by[r["source"].get("scene")].append(r)
for s in by: by[s].sort(key=key)

TOK = re.compile(r"==[A-Za-z0-9.]+==|<[^<>]+>")
out, problems = [], []
for scene, mods in SCENES.items():
    seq = by[scene]
    vi, copy = {}, set()
    for m in mods:
        vi.update(m.VI); copy.update(m.COPY)
    for i, r in enumerate(seq):
        if r["status"] != "Chờ dịch":
            continue
        en = r["source"]["source_text"]
        if i in copy:
            t = en
        elif scene == "STm10001_19" and i in story_19.ANIM_ROWS:
            t = en
            for a, b in story_19.FRAGMENTS.items():
                t = t.replace(a, b)
        else:
            t = vi.get(i)
        if t is None:
            problems.append(("MISSING", scene, i)); continue
        if collections.Counter(TOK.findall(en)) != collections.Counter(TOK.findall(t)):
            problems.append(("TOKENS", scene, i, en[:70], t[:70]))
        out.append({"id": r["id"], "source": {"source_text": en}, "text_vi": t, "status": "Bản nháp"})
(HERE / "pending_vi.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
print("rows written", len(out), "problems", len(problems))
for p in problems: print(p)
