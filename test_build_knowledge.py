"""Test nhanh cho build_knowledge.py bằng project giả trong thư mục tạm.

    python test_build_knowledge.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import build_knowledge as bk

BOM = "﻿"
STORY = (
    "1. [—/ —/ —/ —] (Tiêu đề)\n标题\nタイトル\nTitle\nTiêu đề thử\n\n"
    "2. [Dẫn chuyện] (Lời dẫn)\n<size=47>旁白==RT==行</size>\nナレ\nNarration==W==\nLời dẫn thử\n\n"
    "3. [Sylar/ Sylar/ セラ/ 塞拉] (Lời thoại)\n你好==PLAYER_NAME==\nやあ\nHi\nChào ==PLAYER_NAME==\n"
)
PENDING = "1. [—/ —/ —] (Tiêu đề)\n标题\nタイトル\nTitle\n"
UI = "1. [Item.1.1]\n名\n名\nName\nTên\n"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((BOM + text.replace("\n", "\r\n")).encode("utf-8"))


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name) / "src"
        self.out = Path(self.tmp.name) / "out"
        res = self.src / "StellaSora_TaiNguyen_EN_JP_CN_Text_test_r01"
        write(res / "01_CotTruyen/01_Chinh/Chuong_X/X_01/X_01_Merge.txt", STORY)
        write(res / "01_CotTruyen/01_Chinh/Chuong_X/X_01/X_01_EN.txt", "en")
        write(res / "01_CotTruyen/01_Chinh/Chuong_X/X_02/X_02_Merge.txt", PENDING)
        write(res / "03_BangText_UI_KyNang/Item/Item_Merge.txt", UI)
        write(self.src / "glossary/glossary.csv",
              "id,EN,target,category,JP,CN\n,Artifact,Thánh vật,term,神器,神器\n,Cancel,Hủy,ui_text,,\n"
              ",woman,phụ nữ,gender_female,,\n")

    def tearDown(self):
        self.tmp.cleanup()

    def run_build(self, *extra):
        return bk.main(["--source", str(self.src), "--out", str(self.out), "--patch-root", "none", *extra])

    def test_clean(self):
        self.assertEqual(bk.clean("<size=47>A==RT====RT==B</size>==W=="), "A\n\nB")
        self.assertEqual(bk.clean("Chào ==PLAYER_NAME=="), "Chào [tên người chơi]")
        self.assertEqual(bk.clean("a==RT==b", cjk=True), "ab")

    def test_build_incremental_and_check(self):
        self.assertEqual(self.run_build(), 0)
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["counts"]["docs"], 2)              # story + ui, bỏ file chưa dịch
        self.assertEqual(len(manifest["untranslated_merges"]), 1)
        text = (self.out / "chunks.jsonl").read_text(encoding="utf-8")
        self.assertIn("Sylar: Chào [tên người chơi]", text)
        self.assertIn("[Dẫn chuyện] Lời dẫn thử", text)
        self.assertNotIn("==", text)
        self.assertIn("Item.1.1: Tên", text)
        self.assertIn("Artifact = Thánh vật", text)
        self.assertNotIn("phụ nữ", text)                             # gender_* bị loại
        first = (self.out / "manifest.json").read_bytes()
        self.assertEqual(self.run_build("--check"), 0)
        self.run_build()
        self.assertEqual((self.out / "manifest.json").read_bytes(), first)   # không đổi thì không ghi

    def test_new_translation_is_picked_up_and_stale_doc_removed(self):
        self.run_build()
        res = next(self.src.glob("StellaSora_TaiNguyen_*"))
        write(res / "01_CotTruyen/01_Chinh/Chuong_X/X_02/X_02_Merge.txt", STORY)
        self.assertEqual(self.run_build("--check"), 1)
        self.run_build()
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["counts"]["docs"], 3)
        (res / "01_CotTruyen/01_Chinh/Chuong_X/X_02/X_02_Merge.txt").unlink()
        self.run_build()
        self.assertFalse((self.out / "docs/01_CotTruyen/01_Chinh/Chuong_X/X_02.md").exists())


class PatchSourceTest(BuildTest):
    """Nguồn patch AmeeVH: delivery + hotfix ghi đè dòng còn trống."""

    def make_patch(self, with_hotfix):
        root = Path(self.tmp.name) / "patch"
        run = root / "work/runs/localize_x"
        d = run / "delivery/2.1.0"
        d.mkdir(parents=True, exist_ok=True)
        (run / "210_AvgCharacter.json").write_text(
            json.dumps({"records": [{"id": "avg1_103", "name": "Amber"}]}), encoding="utf-8")

        def row(i, text, cmd, loc, status="Bản nháp", voice=""):
            return {"id": f"2.1.0:lua:0xabc:{i}", "text_vi": text, "status": status, "source": {
                "source_text": "en", "category": "Chương đặc biệt", "scene": "S_01", "command": cmd,
                "locator": loc, "actor_voice": voice, "entry_hash": "0xabc"}}

        rows = [row("command/1/param/2", "Tiêu đề cảnh thử", "SetIntro", "command/1/param/2"),
                row("command/2/param/7", "Chào <size=3>cậu</size>==W==", "SetTalk", "command/2/param/7",
                    voice="avg1_103 | vo_1"),
                row("command/3/param/7", "", "SetTalk", "command/3/param/7", status="Chờ dịch")]
        (d / "Van_ban_EN_VI.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        if with_hotfix:
            h = root / "work/hotfix_a"
            h.mkdir(parents=True, exist_ok=True)
            (h / "pending_vi.jsonl").write_text(
                json.dumps({"id": "2.1.0:lua:0xabc:command/3/param/7", "text_vi": "Dòng bổ sung"},
                           ensure_ascii=False) + "\n", encoding="utf-8")
        return root

    def run_patch(self, root):
        return bk.main(["--source", str(self.src), "--out", str(self.out), "--patch-root", str(root)])

    def test_patch_missing_then_overlay(self):
        self.run_patch(self.make_patch(with_hotfix=False))
        status = (self.out / "STATUS.md").read_text(encoding="utf-8")
        self.assertIn("| 2.1.0 | Chương đặc biệt | 1 | 3 | 2 | 0 | 1 |", status)
        self.run_patch(self.make_patch(with_hotfix=True))
        text = (self.out / "chunks.jsonl").read_text(encoding="utf-8")
        self.assertIn("Amber: Chào cậu", text)
        self.assertIn("Dòng bổ sung", text)
        self.assertNotIn("==W==", text)
        self.assertTrue((self.out / "docs/patch_2.1.0/story/S_01.md").exists())


class ArcxHelpersTest(unittest.TestCase):
    """Phần xử lý dữ liệu trích từ gói arcx (không cần Node)."""

    def test_group_table_rows(self):
        rows = [("Item.1.1", "Đồng Dorra"), ("Item.1.2", "Tiền tệ cơ bản"), ("Item.2.1", "Kim Cương"),
                ("vo_103_x.text.female_jp[0]", "Chào cậu")]
        self.assertEqual(bk.group_table_rows(rows), [
            ("Item.1", "Đồng Dorra | Tiền tệ cơ bản"), ("Item.2", "Kim Cương"),
            ("vo_103_x.text.female_jp[0]", "Chào cậu")])

    def test_flatten_and_vi_detection(self):
        got = dict(bk.flatten_strings({"anim": {}, "text": {"female_jp": ["Chào", ""]}}))
        self.assertEqual(got["text.female_jp[0]"], "Chào")
        self.assertTrue(bk.has_vi("Cậu khỏe không"))
        self.assertFalse(bk.has_vi("Hello there"))

    def test_scene_records_layouts(self):
        scene = {"commands": [
            [0, "SetIntro", ["ep", "Hồi Một", "Khởi Đầu", "Tóm tắt thử", 0]],
            [1, "SetTalk", [3, "avg1_103", "", 1, "", False, "", "Chào <size=3>cậu</size>==W==", ""]],
            [2, "SetTalk", [3, "0", "", 1, "", False, "", "Gió thổi.", ""]],
            [3, "SetBubble", ["avg1_111", "002", "", 0, "vo", "", "Cô Gái Bồn Chồn", 1, "Này!", ""]],
            [4, "SetChoiceBegin", ["a_1", 1, [0], [""], 0, 0, "a", "002", "", "", [""], "", ["Đồng ý", ""], ["Đồng ý", ""]]],
            [5, "SetSceneHeading", ["10:00 ", " Tháng Floris ", " Ngày 26 ", " Khu Tro Tàn", ""]],
        ]}
        recs, title, speakers, talk, talk_vi = bk.scene_records(scene, {"avg1_103": "Amber", "avg1_111": "Iris"}, {})
        lines = [bk.block_line(dict(r, origin="x")) for r in recs if r["kind"] not in bk.SPEAKER_TITLE_KINDS]
        self.assertEqual(title["Tiêu đề"], "Khởi Đầu")
        self.assertEqual(lines[0], "Amber: Chào cậu")
        self.assertEqual(lines[1], "[Dẫn chuyện] Gió thổi.")
        self.assertEqual(lines[2], "Cô Gái Bồn Chồn: Này!")       # tên hiển thị ghi đè
        self.assertEqual(lines[3], "[Lựa chọn] Đồng ý")
        self.assertEqual(lines[4], "[Tiêu đề cảnh] 10:00 · Tháng Floris · Ngày 26 · Khu Tro Tàn")
        self.assertEqual((talk, talk_vi), (3, 3))


if __name__ == "__main__":
    unittest.main()
