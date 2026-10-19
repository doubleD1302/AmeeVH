"""Synthetic fixtures test guard rails, not game translation quality."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("localize", Path(__file__).resolve().parents[1] / "tools/localize.py")
loc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loc)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = self.root / "game"
        self.folder = self.game / "Persistent_Store/Videos"
        self.folder.mkdir(parents=True)
        self.file = self.folder / "test_EN.srt"
        self.raw = b'\xef\xbb\xbf1\r\n00:00:00,000 --> 00:00:02,000\r\nHello, {name}!\r\n\r\n2\r\n00:00:02,100 --> 00:00:04,000\r\nGain +10% power.\r\n\r\n'
        self.file.write_bytes(self.raw)
        self.rows = loc.extract_srt(self.game, "Persistent_Store/Videos")
        self.catalog = self.root / "source.jsonl"
        self.catalog.write_text("".join(loc.canonical(r) + "\n" for r in self.rows), encoding="utf-8")
        self.proposal = self.root / "proposal.json"
        self.review = self.root / "review.json"
        self.p = {"schema": 1, "kind": "translation_proposal", "batch_id": "SYNTHETIC_TEST_ONLY",
                  "catalog_sha256": loc.digest_file(self.catalog), "translator": "synthetic-translator",
                  "entries": [{"id": r["id"], "source_sha256": r["source_sha256"], "source": r,
                               "text_vi": t, "notes": "synthetic fixture"}
                              for r, t in zip(self.rows, ["Chào {name}!", "Tăng +10% sức mạnh."])]}
        self.write_proposal()
        self.write_review()

    def tearDown(self):
        self.tmp.cleanup()

    def write_proposal(self):
        self.proposal.write_text(json.dumps(self.p, ensure_ascii=False), encoding="utf-8")

    def write_review(self):
        self.r = {"schema": 1, "catalog_sha256": loc.digest_file(self.catalog),
                  "glossary_sha256": loc.digest_text(loc.canonical({"entries": []})),
                  "proposal_sha256": loc.digest_file(self.proposal), "reviewer": "synthetic-reviewer",
                  "independent": True, "decisions": [{"id": e["id"], "status": "approved",
                  "rationale": "Synthetic fixture only, not a semantic review.",
                  "evidence": "tests/test_localize.py", "warnings_ack": []} for e in self.p["entries"]]}
        self.write_review_file()

    def write_review_file(self):
        self.review.write_text(json.dumps(self.r), encoding="utf-8")

    def audit(self):
        return loc.audit(self.catalog, self.proposal, {"entries": []})

    def approval(self):
        return loc.approved(self.catalog, self.proposal, self.review, {"entries": []})

    def test_noop_preserves_bom_crlf_and_trailing_bytes(self):
        _, cues = loc.parse_srt(self.raw)
        self.assertEqual(self.raw, loc.render_srt(self.raw, {c["index"]: c["text"] for c in cues}))

    def test_multiline_lf_no_bom_roundtrip(self):
        raw = b'1\n00:00:01,000 --> 00:00:03,000\nHello\nWorld\n\n'
        _, cues = loc.parse_srt(raw)
        self.assertEqual(cues[0]["text"], "Hello\nWorld")
        self.assertEqual(raw, loc.render_srt(raw, {"1": "Hello\nWorld"}))

    def test_duplicate_cues_fail(self):
        with self.assertRaises(ValueError):
            loc.parse_srt(self.raw + self.raw[3:])

    def test_unparsed_content_fails(self):
        with self.assertRaises(ValueError):
            loc.parse_srt(b'not a subtitle\n' + self.raw[3:])

    def test_missing_token_and_changed_sign_fail(self):
        self.p["entries"][0]["text_vi"] = "Xin chào!"
        self.p["entries"][1]["text_vi"] = "Tăng -10% sức mạnh."
        self.write_proposal()
        errors = [e for row in self.audit()["rows"] for e in row["errors"]]
        self.assertIn("TOKEN_MISMATCH", errors)
        self.assertIn("NUMBER_OR_SIGN_MISMATCH", errors)

    def test_tag_order_is_protected(self):
        row = dict(self.rows[0], source_text="<b><i>Hello</i></b>")
        errors, _ = loc.quality(row, "<i><b>Chào</b></i>", {})
        self.assertIn("TAG_ORDER_MISMATCH", errors)

    def test_unnumbered_printf_order_is_protected(self):
        row = dict(self.rows[0], source_text="%s gains %d points")
        errors, _ = loc.quality(row, "Cộng %d điểm cho %s", {})
        self.assertIn("PRINTF_ORDER_MISMATCH", errors)

    def test_percent_followed_by_vietnamese_is_not_printf(self):
        errors, _ = loc.quality(self.rows[1], "Tăng +10% sát thương.", {})
        self.assertEqual(errors, [])

    def test_non_nfc_fails(self):
        import unicodedata
        target = unicodedata.normalize("NFD", "Chào {name}!")
        errors, _ = loc.quality(self.rows[0], target, {})
        self.assertIn("NON_NFC", errors)

    def test_stale_catalog_fails(self):
        self.p["catalog_sha256"] = "0" * 64
        self.write_proposal()
        self.assertFalse(self.audit()["passed"])

    def test_unknown_duplicate_and_tampered_context_fail(self):
        self.p["entries"].append(dict(self.p["entries"][0]))
        self.p["entries"][1]["id"] = "unknown"
        self.p["entries"][0]["source"] = {}
        self.write_proposal()
        self.assertGreaterEqual(self.audit()["error_count"], 3)

    def test_missing_translation_and_translator_fail(self):
        self.p["translator"] = ""
        self.p["entries"][0]["text_vi"] = ""
        self.write_proposal()
        self.assertFalse(self.audit()["passed"])

    def test_review_invalidates_after_proposal_change(self):
        self.p["entries"][0]["text_vi"] = "Xin chào {name}!"
        self.write_proposal()
        with self.assertRaisesRegex(ValueError, "stale"):
            self.approval()

    def test_self_review_fails(self):
        self.r["reviewer"] = self.p["translator"]
        self.write_review_file()
        with self.assertRaises(ValueError):
            self.approval()

    def test_blank_rationale_fails(self):
        self.r["decisions"][0]["rationale"] = ""
        self.write_review_file()
        with self.assertRaises(ValueError):
            self.approval()

    def test_null_evidence_cannot_be_approved(self):
        self.r["decisions"][0]["evidence"] = None
        self.write_review_file()
        with self.assertRaises(ValueError):
            self.approval()

    def test_pending_or_nonindependent_review_fails(self):
        self.r["independent"] = False
        self.write_review_file()
        with self.assertRaises(ValueError):
            self.approval()

    def test_unacknowledged_warning_fails(self):
        self.p["entries"][0]["text_vi"] = self.rows[0]["source_text"]
        self.write_proposal()
        self.write_review()
        with self.assertRaisesRegex(ValueError, "warning"):
            self.approval()

    def test_approved_glossary_only(self):
        term = {"source": "Hello", "target": "Xin chào", "status": "proposed"}
        self.assertFalse(loc.quality(self.rows[0], "Chào {name}!", {"entries": [term]})[0])
        term["status"] = "approved"
        self.assertIn("GLOSSARY:Hello", loc.quality(self.rows[0], "Chào {name}!", {"entries": [term]})[0])

    def test_build_reads_back_and_preserves_live_game(self):
        out = self.root / "candidate"
        self.assertEqual(1, loc.build_srt(self.game, self.catalog, self.proposal, self.review, {"entries": []}, out))
        candidate = (out / "files/Persistent_Store/Videos/test_EN.srt").read_bytes()
        self.assertEqual(self.file.read_bytes(), self.raw)
        _, cues = loc.parse_srt(candidate)
        self.assertEqual(cues[0]["text"], "Chào {name}!")
        self.assertTrue(candidate.startswith(b'\xef\xbb\xbf'))
        self.assertFalse(loc.read(out / "manifest.json")["installed"])

    def test_native_file_drift_fails_before_writing(self):
        self.file.write_bytes(self.raw + b'\n')
        out = self.root / "candidate"
        with self.assertRaisesRegex(ValueError, "changed"):
            loc.build_srt(self.game, self.catalog, self.proposal, self.review, {"entries": []}, out)
        self.assertFalse(out.exists())

    def test_partial_file_cannot_be_built(self):
        self.p["entries"] = self.p["entries"][:1]
        self.write_proposal()
        self.write_review()
        with self.assertRaisesRegex(ValueError, "Partial"):
            loc.build_srt(self.game, self.catalog, self.proposal, self.review, {"entries": []}, self.root / "candidate")

    def test_glossary_change_invalidates_review(self):
        with self.assertRaisesRegex(ValueError, "glossary"):
            loc.approved(self.catalog, self.proposal, self.review, {"entries": [], "revision": 2})

    def test_path_traversal_and_live_outputs_refused(self):
        for p in ["../escape", "C:/Windows/evil", "work/../../evil", "file.txt:stream"]:
            with self.assertRaises(ValueError):
                loc.confined(self.root, p)
        with self.assertRaises(ValueError):
            loc.output_path("../Persistent_Store/test.srt")
        with self.assertRaises(ValueError):
            loc.output_path("tools/overwrite.py")

    def test_existing_output_preserved(self):
        p = self.root / "keep.json"
        loc.save(p, {"original": True})
        with self.assertRaises(FileExistsError):
            loc.save(p, {"original": False})
        self.assertTrue(loc.read(p)["original"])

    def test_diff_flags_source_context_and_new_ids(self):
        rows = json.loads(json.dumps(self.rows))
        rows[0]["source_text"] = "New {name}"
        rows[0]["source_sha256"] = loc.digest_text(rows[0]["source_text"])
        rows[1]["context"]["next"] = "Changed scene"
        new = self.root / "new.jsonl"
        new.write_text("".join(loc.canonical(r) + "\n" for r in rows), encoding="utf-8")
        counts = loc.diff_catalogs(self.catalog, new)["counts"]
        self.assertEqual(counts["text_changed"], 1)
        self.assertEqual(counts["context_or_file_changed"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
