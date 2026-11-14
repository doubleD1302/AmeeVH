"""Offline behavioral tests; no Google calls and no project data changes."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sheet_sync as sync


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / sync.RESOURCE).mkdir()
        self.key = sync.RESOURCE + "/01_CotTruyen/01_Chinh/Chuong_STm02/STm02_08/STm02_08_Merge.txt"
        self.token = sync.begin(self.root)["run"]

    def write(self, count=1, key=None, static=False, vi="Nội dung VI", multiline=False):
        key = key or self.key
        parts, exported = [], []
        for i in range(1, count + 1):
            label = f"EN: a/path/{i}/JP: b/path/{i}/CN: c/path/{i}" if static else "VI/ EN/ JP/ CN"
            header = f"{i}. [{label}]" + ("" if static else " (Lời thoại)")
            source = {"CN": f"中文 {i}", "JP": f"日本語 {i}", "EN": f"English {i}" + ("\ncontinued" if multiline else "")}
            parts.append(header + "\n" + "\n".join([source[l] for l in ("CN", "JP", "EN")] + ([vi] if vi else [])))
            exported.append({"block_order": i, "header": header, "source": source, "text_vi": vi})
        data = b"\xef\xbb\xbf" + ("\n\n".join(parts) + "\n").replace("\n", "\r\n").encode("utf-8")
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return sync.prepare(self.root, key, {"merge_sha256": sync.sha(data), "blocks": exported}) if vi else (key, data, exported)

    def remote(self, payload, rows=None):
        rows = copy.deepcopy(payload["rows"] if rows is None else rows)
        return {"spreadsheet_id": sync.SPREADSHEET, "exists": True, "title": payload["sheet_name"],
                "sheet_id": 17, "row_count": len(rows) + 1, "column_count": 12,
                "headers": sync.HEADERS, "keys": [r[:2] for r in rows], "rows": rows,
                "table": {"table_id": "23", "sheet_id": 17, "headers": sync.HEADERS,
                          "end_row": len(rows) + 1, "end_column": 12, "block_order_type": "DOUBLE"}}

    def published(self, payload):
        sync.scan(self.root, save=True)
        before = self.remote(payload, [])
        before["row_count"] = 1
        plan = sync.build(self.root, self.token, payload, before)
        sync.confirm(self.root, self.token, plan, self.remote(payload))
        return plan

    def simulate(self, plan, remote):
        # Interpret row requests independently and check all neighboring cell values.
        rows = [sync.HEADERS.copy()] + copy.deepcopy(remote["all_rows"])
        rows += [[""] * 12 for _ in range(remote["row_count"] - len(rows))]
        for request in plan["requests"]:
            if "deleteDimension" in request:
                r = request["deleteDimension"]["range"]
                del rows[r["startIndex"]:r["endIndex"]]
            elif "insertDimension" in request:
                r = request["insertDimension"]["range"]
                rows[r["startIndex"]:r["startIndex"]] = [[""] * 12 for _ in range(r["endIndex"] - r["startIndex"])]
            elif "appendDimension" in request:
                rows.extend([[""] * 12 for _ in range(request["appendDimension"]["length"])])
            elif "updateCells" in request:
                r = request["updateCells"]
                first = r["start"]["rowIndex"]
                for i, row in enumerate(r["rows"]):
                    rows[first + i] = [next(iter(c["userEnteredValue"].values())) for c in row["values"]]
        return rows[:len(plan["expected_keys"]) + 1]

    def test_first_scan_new_and_no_published_baseline(self):
        self.write()
        self.assertEqual(sync.scan(self.root, save=True)["new"], [self.key])
        self.assertEqual(sync.scan(self.root)["new"], [self.key])

    def test_unchanged_file_not_read(self):
        self.published(self.write())
        with patch.object(sync, "snapshot", side_effect=AssertionError("Unchanged content was read")):
            self.assertEqual(sync.scan(self.root)["unchanged"], [self.key])

    def test_metadata_only_and_new_bytes(self):
        self.published(self.write())
        path = self.root / self.key
        old = path.stat()
        os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000_000))
        self.assertEqual(sync.scan(self.root, save=True)["metadata_only"], [self.key])
        self.write(vi="Bản sửa")
        self.assertEqual(sync.scan(self.root, save=True)["changed"], [self.key])
        self.assertEqual(sync.scan(self.root)["changed"], [self.key])

    def test_rehash_detects_preserved_metadata(self):
        self.published(self.write())
        fixed = sync.metadata(self.root / self.key)
        self.write(vi="Đã thay đổi")
        with patch.object(sync, "metadata", return_value=fixed):
            self.assertEqual(sync.scan(self.root)["unchanged"], [self.key])
            self.assertEqual(sync.scan(self.root, rehash=True)["changed"], [self.key])

    def test_failed_pending_stays_dirty_even_if_reverted(self):
        p = self.write()
        self.published(p)
        new = self.write(vi="Mới")
        sync.build(self.root, self.token, new, self.remote(p))
        (self.root / self.key).write_bytes(b"\xef\xbb\xbf" + ("1. [VI/ EN/ JP/ CN] (Lời thoại)\r\n中文 1\r\n日本語 1\r\nEnglish 1\r\nNội dung VI\r\n").encode("utf-8"))
        self.assertEqual(sync.scan(self.root)["changed"], [self.key])

    def test_static_codes_and_multiline_preserved(self):
        p = self.write(static=True, multiline=True)
        r = p["rows"][0]
        self.assertEqual(r[2:7], [""] * 5)
        self.assertEqual(json.loads(r[11]), {"EN": "a/path/1", "JP": "b/path/1", "CN": "c/path/1"})
        self.assertEqual(r[10], "English 1\ncontinued")

    def test_no_invented_language_boundaries_without_evidence(self):
        self.write(multiline=True)
        with self.assertRaisesRegex(ValueError, "structured"):
            sync.prepare(self.root, self.key)

    def test_report_exports_exact_multiline_and_rejects_stale_report(self):
        p = self.write(multiline=True)
        parsed = sync.blocks((self.root / self.key).read_bytes())[0]
        row = p["rows"][0]
        info = {"merge_sha256": p["merge_sha256"], "total_blocks": 1,
                "coverage": {"1": {}}, "entries": {"one": {"block_order": 1,
                "header": parsed["header"].split(". ", 1)[1],
                "source": dict(zip(("CN", "JP", "EN"), row[8:11])), "current_text_vi": row[7]}}}
        folder = self.root / "reports"
        folder.mkdir()
        for kind in ("conflicts", "references"):
            (folder / f"translation-{kind}.html").write_text('<script id="report-data" type="application/json">' + json.dumps({"files": {self.key: info}}) + '</script>', encoding="utf-8")
        self.assertEqual(sync.prepare(self.root, self.key)["rows"], p["rows"])
        self.write(vi="Sửa tay")
        with self.assertRaisesRegex(ValueError, "reports do not match"):
            sync.prepare(self.root, self.key)

    def test_old_manifest_different_local_is_not_published_implicitly(self):
        p = self.write()
        m = {"spreadsheet_id": sync.SPREADSHEET, "sheet_name": p["sheet_name"],
             "headers": sync.HEADERS, "verification": {"matched": True},
             "files": [{"file_id": p["file_id"], "merge_path": self.key,
                        "source_sha256": p["merge_sha256"], "blocks": 1}]}
        sync.atomic(self.root / ".ss-sync" / p["sheet_name"] / "partition_manifest.json", m)
        self.write(vi="Nội dung khác")
        self.assertEqual(sync.scan(self.root, save=True)["changed"], [self.key])
        self.assertEqual(sync.load_state(self.root)["files"][self.key]["published_sha256"], p["merge_sha256"])

    def test_scope_and_excluded_tree(self):
        self.write()
        static_key = sync.RESOURCE + "/03_BangText_UI_KyNang/Achievement/Achievement_Merge.txt"
        self.write(key=static_key, static=True)
        self.write(key=sync.RESOURCE + "/99_DuLieuGoc/ignored_Merge.txt", vi="")
        self.assertEqual(sync.scan(self.root, scopes=[self.key])["new"], [self.key])
        self.assertEqual(len(sync.scan(self.root)["new"]), 2)

    def test_incomplete_translation_rejected(self):
        key, data, exported = self.write(vi="")
        with self.assertRaisesRegex(ValueError, "fully translated"):
            sync.prepare(self.root, key, {"merge_sha256": sync.sha(data), "blocks": exported})

    def test_growth_shrink_and_same_count_preserve_neighbors(self):
        old = self.write(count=2)
        before = self.remote(old)
        left = ["OTHER_A", 1, "", "", "", "", "", "=literal", "cn", "jp", "en", ""]
        right = ["OTHER_B", 1, "", "", "", "", "", "VI", "cn", "jp", "en", ""]
        all_rows = [left] + old["rows"] + [right]
        before.update(keys=[r[:2] for r in all_rows], row_count=5, all_rows=all_rows)
        before["table"]["end_row"] = 5
        for count in (1, 2, 9):
            with self.subTest(count=count):
                p = self.write(count=count, vi="Mới")
                plan = sync.build(self.root, self.token, p, before)
                actual = self.simulate(plan, before)
                self.assertEqual(actual, [sync.HEADERS, left] + p["rows"] + [right])
                self.assertEqual(plan["expected_keys"], [r[:2] for r in actual[1:]])

    def test_readback_mismatch_does_not_publish(self):
        p = self.write()
        plan = sync.build(self.root, self.token, p, self.remote(p, []))
        bad = self.remote(p)
        bad["rows"][0][7] = "sai"
        with self.assertRaisesRegex(ValueError, "Readback"):
            sync.confirm(self.root, self.token, plan, bad)
        self.assertNotIn("published_sha256", sync.load_state(self.root)["files"][self.key])

    def test_source_changed_after_write_stays_pending(self):
        p = self.write()
        plan = sync.build(self.root, self.token, p, self.remote(p, []))
        self.write(vi="Sau khi push")
        with self.assertRaisesRegex(ValueError, "stale"):
            sync.confirm(self.root, self.token, plan, self.remote(p))
        self.assertIn("pending", sync.load_state(self.root)["files"][self.key])

    def test_retry_identical_remote_is_noop_and_confirms(self):
        p = self.write()
        plan = sync.build(self.root, self.token, p, self.remote(p))
        self.assertEqual(plan["requests"], [])
        sync.confirm(self.root, self.token, plan, self.remote(p))
        self.assertEqual(sync.scan(self.root)["unchanged"], [self.key])

    def test_duplicate_and_missing_paths_not_deleted(self):
        self.published(self.write())
        second = self.key.replace("Chuong_STm02", "Chuong_STm03")
        self.write(key=second)
        self.assertEqual(len(sync.scan(self.root)["blocked"]), 2)
        (self.root / second).unlink()
        (self.root / self.key).unlink()
        self.assertEqual(sync.scan(self.root)["missing"], [self.key])

    def test_lock_and_stale_payload(self):
        with self.assertRaises(FileExistsError):
            sync.begin(self.root)
        with sync.locked(self.root, self.token):
            with self.assertRaises(FileExistsError):
                with sync.locked(self.root, self.token):
                    pass
        p = self.write()
        self.write(vi="Khác")
        with self.assertRaisesRegex(ValueError, "stale"):
            sync.build(self.root, self.token, p, self.remote(p))

    def test_bootstrap_manifest_and_recover_after_state_loss(self):
        self.published(self.write())
        (sync.home(self.root) / "state.json").unlink()
        state = sync.load_state(self.root)
        self.assertIn("published_sha256", state["files"][self.key])
        self.assertEqual(sync.scan(self.root)["metadata_only"], [self.key])

    def test_remote_interleaved_and_wrong_schema_rejected(self):
        p = self.write(count=2)
        remote = self.remote(p)
        remote["keys"].insert(1, ["OTHER", 1])
        remote["row_count"] += 1
        with self.assertRaisesRegex(ValueError, "contiguous"):
            sync.build(self.root, self.token, p, remote)
        remote = self.remote(p)
        remote["headers"] = ["old_schema"]
        with self.assertRaisesRegex(ValueError, "schema"):
            sync.build(self.root, self.token, p, remote)

    def test_new_sheet_and_literal_formula(self):
        p = self.write(vi="=SUM(A1:A2)")
        remote = {"spreadsheet_id": sync.SPREADSHEET, "exists": False, "sheet_id": 57,
                  "title": p["sheet_name"], "keys": [], "rows": []}
        plan = sync.build(self.root, self.token, p, remote)
        write = next(r["updateCells"] for r in plan["requests"] if "updateCells" in r and r["updateCells"]["start"]["rowIndex"] == 1)
        self.assertEqual(write["rows"][0]["values"][7], {"userEnteredValue": {"stringValue": "=SUM(A1:A2)"}})
        self.assertTrue(any("addTable" in r for r in plan["requests"]))


if __name__ == "__main__":
    unittest.main()
