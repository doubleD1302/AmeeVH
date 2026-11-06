"""Behavior tests use isolated temporary projects, never the SS data tree."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("update_reports", Path(__file__).with_name("update_reports.py"))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def block(number, word="Một", conflict=True, reference=True):
    return {"block_order": number, "kind": "Lời thoại", "speaker": "Sylar",
            "source": {"EN": word + ' <size=48>EN</size>\nline 2 ==W== %s', "JP": word + " 日本語", "CN": word + " 中文"},
            "text_vi": word + " tiếng Việt", "source_refs": {},
            "conflicts": [{"title": "Khác chủ thể", "detail": "EN khác CN/JP.", "handling": "VI bám EN.", "basis": "EN", "languages": ["EN", "JP", "CN"]}] if conflict else [],
            "references": [{"title": "Chơi chữ", "detail": "Hai nghĩa trong cùng ngữ cảnh.", "handling": "Giữ nghĩa chính.", "languages": ["EN"], "confidence": "verified",
                            "evidence": [{"label": "Đối chiếu trực tiếp trong câu", "url": ""}]}] if reference else []}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ss-report-tests-")
        self.root = Path(self.temp.name).resolve()
        self.assertTrue(self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.path = report.RESOURCE + "/01_CotTruyen/01_Chinh/Chuong_STm02/STm02_05/scene_Merge.txt"

    def tearDown(self):
        self.temp.cleanup()

    def write_merge(self, blocks, path=None):
        path = path or self.path
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        units = []
        for b in blocks:
            parts = [b["source"][k] for k in ("CN", "JP", "EN")] + ([b["text_vi"]] if b["text_vi"] else [])
            header = '[' + b['source_code'] + ']' if b.get('ui_type') == 'static' else f'[Sylar/ Sylar/ セラ/ 塞拉] ({b["kind"]})'
            units.append(f'{b["block_order"]}. {header}\n' + "\n".join(parts))
        p.write_bytes(("\n\n".join(units) + "\n").replace("\n", "\r\n").encode("utf-8-sig"))

    def payload(self, reviewed, path=None):
        path = path or self.path
        return {"files": [{"merge_path": path, "merge_sha256": report.sha((self.root / path).read_bytes()), "blocks": copy.deepcopy(reviewed)}]}

    def stores(self):
        return report.load_pair(self.root)[1]

    def bytes_pair(self):
        return {k: (self.root / "reports" / name).read_bytes() for k, name in report.REPORT_NAMES.items()}

    def test_init_is_empty_and_keeps_existing_data(self):
        report.run(self.root, initialize=True)
        self.assertEqual(len(list((self.root / "reports").iterdir())), 2)
        self.assertFalse(self.stores()["conflicts"]["files"])
        before = self.bytes_pair()
        report.run(self.root, initialize=True)
        self.assertEqual(before, self.bytes_pair())

    def static_block(self, number=1, code="Achievement.1.1"):
        b = block(number)
        b.update(ui_type="static", source_code=code, kind="", speaker="")
        return b

    def test_static_common_code_preserves_header_and_all_content(self):
        b = self.static_block()
        self.write_merge([b]);original = (self.root / self.path).read_bytes()
        report.run(self.root, self.payload([b]))
        self.assertEqual((self.root / self.path).read_bytes(), original)
        for store in self.stores().values():
            e = store["files"][self.path]["entries"]["1"]
            self.assertEqual(e["ui_type"], "static")
            self.assertEqual(e["header"], "[Achievement.1.1]")
            self.assertEqual(e["source_refs"], {k: "Achievement.1.1" for k in ("EN", "JP", "CN")})
            self.assertEqual((e["kind"], e["speaker"]), ("", ""))
            self.assertEqual(e["source"], b["source"])

    def test_static_distinct_codes_keep_internal_slashes(self):
        b = self.static_block(code="EN: Table/item/1/JP: Table/item/2/CN: Table/item/3")
        self.write_merge([b]);report.run(self.root, self.payload([b]))
        e = self.stores()["conflicts"]["files"][self.path]["entries"]["1"]
        self.assertEqual(e["source_refs"], {"EN": "Table/item/1", "JP": "Table/item/2", "CN": "Table/item/3"})
        self.assertEqual(e["source_code"], b["source_code"])
        common = self.static_block(code="Table/item/with/slashes")
        self.write_merge([common]);report.run(self.root, self.payload([common]))
        self.assertEqual(self.stores()["references"]["files"][self.path]["entries"]["1"]["source_refs"]["EN"], common["source_code"])

    def test_static_retranslate_partial_scope_and_renumber_use_codes(self):
        a, b = self.static_block(), self.static_block(2, "Achievement.2.1")
        # Identical contents at separate source codes stay separate.
        self.write_merge([a,b]);report.run(self.root,self.payload([a,b]))
        uid = self.stores()["conflicts"]["files"][self.path]["entries"]["1"]["uid"]
        a["text_vi"] = "VI mới";a["conflicts"] = [];a["references"] = []
        self.write_merge([a,b]);report.run(self.root,self.payload([a]))
        info=self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(len(info["entries"]),2)
        self.assertEqual(info["entries"]["1"]["uid"],uid)
        self.assertEqual(info["entries"]["1"]["status"],"absent")
        self.assertEqual(info["entries"]["2"]["text_vi"],b["text_vi"])
        a["block_order"],b["block_order"]=2,1
        self.write_merge([b,a]);report.run(self.root,self.payload([b,a]))
        info=self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(info["entries"]["2"]["uid"],uid)
        self.assertFalse(info["unresolved"])

    def test_static_metadata_mismatch_is_rejected_before_report_change(self):
        b = self.static_block();self.write_merge([b]);report.run(self.root,self.payload([b]))
        old=self.bytes_pair()
        for fields in ({"kind":"Lời thoại"},{"speaker":"Achievement"},{"source_code":"Changed"},{"ui_type":"story"},{"source_refs":{"EN":"wrong"}}):
            with self.subTest(fields=fields):
                payload=self.payload([b]);payload["files"][0]["blocks"][0].update(fields)
                with self.assertRaises(ValueError):report.run(self.root,payload)
                self.assertEqual(self.bytes_pair(),old)

    def test_old_story_reports_remain_readable_and_stable(self):
        b = block(1);self.write_merge([b]);report.run(self.root,self.payload([b]))
        originals, stores=report.load_pair(self.root)
        uid=stores["conflicts"]["files"][self.path]["entries"]["1"]["uid"]
        for k,s in stores.items():
            for e in s["files"][self.path]["entries"].values():
                e.pop("ui_type");e.pop("source_code")
        report.commit_pair(self.root, originals, stores, [])
        report.run(self.root,self.payload([b]))
        e=self.stores()["conflicts"]["files"][self.path]["entries"]["1"]
        self.assertEqual(e["uid"],uid)
        self.assertEqual(e["ui_type"],"story")

    def test_repeat_updates_absence_and_new_vi_without_duplicates(self):
        b = block(1)
        self.write_merge([b])
        report.run(self.root, self.payload([b]))
        uid = self.stores()["conflicts"]["files"][self.path]["entries"]["1"]["uid"]
        b["conflicts"][0]["detail"] = "Updated explanation"
        report.run(self.root, self.payload([b]))
        entry = self.stores()["conflicts"]["files"][self.path]["entries"]["1"]
        self.assertEqual(entry["uid"], uid)
        self.assertEqual(entry["findings"][0]["detail"], "Updated explanation")
        b["text_vi"] = "VI đã hiệu đính"
        b["conflicts"] = []
        self.write_merge([b])
        report.run(self.root, self.payload([b]))
        info = self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(len(info["entries"]), 1)
        self.assertEqual(info["entries"]["1"]["status"], "absent")
        self.assertEqual(info["entries"]["1"]["uid"], uid)
        self.assertEqual(info["entries"]["1"]["previous_context"]["text_vi"], "Một tiếng Việt")

    def test_no_findings_records_coverage_and_partial_preserves_other_blocks(self):
        a, b = block(1, conflict=False, reference=False), block(2, "Hai")
        self.write_merge([a, b])
        report.run(self.root, self.payload([a, b]))
        previous = copy.deepcopy(self.stores()["conflicts"]["files"][self.path]["entries"]["2"])
        a["text_vi"] = "Một mới"
        self.write_merge([a, b])
        report.run(self.root, self.payload([a]))
        info = self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(info["entries"]["2"], previous)
        self.assertEqual(set(info["coverage"]), {"1", "2"})
        self.assertEqual(info["entries"]["1"]["status"], "clear")
        self.assertEqual(info["entries"]["1"]["findings"], [])

    def test_each_removed_finding_is_retained_and_can_return(self):
        b = block(1)
        b["conflicts"].append({**b["conflicts"][0], "id": "second", "title": "Khác số lượng"})
        self.write_merge([b]);report.run(self.root, self.payload([b]))
        b["conflicts"].pop();b["text_vi"] = "Hiệu đính mới"
        self.write_merge([b]);report.run(self.root, self.payload([b]))
        e = self.stores()["conflicts"]["files"][self.path]["entries"]["1"]
        self.assertEqual(e["status"], "active")
        self.assertEqual([f["status"] for f in e["findings"]], ["active", "absent"])
        self.assertEqual(e["findings"][1]["previous_context"]["text_vi"], "Một tiếng Việt")
        report.run(self.root, self.payload([b]))
        self.assertEqual(len(self.stores()["conflicts"]["files"][self.path]["entries"]["1"]["findings"]), 2)
        b["conflicts"].append({**b["conflicts"][0], "id": "second", "title": "Đổi tên phát hiện"})
        report.run(self.root, self.payload([b]))
        self.assertEqual([f["status"] for f in self.stores()["conflicts"]["files"][self.path]["entries"]["1"]["findings"]], ["active", "active"])

    def test_same_file_name_in_different_deep_unicode_folders(self):
        b = block(1)
        other = report.RESOURCE + "/02_NhanVat/Tên # 1/Story/A/B/C/D/E/scene_Merge.txt"
        for path in (self.path, other):
            self.write_merge([b], path)
            report.run(self.root, self.payload([b], path))
        self.assertEqual(set(self.stores()["references"]["files"]), {self.path, other})

    def test_stale_snapshot_and_wrong_quotes_do_not_write(self):
        b = block(1)
        self.write_merge([b])
        report.run(self.root, self.payload([b]))
        before = self.bytes_pair()
        stale = self.payload([b])
        b["text_vi"] = "new VI"
        self.write_merge([b])
        with self.assertRaisesRegex(ValueError, "Stale"):
            report.run(self.root, stale)
        bad = self.payload([b]);bad["files"][0]["blocks"][0]["source"]["EN"] = "wrong"
        with self.assertRaisesRegex(ValueError, "does not match"):
            report.run(self.root, bad)
        self.assertEqual(before, self.bytes_pair())

    def test_renumber_unique_moves_entry_and_ambiguous_stays_unresolved(self):
        a, b = block(1, "Một"), block(2, "Hai", False, False)
        self.write_merge([a, b]);report.run(self.root, self.payload([a, b]))
        a["block_order"], b["block_order"] = 2, 1
        self.write_merge([b, a]);report.run(self.root, self.payload([b]))
        info = self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(set(info["entries"]), {"1", "2"})
        self.assertFalse(info["unresolved"])
        # Duplicate source/header text prevents an arbitrary relocation.
        duplicate = copy.deepcopy(a);duplicate["block_order"] = 3
        lead = block(1, "Mở đầu", False, False)
        self.write_merge([lead, a, duplicate]);report.run(self.root, self.payload([lead]))
        info = self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(sum(bool(e["findings"]) for e in info["unresolved"].values()), 1)
        a["conflicts"] = [];a["references"] = []
        report.run(self.root, self.payload([a]))
        self.assertEqual(sum(bool(e["findings"]) for e in self.stores()["conflicts"]["files"][self.path]["unresolved"].values()), 1)

    def test_verified_source_ref_updates_changed_source_without_duplicate(self):
        b = block(1);b["source_refs"] = {"EN": "scene::command/1 SetTalk/param/7"}
        self.write_merge([b]);report.run(self.root, self.payload([b]))
        uid = self.stores()["conflicts"]["files"][self.path]["entries"]["1"]["uid"]
        b["source"]["EN"] = "Different source at same verified command"
        self.write_merge([b]);report.run(self.root, self.payload([b]))
        info = self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(info["entries"]["1"]["uid"], uid)
        self.assertFalse(info["unresolved"])

    def test_unreviewed_vi_change_is_pending_and_loses_coverage(self):
        a, b = block(1), block(2, "Hai", False, False)
        self.write_merge([a, b]);report.run(self.root, self.payload([a, b]))
        a["text_vi"] = "Sửa thủ công ngoài phạm vi"
        self.write_merge([a, b]);report.run(self.root, self.payload([b]))
        info = self.stores()["conflicts"]["files"][self.path]
        self.assertEqual(info["entries"]["1"]["status"], "needs_review")
        self.assertEqual(info["entries"]["1"]["current_text_vi"], a["text_vi"])
        self.assertNotIn("1", info["coverage"])

    def test_source_exception_can_be_logged_before_vi_exists(self):
        b = block(1);b["text_vi"] = ""
        self.write_merge([b]);report.run(self.root, self.payload([b]))
        self.assertEqual(self.stores()["conflicts"]["files"][self.path]["entries"]["1"]["text_vi"], "")

    def test_html_raw_text_escaping_bom_crlf_and_readback(self):
        b = block(1, '</script><script>window.pwned=1</script> & "\\')
        b["references"][0]["evidence"][0]["url"] = "javascript:window.pwned=2"
        self.write_merge([b]);report.run(self.root, self.payload([b]))
        for data in self.bytes_pair().values():
            self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
            self.assertNotIn(b'\n', data.replace(b'\r\n', b''))
            self.assertNotIn(b'<script>window.pwned', data)
        self.assertEqual(self.stores()["conflicts"]["files"][self.path]["entries"]["1"]["source"], b["source"])

    def test_corrupt_missing_or_mixed_checkpoint_pair_is_not_overwritten(self):
        b = block(1);self.write_merge([b]);report.run(self.root, self.payload([b]))
        original = self.bytes_pair();target = self.root / "reports" / report.REPORT_NAMES["conflicts"]
        target.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):report.run(self.root, self.payload([b]))
        self.assertEqual(target.read_bytes(), b'corrupt')
        target.unlink()
        with self.assertRaises(ValueError):report.run(self.root, self.payload([b]))
        store = report.read_store(original["conflicts"], "conflicts");store["checkpoint"] = "mismatch"
        target.write_bytes(report.render(store))
        with self.assertRaisesRegex(ValueError, "checkpoints differ"):report.run(self.root, self.payload([b]))
        self.assertEqual((self.root / "reports" / report.REPORT_NAMES["references"]).read_bytes(), original["references"])

    def test_second_replace_failure_rolls_back_and_keeps_recovery(self):
        b = block(1);self.write_merge([b]);report.run(self.root, self.payload([b]))
        old = self.bytes_pair();merge = (self.root / self.path).read_bytes()
        real = report.os.replace;failed = False
        def fail_once(src, dst):
            nonlocal failed
            if Path(dst).name == report.REPORT_NAMES["references"] and not failed:
                failed = True
                raise PermissionError("file locked")
            return real(src, dst)
        with patch.object(report.os, "replace", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "recovery"):
                report.run(self.root, self.payload([b]))
        self.assertEqual(self.bytes_pair(), old)
        self.assertEqual((self.root / self.path).read_bytes(), merge)
        self.assertGreaterEqual(len(list((self.root / 'reports').glob('*.pending'))), 2)
        self.assertFalse((self.root / 'reports/.translation-reports.lock').exists())

    def test_changed_merge_during_staging_aborts_without_writing_reports(self):
        b = block(1);self.write_merge([b]);report.run(self.root, self.payload([b]))
        old = self.bytes_pair();real = report.stage;changed = False
        def interfere(*args):
            nonlocal changed
            p = real(*args)
            if not changed:
                changed = True
                (self.root / self.path).write_bytes(b'user edit')
            return p
        with patch.object(report, "stage", side_effect=interfere):
            with self.assertRaisesRegex(OSError, "Merge changed"):
                report.run(self.root, self.payload([b]))
        self.assertEqual(self.bytes_pair(), old)
        self.assertEqual((self.root / self.path).read_bytes(), b'user edit')

    def test_dry_run_writes_nothing_and_existing_lock_is_respected(self):
        b = block(1);self.write_merge([b])
        report.run(self.root, self.payload([b]), dry_run=True)
        self.assertFalse((self.root / 'reports').exists())
        (self.root / 'reports').mkdir();lock = self.root / 'reports/.translation-reports.lock';lock.write_text('other process')
        with self.assertRaisesRegex(OSError, 'locked'):report.run(self.root, self.payload([b]))
        self.assertEqual(lock.read_text(), 'other process')

    def test_merge_changed_during_replacement_rolls_back(self):
        b = block(1);self.write_merge([b]);report.run(self.root, self.payload([b]))
        old = self.bytes_pair();real = report.os.replace
        def interfere(src, dst):
            result = real(src, dst)
            if Path(dst).name == report.REPORT_NAMES["references"]:
                (self.root / self.path).write_bytes(b'user edit during replacement')
            return result
        with patch.object(report.os, "replace", side_effect=interfere):
            with self.assertRaisesRegex(OSError, "Merge changed while saving"):
                report.run(self.root, self.payload([b]))
        self.assertEqual(self.bytes_pair(), old)


if __name__ == '__main__':
    unittest.main(verbosity=2)
