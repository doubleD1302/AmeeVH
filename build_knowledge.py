#!/usr/bin/env python3
"""Dựng thư mục tri thức cho chatbot lore từ các file *_Merge.txt đã Việt hóa.

Chạy offline, chỉ dùng thư viện chuẩn, không đụng vào dữ liệu nguồn.
Mỗi lần chạy dựng lại toàn bộ và chỉ ghi ra đĩa khi nội dung thật sự đổi.

    python build_knowledge.py            # dựng/cập nhật knowledge/
    python build_knowledge.py --check    # chỉ kiểm tra có cũ không (exit 1 nếu cũ)

Nguồn mặc định: ../StellaSoraVietHoaData (đổi bằng --source hoặc SS_SOURCE_ROOT).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import unicodedata
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_VERSION = 1
MAX_CHARS = 1500          # kích thước chunk tối đa (ký tự, không tách một khối)
OVERLAP_LINES = 2         # số dòng gối đầu giữa hai chunk liền nhau
RESOURCE_GLOB = "StellaSora_TaiNguyen_EN_JP_CN_Text_*"

# Thư mục nguồn -> (nhãn category, mô tả). Nhóm chưa liệt kê ở đây (05_Lua, 99_*) bị bỏ qua.
CATEGORIES = {
    "01_CotTruyen": ("story", "Cốt truyện, sự kiện, ngoại truyện"),
    "02_NhanVat": ("character", "Hồ sơ, giọng và dữ liệu nhân vật"),
    "03_BangText_UI_KyNang": ("game_text", "Vật phẩm, kỹ năng, nhiệm vụ, giao diện"),
    "04_PhuDeVideo": ("subtitle", "Phụ đề video"),
    "90_CN_Moi_2.0.1": ("extra", "Nhóm khóa bổ sung 2.0.1"),
}
GLOSSARY_KEEP = {
    "term": "Thuật ngữ",
    "character_name": "Tên nhân vật và tên riêng",
    "ui_text": "Chữ giao diện",
}

HEADER = re.compile(r"^([1-9]\d*)\. \[(.*)\](?: \(([^\n]+)\))?\n", re.M)
TAG = re.compile(r"</?[A-Za-z][^>\n]*>")
RT = re.compile(r"(?:==RT==)+")
MARK = re.compile(r"==[A-Za-z_0-9.-]+==")
SPEAKER_TITLE_KINDS = ("Tên hồi", "Tiêu đề", "Tóm tắt")
SKIP_TEXT = {"", "[EMPTY_SOURCE]"}


# --------------------------------------------------------------------------- helpers
def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean(text: str, cjk: bool = False) -> str:
    """Bỏ thẻ định dạng (<size>, <r=...>, <color>...), đổi ==RT== thành xuống dòng."""
    def rt(m):
        return "\n\n" if m.group(0).count("==RT==") >= 2 else ("" if cjk else " ")
    text = RT.sub(rt, text)
    text = text.replace("==PLAYER_NAME==", "[tên người chơi]")
    text = re.sub(r"==SEX\d*==", "[giới tính]", text)
    text = MARK.sub("", text)              # ==W== (chờ), ==P==, ==Off== ... là mã hiệu ứng chữ
    text = TAG.sub("", text)
    text = text.replace("　", " ")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def group_of(parts: tuple[str, ...]) -> str:
    """parts: đường dẫn tương đối trong thư mục tài nguyên, đã bỏ tên file."""
    top = parts[0]
    if top == "01_CotTruyen" and len(parts) >= 3:
        return parts[2] if parts[1] in ("01_Chinh", "02_SuKien") and len(parts) >= 4 else parts[1]
    if top in ("02_NhanVat",) and len(parts) >= 2:
        return parts[1]
    return top


def find_resource(source: Path, name: str | None) -> Path:
    if name:
        path = source / name
        if not path.is_dir():
            raise SystemExit(f"Không thấy thư mục tài nguyên: {path}")
        return path
    found = sorted(p for p in source.glob(RESOURCE_GLOB) if p.is_dir())
    if not found:
        raise SystemExit(f"Không tìm thấy {RESOURCE_GLOB} trong {source}")
    return found[-1]


# --------------------------------------------------------------------------- parsing
def parse_merge(data: bytes):
    """Trả về (blocks, warnings). Mỗi block: dict kind/label/lines(4 hoặc 3)/vi?"""
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    ms = list(HEADER.finditer(text))
    if not ms or ms[0].start() != 0:
        raise ValueError("Không có khối đánh số ở đầu file")
    out, warnings = [], []
    for i, m in enumerate(ms):
        if int(m[1]) != i + 1:
            raise ValueError(f"Số khối không liên tục tại {m[1]}")
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        lines = text[m.end():end].rstrip("\n").split("\n")
        label, kind = m[2], m[3] or ""
        n = len(lines)
        if n == 4:
            cn, jp, en, vi = lines
        elif n == 3:
            cn, jp, en = lines
            vi = None                      # đã merge nhưng chưa dịch
        elif n % 4 == 0:                   # nhiều dòng mỗi ngôn ngữ: chia đều (có cảnh báo)
            k = n // 4
            cn, jp, en, vi = ("\n".join(lines[j * k:(j + 1) * k]) for j in range(4))
            warnings.append(f"khối {i + 1}: nhiều dòng, chia đều {k} dòng/ngôn ngữ")
        else:
            warnings.append(f"khối {i + 1}: {n} dòng không chia được, bỏ qua")
            continue
        out.append({"order": i + 1, "kind": kind, "label": label,
                    "cn": cn, "jp": jp, "en": en, "vi": vi})
    return out, warnings


def split_speakers(block):
    """Story: nhãn 4 phần = VI/ EN/ JP/ CN; 1 phần = chỉ nhãn VI; 3 phần = EN/ JP/ CN (chưa dịch)."""
    parts = [p.strip() for p in block["label"].split("/ ")]
    if len(parts) == 4:
        vi, en, jp, cn = parts
    elif len(parts) == 1:
        vi, en, jp, cn = parts[0], "", "", ""
    else:
        vi, (en, jp, cn) = "", (parts + ["", "", ""])[:3]
    blank = lambda s: "" if s in ("—", "") else s
    return blank(vi), blank(en), blank(jp), blank(cn)


def static_code(label: str) -> str:
    m = re.fullmatch(r"EN: (.+?)/JP: .+?/CN: .+", label)
    return m[1] if m else label


# --------------------------------------------------------------------------- rendering
def block_line(rec) -> str:
    text, kind, spk = rec["text_vi"], rec["kind"], rec["speaker_vi"]
    if not kind:                                   # UI tĩnh
        return f"{rec['code']}: {text}"
    if kind == "Lời dẫn" or spk == "Dẫn chuyện":
        return f"[Dẫn chuyện] {text}"
    if kind in ("Lời thoại", "Tin nhắn") and spk:
        return f"{spk}: {text}" if kind == "Lời thoại" else f"{spk} (tin nhắn): {text}"
    if kind == "Độc thoại" and spk:
        return f"{spk} (độc thoại): {text}"
    if kind == "Lựa chọn":
        return f"[Lựa chọn] {text}" if not spk else f"{spk} (lựa chọn): {text}"
    if spk:
        return f"{spk} ({kind.lower()}): {text}"
    return f"[{kind}] {text}"


def chunk_lines(items, prefix):
    """items: [(line, order, speaker)] -> [(text, first, last, speakers)]"""
    chunks, cur, size, fresh = [], [], 0, 0

    def emit():
        body = "\n".join(x[0] for x in cur)
        spk = sorted({x[2] for x in cur if x[2]})
        chunks.append((f"{prefix}\n{body}", cur[0][1], cur[-1][1], spk))

    for it in items:
        add = len(it[0]) + 1
        if cur and size + add > MAX_CHARS:
            emit()
            tail = cur[-OVERLAP_LINES:] if OVERLAP_LINES else []
            if sum(len(x[0]) + 1 for x in tail) > MAX_CHARS // 3:
                tail = []
            cur[:] = tail
            size = sum(len(x[0]) + 1 for x in cur)
            fresh = 0
        cur.append(it)
        size += add
        fresh += 1
    if fresh:                       # không phát chunk chỉ gồm phần gối đầu
        emit()
    return chunks


def doc_path_for(rel_parts: tuple[str, ...], fid: str) -> str:
    parts = list(rel_parts)
    if parts and parts[-1] == fid:
        parts.pop()
    return "/".join(parts + [fid])


def render_doc(meta, title_bits, speakers, lines, status):
    fm = ["---"] + [f"{k}: {v}" for k, v in meta.items()] + [f"status: {status}", "---", ""]
    head = [f"# {title_bits['title']}", ""]
    if title_bits.get("summary"):
        head += [f"**Tóm tắt:** {title_bits['summary']}", ""]
    if speakers:
        head += ["**Nhân vật/người nói xuất hiện:** " + ", ".join(speakers), ""]
    head += ["## Nội dung", ""]
    return "\n".join(fm + head + lines) + "\n"


def assemble(doc_id, category, grp, fid, rel, digest, recs, total, story, title_bits,
             speakers_seen, origin, title_hint=None):
    """Dựng tài liệu markdown + chunk từ danh sách khối đã chuẩn hóa. Dùng chung cho mọi nguồn."""
    if not recs:
        return None, [], [], {"doc_id": doc_id, "blocks_total": total}
    status = "translated" if len(recs) == total else "partial"
    for r in recs:
        r["origin"] = origin
    if story:
        parts = [title_bits.get("Tên hồi"), title_bits.get("Tiêu đề")]
        title = " — ".join(p for p in parts if p) or fid
        title = f"{fid}: {title}" if fid not in title else title
    else:
        title = title_hint or f"{fid} (bảng văn bản)"
    summary = title_bits.get("Tóm tắt", "")
    speakers = [f"{v} ({e})" if e else v for v, e in sorted(speakers_seen.items())]

    body_recs = [r for r in recs if r["kind"] not in SPEAKER_TITLE_KINDS]
    body_lines = [block_line(r) for r in body_recs]
    meta = {"doc_id": doc_id, "category": category, "group": grp, "file_id": fid, "origin": origin,
            "source": rel, "source_sha256": digest, "blocks": len(recs)}
    doc = render_doc(meta, {"title": title, "summary": summary}, speakers, body_lines, status)

    prefix = f"[{category} | {grp} | {title}]"
    items = [(block_line(r), r["order"], r["speaker_vi"]) for r in body_recs]
    if summary:
        items.insert(0, (f"Tóm tắt: {summary}", recs[0]["order"], ""))
    chunk_rows = []
    for n, (text, first, last, spk) in enumerate(chunk_lines(items, prefix), 1):
        chunk_rows.append({"id": f"{doc_id}#{n:03d}", "doc_id": doc_id, "category": category,
                           "group": grp, "file_id": fid, "origin": origin, "title": title,
                           "block_start": first, "block_end": last, "speakers": spk,
                           "chars": len(text), "source": rel, "text": text})
    info = {"doc_id": doc_id, "category": category, "group": grp, "origin": origin, "source": rel,
            "source_sha256": digest, "status": status, "blocks_total": total,
            "blocks_included": len(recs), "chunks": len(chunk_rows)}
    return doc, recs, chunk_rows, info


def build_file(rel_posix: str, key_parts, data: bytes, category: str):
    """Trả về (doc_text, recs, chunk_rows, info, warnings); doc_text None nếu chưa có khối VI."""
    blocks, warns = parse_merge(data)
    fid = Path(rel_posix).name.removesuffix("_Merge.txt")
    rel_parts = tuple(Path(rel_posix).parts[:-1])
    grp = group_of(rel_parts)
    doc_id = doc_path_for(rel_parts, fid)
    story = any(b["kind"] for b in blocks)

    recs, title_bits, speakers_seen = [], {}, {}
    for b in blocks:
        if b["vi"] is None or clean(b["vi"]) in SKIP_TEXT:
            continue
        spk = split_speakers(b) if b["kind"] else ("", "", "", "")
        rec = {"doc_id": doc_id, "order": b["order"], "kind": b["kind"],
               "speaker_vi": spk[0], "speaker_en": spk[1], "speaker_jp": spk[2], "speaker_cn": spk[3],
               "code": static_code(b["label"]) if not b["kind"] else "",
               "text_vi": clean(b["vi"]), "text_en": clean(b["en"]),
               "text_jp": clean(b["jp"], True), "text_cn": clean(b["cn"], True)}
        recs.append(rec)
        if b["kind"] in SPEAKER_TITLE_KINDS:
            title_bits[b["kind"]] = rec["text_vi"]
        if spk[0] and spk[0] not in ("Dẫn chuyện", "Người chơi") and b["kind"] in (
                "Lời thoại", "Độc thoại", "Tin nhắn"):
            en = spk[1] if spk[1] and spk[1] != spk[0] else ""
            speakers_seen[spk[0]] = en

    return assemble(doc_id=doc_id, category=category, grp=grp, fid=fid, rel=rel_posix,
                    digest=sha(data), recs=recs, total=len(blocks), story=story,
                    title_bits=title_bits, speakers_seen=speakers_seen, origin="merge") + (warns,)


def build_glossary(path: Path):
    if not path.exists():
        return None, [], {"entries": 0}
    raw = path.read_bytes()
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    by_cat: dict[str, list] = {}
    seen = set()
    for r in rows:
        cat, en, vi = r.get("category", ""), clean(r.get("EN") or ""), clean(r.get("target") or "")
        if cat not in GLOSSARY_KEEP or en in SKIP_TEXT or vi in SKIP_TEXT:
            continue
        key = (cat, en, vi)
        if key in seen:
            continue
        seen.add(key)
        by_cat.setdefault(cat, []).append((en, vi, clean(r.get("JP") or "", True), clean(r.get("CN") or "", True)))
    md = ["# Bảng thuật ngữ EN → VI", "",
          "Nguồn: glossary/glossary.csv của dự án Việt hóa. Dùng để giữ đúng tên riêng và thuật ngữ.", ""]
    chunks = []
    for cat, label in GLOSSARY_KEEP.items():
        entries = sorted(by_cat.get(cat, []), key=lambda x: x[0].lower())
        if not entries:
            continue
        md += [f"## {label} ({len(entries)})", "", "| EN | VI | JP | CN |", "|---|---|---|---|"]
        lines = []
        for en, vi, jp, cn in entries:
            esc = lambda s: s.replace("|", "\\|")
            md.append(f"| {esc(en)} | {esc(vi)} | {esc(jp)} | {esc(cn)} |")
            extra = "; ".join(x for x in (f"JP: {jp}" if jp else "", f"CN: {cn}" if cn else "") if x)
            lines.append((f"{en} = {vi}" + (f" ({extra})" if extra else ""), 0, ""))
        md.append("")
        for n, (text, _, _, _) in enumerate(chunk_lines(lines, f"[glossary | {label}]"), 1):
            chunks.append({"id": f"glossary/{cat}#{n:03d}", "doc_id": f"glossary/{cat}",
                           "category": "glossary", "group": cat, "file_id": cat,
                           "title": f"Bảng thuật ngữ — {label}", "block_start": 0, "block_end": 0,
                           "speakers": [], "chars": len(text), "source": "glossary/glossary.csv",
                           "text": text})
    return "\n".join(md) + "\n", chunks, {"entries": sum(len(v) for v in by_cat.values()), "sha256": sha(raw)}


# --------------------------------------------------------------------------- nguồn patch (AmeeVH)
PATCH_STORY_CATS = {"Chương đặc biệt", "Truyện sự kiện", "Ngoại truyện / Nova Times", "Truyện đĩa nhạc",
                    "Truyện & mô tả chương", "Truyện chính & chiến đấu"}
SETINTRO_KIND = {"1": "Tên hồi", "2": "Tiêu đề", "3": "Tóm tắt"}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_") or "x"


def cat_label(category: str) -> str:
    if category in PATCH_STORY_CATS:
        return "story"
    if category.startswith("Nhân vật") or category in ("Danh bạ", "Tên người nói"):
        return "character"
    return "game_text"


def load_glossary_map(path: Path) -> dict:
    out: dict[str, str] = {}
    if path.exists():
        for r in csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8-sig"), newline="")):
            en, vi = clean(r.get("EN") or ""), clean(r.get("target") or "")
            if r.get("category") in ("character_name", "term") and en not in SKIP_TEXT and vi:
                out.setdefault(en.lower(), vi)
    return out


def read_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def patch_group(scene: str, fallback: str) -> str:
    m = re.fullmatch(r"(.+?)_\d+[A-Za-z]?", scene or "")
    return m[1] if m else (scene or fallback)


_SCENE_CACHE: dict = {}


def scene_speaker(patch_root: Path, ver: str, entry_hash: str, locator: str, source_text: str) -> str:
    """Id người nói (param[1] của SetTalk) lấy từ bản trích scene JSON; chỉ nhận khi câu thoại khớp nguồn."""
    m = re.fullmatch(r"command/(\d+)/param/(\d+)", locator or "")
    if not (m and entry_hash):
        return ""
    key = (ver, entry_hash)
    if key not in _SCENE_CACHE:
        pref = "text_202" if ver == "2.0.2" else "text"
        found = sorted((patch_root / "work" / "runs").glob(f"update_*/{pref}/scenes/*__{entry_hash}.json"))
        try:
            _SCENE_CACHE[key] = json.loads(found[-1].read_text(encoding="utf-8-sig")).get("commands", []) if found else []
        except (OSError, ValueError):
            _SCENE_CACHE[key] = []
    cmds, i, pi = _SCENE_CACHE[key], int(m[1]), int(m[2])
    if i >= len(cmds) or cmds[i].get("cmd") != "SetTalk":
        return ""
    param = cmds[i].get("param") or []
    if len(param) <= max(1, pi) or param[pi] != source_text or param[1] in (None, ""):
        return ""
    return str(param[1])


def build_patch(patch_root: Path, gmap: dict, skip: set = frozenset()):
    """Gom bản Việt hóa trong dự án patch: delivery/<ver>/Van_ban_EN_VI.jsonl + lớp hotfix_*."""
    runs = patch_root / "work" / "runs"
    deliveries = sorted(runs.glob("localize_*/delivery/*/Van_ban_EN_VI.jsonl")) if runs.is_dir() else []
    if not deliveries:
        return [], [], [], {}, ["Không thấy delivery/*/Van_ban_EN_VI.jsonl trong dự án patch — bỏ qua nguồn patch"]
    rels = lambda p: p.relative_to(patch_root).as_posix()
    overlay, overlay_files = {}, []
    for f in sorted((patch_root / "work").glob("hotfix_*/*.jsonl")):
        for r in read_jsonl(f):
            if r.get("id") and clean(r.get("text_vi") or ""):
                overlay[r["id"]] = r
        overlay_files.append({"path": rels(f), "sha256": sha(f.read_bytes())})

    by_version: dict[str, dict] = {}
    sources = []
    for f in deliveries:
        ver = f.parent.name
        names = {}
        nf = f.parents[2] / f"{ver.replace('.', '')}_AvgCharacter.json"
        if nf.exists():
            for rec in json.loads(nf.read_text(encoding="utf-8-sig")).get("records", []):
                if rec.get("name"):
                    names[str(rec["id"])] = rec["name"]
        sources.append({"path": rels(f), "sha256": sha(f.read_bytes())})
        for r in read_jsonl(f):
            r["_names"] = names
            by_version.setdefault(ver, {})[r["id"]] = r

    docs, warnings, used = {}, [], set()
    for ver, rows in by_version.items():
        for rid, r in rows.items():
            ov = overlay.get(rid)
            if ov:
                r["text_vi"], used = ov["text_vi"], used | {rid}
            s = r.get("source") or {}
            category = s.get("category") or "Khác"
            scene = s.get("scene") or ""
            lua = ":lua:" in rid
            label = cat_label(category)
            if lua and scene:
                key, grp = scene, patch_group(scene, slug(category))
            elif not lua:
                pointer = rid.split(":", 3)[-1]
                key = re.match(r"/?([^./]+)", pointer)[1]
                grp = slug(category)
            else:
                key, grp = slug(category), slug(category)
            d = docs.setdefault((ver, label, key), {"category": category, "grp": grp, "rows": [], "story": lua and bool(scene)})
            d["rows"].append(r)
    orphans = [rid for rid in overlay if not any(rid in rows for rows in by_version.values())]
    if orphans:
        warnings.append(f"hotfix: {len(orphans)} dòng không có trong delivery nên không nạp")

    out_docs, out_recs, out_chunks, infos, cov = [], [], [], [], {}
    for (ver, label, key), d in sorted(docs.items()):
        if key in skip:
            continue
        doc_id = f"patch_{ver}/{label}/{key}"
        recs, title_bits, speakers_seen, total, keep_en = [], {}, {}, len(d["rows"]), 0
        for r in d["rows"]:
            s, text = r.get("source") or {}, clean(r.get("text_vi") or "")
            if r.get("status") == "Giữ EN" or text in SKIP_TEXT:
                keep_en += r.get("status") == "Giữ EN"
                continue
            cmd, loc = s.get("command") or "", s.get("locator") or ""
            p = (re.search(r"param/(\d+)", loc) or [None, ""])[1]
            kind, code, spk_vi, spk_en = "", "", "", ""
            if d["story"]:
                kind = (SETINTRO_KIND.get(p, "Lời dẫn") if cmd == "SetIntro" else
                        "Lời thoại" if cmd in ("SetTalk", "SetBubble") else
                        "Tin nhắn" if cmd == "SetPhoneMsg" else
                        "Tiêu đề cảnh" if cmd == "SetSceneHeading" else
                        "Lựa chọn" if "Choice" in cmd else (cmd or "Văn bản"))
                token = (s.get("actor_voice") or "").split("|")[0].strip()
                if not token and cmd == "SetTalk":
                    token = scene_speaker(patch_root, ver, s.get("entry_hash") or "", loc, s.get("source_text") or "")
                if token == "1":
                    spk_vi = "Người chơi"
                elif token == "0":
                    kind, spk_vi = "Lời dẫn", "Dẫn chuyện"
                elif token:   # mã nhân vật (avg1_133) tra bảng tên; không thì chính là tên hiển thị EN
                    spk_en = r["_names"].get(token) or ("" if re.fullmatch(r"avg\d*_\w+", token) else token)
                    if spk_en:
                        spk_vi = gmap.get(spk_en.lower(), spk_en)
                if kind == "Lời thoại" and not spk_vi:
                    kind = "Thoại"
            else:
                code = r["id"].split(":", 3)[-1].lstrip("/")
            en = clean(s.get("source_text") or "")
            vi_line = text if d["story"] or not en or en == text else f"{text} (EN: {en})"
            rec = {"doc_id": doc_id, "order": len(recs) + 1, "kind": kind, "speaker_vi": spk_vi,
                   "speaker_en": spk_en, "speaker_jp": "", "speaker_cn": "", "code": code,
                   "text_vi": vi_line, "text_en": en, "text_jp": "", "text_cn": ""}
            recs.append(rec)
            if kind in SPEAKER_TITLE_KINDS:
                title_bits[kind] = text
            if spk_vi and spk_vi not in ("Dẫn chuyện", "Người chơi") and kind in ("Lời thoại", "Tin nhắn"):
                speakers_seen[spk_vi] = spk_en if spk_en and spk_en != spk_vi else ""
        c = cov.setdefault((ver, d["category"]), {"docs": 0, "rows": 0, "vi": 0, "keep_en": 0, "missing": 0, "missing_docs": []})
        c["docs"] += 1
        c["rows"] += total
        c["vi"] += len(recs)
        c["keep_en"] += keep_en
        c["missing"] += total - len(recs) - keep_en
        if total - len(recs) - keep_en:
            c["missing_docs"].append(f"{key} ({total - len(recs) - keep_en}/{total})")
        digest = sha(json.dumps([(r["id"], r.get("source_sha256"), r.get("text_vi")) for r in d["rows"]],
                                ensure_ascii=False).encode("utf-8"))
        rel = f"patch:{ver}/{label}/{key}"
        title_hint = f"{key} — {d['category']}"
        doc, rr, chunks, info = assemble(doc_id=doc_id, category=label, grp=d["grp"], fid=key, rel=rel,
                                         digest=digest, recs=recs, total=total - keep_en, story=d["story"],
                                         title_bits=title_bits, speakers_seen=speakers_seen,
                                         origin=f"patch_{ver}", title_hint=title_hint)
        if doc is None:
            continue
        out_docs.append((f"docs/{doc_id}.md", doc.encode("utf-8")))
        out_recs += rr
        out_chunks += chunks
        infos.append(info)
    meta = {"sources": sources, "hotfix_files": overlay_files, "overlay_rows_used": len(used),
            "coverage": {f"{v} | {c}": {k: x for k, x in val.items() if k != "missing_docs"} for (v, c), val in sorted(cov.items())},
            "missing_docs": {f"{v} | {c}": val["missing_docs"] for (v, c), val in sorted(cov.items()) if val["missing_docs"]}}
    return out_docs, out_recs, out_chunks, {"infos": infos, "meta": meta}, warnings


# --------------------------------------------------------------------------- nguồn gói arcx đang chạy trong game
CACHE_DIR = HERE / ".cache" / "patched_vi"
VI_CHARS = re.compile(r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", re.I)
AVG_ID = re.compile(r"avg\d*_\w+")
MIN_VI_SHARE = 0.2        # cảnh có dưới 20% dòng thoại mang dấu tiếng Việt coi như chưa dịch


def ensure_patched_cache(patch_root: Path):
    """Giải nén text từ dist/*_patched_vi.arcx bằng Node (chỉ chạy lại khi gói đổi). Trả (thư mục, meta, cảnh báo)."""
    arcs = [patch_root / "dist" / n for n in ("lua_patched_vi.arcx", "data_patched_vi.arcx")]
    arcs = [a for a in arcs if a.exists()]
    if not arcs:
        return None, {}, ["Không thấy dist/*_patched_vi.arcx — bỏ qua nguồn gói arcx"]
    hashes = {a.name: sha(a.read_bytes()) for a in arcs}
    stamp = CACHE_DIR / "stamp.json"
    try:
        fresh = json.loads(stamp.read_text(encoding="utf-8")) == hashes and (CACHE_DIR / "scenes.jsonl").exists()
    except (OSError, ValueError):
        fresh = False
    if not fresh:
        node = shutil.which("node")
        if not node:
            return None, {}, ["Không có Node.js trong PATH nên không đọc được gói arcx — bỏ qua nguồn này"]
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True)
        run = subprocess.run([node, str(HERE / "tools" / "extract_patched_vi.cjs"), str(patch_root), str(CACHE_DIR)],
                             capture_output=True, text=True)
        if run.returncode != 0:
            shutil.rmtree(CACHE_DIR, ignore_errors=True)
            return None, {}, [f"Trích gói arcx thất bại: {run.stderr.strip()[:200]}"]
        stamp.write_text(json.dumps(hashes), encoding="utf-8")
    meta = json.loads((CACHE_DIR / "meta.json").read_text(encoding="utf-8"))
    return CACHE_DIR, meta, []


def has_vi(text) -> bool:
    return isinstance(text, str) and bool(VI_CHARS.search(text))


def flatten_strings(value, path=""):
    """Duyệt giá trị lồng (dict/list) lấy các chuỗi kèm đường dẫn."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from flatten_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from flatten_strings(v, f"{path}[{i}]")


def scene_records(scene, names, gmap):
    """Chuyển lệnh trong cảnh thành khối. Trả (recs, title_bits, speakers_seen, số_dòng_thoại, số_dòng_có_dấu_VI)."""
    recs, title_bits, speakers_seen, talk, talk_vi = [], {}, {}, 0, 0

    def add(kind, text, spk_vi="", spk_en="", code=""):
        text = clean(text) if isinstance(text, str) else ""
        if text in SKIP_TEXT:
            return
        recs.append({"order": len(recs) + 1, "kind": kind, "speaker_vi": spk_vi, "speaker_en": spk_en,
                     "speaker_jp": "", "speaker_cn": "", "code": code, "text_vi": text, "text_en": "",
                     "text_jp": "", "text_cn": ""})
        if kind in SPEAKER_TITLE_KINDS:
            title_bits[kind] = text
        if spk_vi and spk_vi not in ("Dẫn chuyện", "Người chơi") and kind in ("Lời thoại", "Tin nhắn"):
            speakers_seen[spk_vi] = spk_en if spk_en and spk_en != spk_vi else ""

    def speaker(token, override):
        token = str(token or "").strip()
        if token == "0":
            return "Dẫn chuyện", ""
        if token == "1":
            return "Người chơi", ""
        en = names.get(token) or ("" if AVG_ID.fullmatch(token) else token)
        vi = clean(override) if isinstance(override, str) and clean(override) else (gmap.get(en.lower(), en) if en else "")
        return vi, en

    def get(p, i):
        return p[i] if isinstance(p, list) and len(p) > i else None

    for _idx, cmd, p in scene["commands"]:
        if cmd == "SetIntro":
            for i, kind in ((1, "Tên hồi"), (2, "Tiêu đề"), (3, "Tóm tắt")):
                add(kind, get(p, i))
        elif cmd in ("SetTalk", "SetBubble", "SetPhoneMsg"):
            ti, si = (8, 0) if cmd == "SetBubble" else (7, 1)
            text = get(p, ti)
            if not isinstance(text, str) or clean(text) in SKIP_TEXT:
                continue
            vi, en = speaker(get(p, si), get(p, 6) if cmd != "SetPhoneMsg" else None)
            if vi == "Dẫn chuyện":
                kind = "Lời dẫn"
            else:
                kind = "Tin nhắn" if cmd == "SetPhoneMsg" else "Lời thoại"
            talk += 1
            talk_vi += has_vi(text)
            add(kind, text, vi, en)
        elif cmd == "SetSceneHeading":
            parts = [clean(x) for x in (p or [])[:5] if isinstance(x, str) and clean(x)]
            add("Tiêu đề cảnh", " · ".join(parts))
        elif cmd == "SetChoiceBegin":
            for lst in (get(p, 12), get(p, 3)):
                items = [x for x in (lst or []) if isinstance(x, str) and x.strip()] if isinstance(lst, list) else []
                if items:
                    for x in dict.fromkeys(items):
                        add("Lựa chọn", x)
                    break
        elif cmd == "SetPhoneMsgChoiceBegin":
            for i in (1, 2):
                add("Lựa chọn", get(p, i))
        elif cmd == "SetPersonalityChoice":
            for i in (2, 3, 4, 8):
                add("Lựa chọn", get(p, i))
        elif cmd == "SetTrans" and has_vi(get(p, 8)):
            add("Chữ chuyển cảnh", get(p, 8))
    return recs, title_bits, speakers_seen, talk, talk_vi


TABLE_KEY = re.compile(r"(.+)\.([^.]+)\.(\d+)")


def group_table_rows(rows):
    """Gộp các cột của cùng một bản ghi (Item.1.1, Item.1.2 ...) thành một dòng để chunk có đủ ngữ cảnh."""
    grouped: dict[str, list] = {}
    for code, text in rows:
        m = TABLE_KEY.fullmatch(code)
        grouped.setdefault(f"{m[1]}.{m[2]}" if m else code, []).append(text)
    return [(k, " | ".join(dict.fromkeys(v))) for k, v in grouped.items()]


def build_arcx(patch_root: Path, gmap: dict, skip: set):
    """Văn bản tiếng Việt đang dùng trong game: cảnh AVG (lua) và bảng text (data) từ dist/*_patched_vi.arcx."""
    cache, meta, warnings = ensure_patched_cache(patch_root)
    empty = ([], [], [], {"infos": [], "meta": {}, "covered": set()}, warnings)
    if cache is None:
        return empty
    presets = json.loads((cache / "presets.json").read_text(encoding="utf-8")) if (cache / "presets.json").exists() else {}
    recs_by_id = {str(r.get("id")): r for r in presets.get("AvgCharacter", [])}
    names = {}
    for rid, r in recs_by_id.items():
        nm = r.get("name") or (recs_by_id.get(str(r.get("reuse")), {}) or {}).get("name") or ""
        if nm:
            names[rid] = nm
    out_docs, out_recs, out_chunks, infos, covered = [], [], [], [], set()
    stats = {"scenes_total": 0, "scenes_included": 0, "scenes_untranslated": [], "scenes_skipped_merge": 0,
             "tables_included": 0, "table_strings": 0}

    def emit(doc_id, label, grp, key, recs, title_bits, speakers_seen, story, title_hint, digest_parts):
        digest = sha(json.dumps(digest_parts, ensure_ascii=False).encode("utf-8"))
        doc, rr, chunks, info = assemble(doc_id=doc_id, category=label, grp=grp, fid=key, rel=f"patch:arcx/{label}/{key}",
                                         digest=digest, recs=recs, total=len(recs), story=story, title_bits=title_bits,
                                         speakers_seen=speakers_seen, origin="patch_game", title_hint=title_hint)
        for r in rr:
            r["doc_id"] = doc_id
        if doc is None:
            return False
        out_docs.append((f"docs/{doc_id}.md", doc.encode("utf-8")))
        out_recs.extend(rr)
        out_chunks.extend(chunks)
        infos.append(info)
        covered.add(key)
        return True

    scenes = {}
    for line in (cache / "scenes.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line)
            scenes[s["scene"]] = s
    for name, scene in sorted(scenes.items()):
        stats["scenes_total"] += 1
        if name in skip:
            stats["scenes_skipped_merge"] += 1
            continue
        recs, tb, spk, talk, talk_vi = scene_records(scene, names, gmap)
        if not recs:
            continue
        if talk >= 5 and talk_vi / talk < MIN_VI_SHARE:
            stats["scenes_untranslated"].append(name)
            continue
        label = "character" if re.match(r"(CG|DP|PM)", name) else "story"
        grp = patch_group(name, "scene")
        for r in recs:
            r["doc_id"] = f"patch/{label}/{name}"
        if emit(f"patch/{label}/{name}", label, grp, name, recs, tb, spk, True, None,
                [(r["kind"], r["speaker_vi"], r["text_vi"]) for r in recs]):
            stats["scenes_included"] += 1

    # danh bạ nhân vật
    contacts = []
    for r in presets.get("AvgContacts", []):
        for field, label_vi in (("landmark", "địa điểm"), ("signature", "chữ ký")):
            if has_vi(r.get(field)):
                contacts.append(f"{clean(str(r.get('name')))} ({label_vi}): {clean(r[field])}")
    if contacts and "AvgContacts" not in skip:
        recs = [{"order": i + 1, "kind": "Danh bạ", "speaker_vi": "", "speaker_en": "", "speaker_jp": "", "speaker_cn": "",
                 "code": "", "text_vi": t, "text_en": "", "text_jp": "", "text_cn": ""} for i, t in enumerate(contacts)]
        emit("patch/character/AvgContacts", "character", "AvgContacts", "AvgContacts", recs, {}, {}, False,
             "Danh bạ nhân vật (địa điểm, chữ ký)", contacts)

    tables: dict[str, list] = {}
    for line in (cache / "tables.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        t = json.loads(line)
        first = next(iter(t["data"]), "")
        name = t["name"] or ("VoiceText" if str(first).startswith("vo_") else f"Table_{t['hash'][2:10]}")
        rows = []
        for key, value in t["data"].items():
            seen = set()
            for path, text in flatten_strings(value):
                if has_vi(text) and text not in seen:
                    seen.add(text)
                    code = key if not path or path == "text" else f"{key}.{path}"
                    rows.append((code, clean(text)))
        if rows:
            tables.setdefault(name, []).extend(rows)
    for name, rows in sorted(tables.items()):
        if name in skip:
            continue
        rows = group_table_rows(rows)
        label = "character" if name == "VoiceText" else "game_text"
        recs = [{"order": i + 1, "kind": "", "speaker_vi": "", "speaker_en": "", "speaker_jp": "", "speaker_cn": "",
                 "code": c, "text_vi": x, "text_en": "", "text_jp": "", "text_cn": ""} for i, (c, x) in enumerate(rows) if x]
        if emit(f"patch/{label}/{name}", label, "tables", name, recs, {}, {}, False, f"{name} (bảng văn bản trong game)",
                rows):
            stats["tables_included"] += 1
            stats["table_strings"] += len(recs)
    meta_out = {"archives": meta.get("archives", {}), **{k: v for k, v in stats.items() if k != "scenes_untranslated"},
                "scenes_untranslated": sorted(stats["scenes_untranslated"])}
    return out_docs, out_recs, out_chunks, {"infos": infos, "meta": meta_out, "covered": covered}, warnings


# --------------------------------------------------------------------------- coverage
def coverage(res: Path, translated: set[str], pending: set[str], partial: set[str]):
    """Đếm đơn vị nguồn (mỗi *_EN.txt = một đơn vị) theo category và nhóm."""
    cats, groups = {}, {}
    for top, (label, _desc) in CATEGORIES.items():
        base = res / top
        if not base.is_dir():
            continue
        for en in base.rglob("*_EN.txt"):
            rel = en.relative_to(res).as_posix()
            merge = rel.removesuffix("_EN.txt") + "_Merge.txt"
            state = ("translated" if merge in translated else "partial" if merge in partial
                     else "pending" if merge in pending else
                     "merged_only" if (res / merge).exists() else "unmerged")
            g = group_of(tuple(Path(rel).parts[:-1]))
            for bucket, k in ((cats, top), (groups, (top, g))):
                bucket.setdefault(k, dict.fromkeys(("translated", "partial", "pending", "merged_only", "unmerged"), 0))[state] += 1
    return cats, groups


def status_md(cats, groups, infos, warnings, glossary_info, untranslated, errors, patch_meta=None, arcx_meta=None):
    def row(label, c):
        total = sum(c.values())
        done = c["translated"] + c["partial"]
        pct = f"{100 * done / total:.1f}%" if total else "—"
        return f"| {label} | {total} | {c['translated']} | {c['partial']} | {c['pending'] + c['merged_only']} | {c['unmerged']} | {pct} |"

    head = "| Nhóm | Đơn vị nguồn | Đã dịch | Dịch dở | Merge chưa dịch | Chưa merge | Phủ |\n|---|--:|--:|--:|--:|--:|--:|"
    out = ["# Trạng thái tri thức chatbot", "",
           "File này do `build_knowledge.py` tự sinh, đừng sửa tay. Chatbot chỉ có tri thức về phần **đã Việt hóa**; "
           "phần còn lại cần nói rõ là chưa có dữ liệu.", "",
           f"- Tài liệu (docs): **{len(infos)}**, khối: **{sum(i['blocks_included'] for i in infos)}**, "
           f"chunk: **{sum(i['chunks'] for i in infos)}** (chưa tính thuật ngữ)",
           f"- Thuật ngữ nạp vào: **{glossary_info.get('entries', 0)}** mục",
           "", "## Độ phủ luồng Merge (bản dịch đã review)", "",
           "Chỉ tính các file Merge trong dự án Việt hóa SS; phần bản Việt hóa đang chạy trong game (gói arcx) xem các mục bên dưới.", "", head]
    for top, (label, desc) in CATEGORIES.items():
        if top in cats:
            out.append(row(f"`{top}` — {desc}", cats[top]))
    out += ["", "## Độ phủ luồng Merge theo nhóm (chỉ nhóm đã có Merge)", "", head]
    for (top, g), c in sorted(groups.items()):
        if c["translated"] or c["partial"] or c["pending"] or c["merged_only"]:
            out.append(row(f"`{top}` / `{g}`", c))
    if arcx_meta:
        arcs = ", ".join(f"`{n}` ({a['entries']} mục)" for n, a in arcx_meta.get("archives", {}).items())
        out += ["", "## Bản Việt hóa đang chạy trong game (gói arcx)", "",
                f"Nguồn: {arcs} trong `dist/` của dự án patch AmeeVH — văn bản tiếng Việt thực tế người chơi thấy. "
                "Cảnh/bảng đã có trong Merge (đã review) thì dùng Merge, không lặp lại ở đây.", "",
                f"- Cảnh AVG: **{arcx_meta.get('scenes_included', 0)}** nạp / {arcx_meta.get('scenes_total', 0)} cảnh trong gói "
                f"({arcx_meta.get('scenes_skipped_merge', 0)} cảnh dùng bản Merge)",
                f"- Bảng text: **{arcx_meta.get('tables_included', 0)}** bảng, {arcx_meta.get('table_strings', 0)} chuỗi tiếng Việt"]
        un = arcx_meta.get("scenes_untranslated", [])
        if un:
            out.append(f"- Cảnh còn nguyên EN, không nạp ({len(un)}): " + ", ".join(un[:30]) + (" ..." if len(un) > 30 else ""))
    if patch_meta and patch_meta.get("coverage"):
        out += ["", "## Bản Việt hóa trong patch (dự án AmeeVH)", "",
                f"Nguồn: {len(patch_meta['sources'])} bản tổng hợp `delivery/*/Van_ban_EN_VI.jsonl` cộng "
                f"{len(patch_meta['hotfix_files'])} file `hotfix_*` ({patch_meta['overlay_rows_used']} dòng ghi đè/bổ sung). "
                "Trường `status` trong dữ liệu gốc ghi \"Bản nháp\" (chưa thấy ghi nhận review độc lập); "
                "dòng giữ nguyên EN không được nạp.", "",
                "| Phiên bản | Loại nội dung | Tài liệu | Dòng nguồn | Có VI | Giữ EN | Chưa có VI |",
                "|---|---|--:|--:|--:|--:|--:|"]
        for k, c in patch_meta["coverage"].items():
            ver, cat = k.split(" | ", 1)
            out.append(f"| {ver} | {cat} | {c['docs']} | {c['rows']} | {c['vi']} | {c['keep_en']} | {c['missing']} |")
        for k, items in patch_meta.get("missing_docs", {}).items():
            out += ["", f"Chưa có VI — {k}: " + ", ".join(items[:20]) + (" ..." if len(items) > 20 else "")]
    if untranslated:
        out += ["", "## Merge đã có nhưng chưa dịch xong (chưa nạp)", ""] + [f"- `{p}`" for p in untranslated]
    if errors:
        out += ["", "## Lỗi đọc file (bị bỏ qua)", ""] + [f"- `{p}`: {m}" for p, m in errors]
    if warnings:
        out += ["", "## Cảnh báo", ""] + [f"- {w}" for w in warnings]
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- main build
def jsonl(rows) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows).encode("utf-8")


def build(source: Path, resource_name: str | None, patch_root: Path | None = None):
    res = find_resource(source, resource_name)
    outputs: dict[str, bytes] = {}
    infos, all_blocks, all_chunks, warnings, errors = [], [], [], [], []
    untranslated, partial_set, translated_set, pending_set = [], set(), set(), set()

    for top, (cat, _d) in CATEGORIES.items():
        base = res / top
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*_Merge.txt")):
            rel = path.relative_to(res).as_posix()
            try:
                doc, recs, chunk_rows, info, warns = build_file(rel, None, path.read_bytes(), cat)
            except (ValueError, UnicodeDecodeError) as exc:
                errors.append((rel, str(exc)))
                continue
            warnings += [f"{rel}: {w}" for w in warns]
            if doc is None:
                pending_set.add(rel)
                untranslated.append(rel)
                continue
            (translated_set if info["status"] == "translated" else partial_set).add(rel)
            outputs[f"docs/{info['doc_id']}.md"] = doc.encode("utf-8")
            all_blocks += recs
            all_chunks += chunk_rows
            infos.append(info)

    gmd, gchunks, ginfo = build_glossary(source / "glossary" / "glossary.csv")
    if gmd:
        outputs["glossary.md"] = gmd.encode("utf-8")
    all_chunks += gchunks

    patch_meta, arcx_meta = {}, {}
    if patch_root is not None:
        if patch_root.is_dir():
            gmap = load_glossary_map(source / "glossary" / "glossary.csv")
            merge_keys = {Path(i["doc_id"]).name for i in infos}
            # 1) gói arcx đang chạy trong game (đủ nhất); Merge đã review được ưu tiên cho cảnh/bảng trùng
            adocs, arecs, achunks, ainfo, awarn = build_arcx(patch_root, gmap, merge_keys)
            warnings += awarn
            outputs.update(dict(adocs))
            all_blocks += arecs
            all_chunks += achunks
            infos += ainfo.get("infos", [])
            arcx_meta = ainfo.get("meta", {})
            # 2) bản tổng hợp delivery/hotfix: chỉ bổ sung phần gói arcx chưa có
            pdocs, precs, pchunks, pinfo, pwarn = build_patch(patch_root, gmap, merge_keys | ainfo.get("covered", set()))
            warnings += pwarn
            outputs.update(dict(pdocs))
            all_blocks += precs
            all_chunks += pchunks
            infos += pinfo.get("infos", [])
            patch_meta = pinfo.get("meta", {})
        else:
            warnings.append("Không thấy dự án patch (--patch-root) nên bỏ qua nguồn bản Việt hóa trong patch")

    ids = [c["id"] for c in all_chunks]
    if len(ids) != len(set(ids)):
        raise SystemExit("Trùng id chunk — kiểm tra file_id trùng giữa các nhóm")
    outputs["blocks.jsonl"] = jsonl(all_blocks)
    outputs["chunks.jsonl"] = jsonl(all_chunks)

    cats, groups = coverage(res, translated_set, pending_set, partial_set)
    infos.sort(key=lambda i: i["doc_id"])
    outputs["STATUS.md"] = status_md(cats, groups, infos, warnings, ginfo, untranslated, errors, patch_meta, arcx_meta).encode("utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source_resource": res.name,
        "counts": {"docs": len(infos), "blocks": len(all_blocks), "chunks": len(all_chunks),
                   "glossary_entries": ginfo.get("entries", 0)},
        "glossary_sha256": ginfo.get("sha256", ""),
        "files": infos,
        "untranslated_merges": untranslated,
        "errors": [{"path": p, "error": m} for p, m in errors],
        "warnings": warnings,
        "coverage": {k: v for k, v in sorted(cats.items())},
        "patch": patch_meta,
        "patch_game": arcx_meta,
    }
    outputs["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    digest = hashlib.sha256()
    for name in sorted(outputs):
        digest.update(name.encode() + b"\0" + outputs[name] + b"\0")
    return outputs, manifest, digest.hexdigest(), errors


def read_existing(out: Path):
    path = out / "manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_outputs(out: Path, outputs, manifest, digest):
    manifest = dict(manifest, content_sha256=digest,
                    built_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    outputs = dict(outputs)
    outputs["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    outputs["STATUS.md"] += f"\n_Cập nhật lần cuối: {manifest['built_at']}_\n".encode("utf-8")
    out.mkdir(parents=True, exist_ok=True)
    keep = set(outputs)
    docs = out / "docs"
    if docs.exists():
        for p in docs.rglob("*.md"):
            if p.relative_to(out).as_posix() not in keep:
                p.unlink()
        for d in sorted((d for d in docs.rglob("*") if d.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()
    for name, data in outputs.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, target)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=os.environ.get("SS_SOURCE_ROOT") or str(HERE.parent / "StellaSoraVietHoaData"))
    ap.add_argument("--patch-root", default=os.environ.get("SS_PATCH_ROOT") or str(HERE.parent / "StellaSora_EN" / "StellaSora_VietHoa"),
                    help="Dự án patch AmeeVH (bản Việt hóa 2.x); 'none' để bỏ qua nguồn này")
    ap.add_argument("--resource", help="Tên thư mục tài nguyên (mặc định: bản StellaSora_TaiNguyen_* mới nhất)")
    ap.add_argument("--out", default=str(HERE / "knowledge"))
    ap.add_argument("--check", action="store_true", help="Không ghi; exit 1 nếu tri thức đã cũ so với nguồn")
    ap.add_argument("--strict", action="store_true", help="Exit 2 nếu có file Merge không đọc được")
    args = ap.parse_args(argv)

    source, out = Path(args.source).resolve(), Path(args.out).resolve()
    if not source.is_dir():
        print(f"Không thấy thư mục nguồn: {source}", file=sys.stderr)
        return 2
    patch_root = None if str(args.patch_root).lower() in ("none", "") else Path(args.patch_root).resolve()
    outputs, manifest, digest, errors = build(source, args.resource, patch_root)
    old = read_existing(out)
    stale = old.get("content_sha256") != digest

    def diff():
        before = {f["doc_id"]: f["source_sha256"] for f in old.get("files", [])}
        after = {f["doc_id"]: f["source_sha256"] for f in manifest["files"]}
        return ([d for d in after if d not in before],
                [d for d in after if d in before and before[d] != after[d]],
                [d for d in before if d not in after])

    new, changed, removed = diff()
    if args.check:
        print("Tri thức ĐÃ CŨ — chạy build_knowledge.py để cập nhật." if stale else "Tri thức đang mới.")
        return 1 if stale else 0
    if stale:
        write_outputs(out, outputs, manifest, digest)
    c = manifest["counts"]
    print(("Đã cập nhật" if stale else "Không có thay đổi") + f": {c['docs']} tài liệu, {c['blocks']} khối, "
          f"{c['chunks']} chunk, {c['glossary_entries']} thuật ngữ -> {out}")
    for label, items in (("mới", new), ("đổi", changed), ("bỏ", removed)):
        if items and stale:
            print(f"  {label} ({len(items)}): " + ", ".join(items[:15]) + (" ..." if len(items) > 15 else ""))
    if manifest["untranslated_merges"]:
        print(f"  Merge chưa dịch xong, chưa nạp: {len(manifest['untranslated_merges'])}")
    for path, msg in errors:
        print(f"  LỖI {path}: {msg}", file=sys.stderr)
    return 2 if (errors and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
