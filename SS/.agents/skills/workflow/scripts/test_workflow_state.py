"""Run with Python; all writes are confined to disposable fixture projects."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import workflow_state as w

PROJECT = Path(__file__).resolve().parents[4]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.q = w.Queue(self.root)
        for relative in (".agents/skills/translate/scripts/update_reports.py",
                         ".agents/skills/translate/assets/report_template.html"):
            dest = self.root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / relative, dest)
        configs = self.root / ".codex/agents"
        configs.mkdir(parents=True)
        for name in ("merger", "term-controller", "translator"):
            shutil.copyfile(PROJECT / ".codex/agents" / (name + ".toml"), configs / (name + ".toml"))
        self.write("glossary/glossary.csv", "id,EN,target,category,JP,CN\n,Tower,Tháp,term,塔,塔\n")
        self.scope = w.RESOURCE + "/Nhánh thử/Sâu/Story"
        self.source_set(self.scope)
        self.q.init()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8-sig"))
        return path

    def source_set(self, scope, base="Test"):
        for lang in ("EN", "JP", "CN"):
            self.write(f"{scope}/{base}_{lang}.txt", f"{base} | {lang} | source\n[A/1]\nTower\n")

    def begin(self, **limits):
        self.q.enqueue([self.scope])
        run = self.q.start(**limits)
        self.token = run["token"]
        return self.q.claim(self.token)

    def finish(self, claim, **receipt):
        return self.q.complete(self.token, claim["job"]["id"], claim["job"]["claim"]["token"], {"summary": "Reviewed fixture", **receipt})

    def inspect(self, proposals=None, ui="static"):
        claim = self.begin()
        path, _ = self.merge(claim, ui=ui)
        self.finish(claim, ui_type=ui, term_proposals=proposals or [], snapshot_path=str(path))
        return self.q.claim(self.token)

    def merge(self, claim, vi="", ui="static"):
        header = "[A/1]" if ui == "static" else ("[Tên/ Name/ 名前/ 名] (Lời thoại)" if vi else "[Name/ 名前/ 名] (Lời thoại)")
        relative = claim["job"]["merge_path"]
        self.write(relative, "1. " + header + "\n塔\n塔\nTower" + ("\n" + vi if vi else "") + "\n")
        payload = {"files": [{"merge_path": relative, "merge_sha256": w.digest((self.root / relative).read_bytes()), "blocks": [{
            "block_order": 1, "kind": "" if ui == "static" else "Lời thoại", "speaker": "" if ui == "static" else "Name",
            "source": {"CN": "塔", "JP": "塔", "EN": "Tower"}, "text_vi": vi, "conflicts": [], "references": []}]}]}
        path = self.root / "snapshot.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path, payload

    def through_merge(self, ui="static"):
        return self.inspect(ui=ui)

    def done(self, ui="static"):
        claim = self.through_merge(ui)
        _, payload = self.merge(claim, "Tháp", ui)
        self.q.helper().run(self.root, payload)
        self.finish(claim)
        claim = self.q.claim(self.token)
        self.finish(claim)
        self.assertEqual(self.q.status()["counts"]["done"], 1)
        self.assertTrue(self.q.claim(self.token)["stop"])
        return claim["job"]

    def scoped_fixture(self):
        for lang, texts in {'EN': ['Tower', 'Apple'], 'JP': ['塔', '林檎'], 'CN': ['塔', '苹果']}.items():
            self.write(f'{self.scope}/Test_{lang}.txt', f'Test | {lang} | source\n[A/1]\n{texts[0]}\n[A/2]\n{texts[1]}\n')
        claim = self.begin()
        relative = claim['job']['merge_path']
        blocks = [{'block_order': n, 'kind': '', 'speaker': '',
                   'source': {'EN': en, 'JP': jp, 'CN': cn},
                   'text_vi': '', 'conflicts': [], 'references': []}
                  for n, en, jp, cn in [(1, 'Tower', '塔', '塔'), (2, 'Apple', '林檎', '苹果')]]
        def payload(translated):
            for b in blocks:
                b['text_vi'] = ('Tháp' if b['block_order'] == 1 else 'Táo') if translated else ''
            self.write(relative, '\n\n'.join(str(b['block_order']) + '. [A/' + str(b['block_order']) + ']\n' +
                       '\n'.join([b['source'][k] for k in ('CN', 'JP', 'EN')] +
                                 ([b['text_vi']] if translated else [])) for b in blocks) + '\n')
            return {'files': [{'merge_path': relative, 'merge_sha256': w.digest((self.root / relative).read_bytes()),
                              'blocks': blocks}]}
        source = payload(False)
        path = self.root / 'two_blocks.json'
        path.write_text(json.dumps(source), encoding='utf-8')
        self.finish(claim, ui_type='static', term_proposals=[], snapshot_path=str(path))
        claim = self.q.claim(self.token)
        translated = payload(True)
        self.q.helper().run(self.root, translated)
        self.finish(claim)
        self.finish(self.q.claim(self.token))
        self.q.claim(self.token)
        return relative, translated

    def scoped_claim(self, glossary):
        self.write('glossary/glossary.csv', glossary)
        self.token = self.q.start()['token']
        return self.q.claim(self.token)

    def test_scoped_target_change_reviews_one_block_and_preserves_other(self):
        relative, payload = self.scoped_fixture()
        _, prior_reports = self.q.helper().load_pair(self.root)
        other = {kind: store['files'][relative]['entries']['2'] for kind, store in prior_reports.items()}
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        self.assertEqual(claim['job']['review_scope']['blocks'], [1])
        scope = claim['job']['review_scope']
        raw = (self.root / relative).read_text(encoding='utf-8-sig')
        self.write(relative, raw.replace('Tháp', 'Tháp mới'))
        payload['files'][0]['merge_sha256'] = w.digest((self.root / relative).read_bytes())
        payload['files'][0]['blocks'] = payload['files'][0]['blocks'][:1]
        payload['files'][0]['blocks'][0]['text_vi'] = 'Tháp mới'
        self.q.helper().run(self.root, payload)
        _, after_reports = self.q.helper().load_pair(self.root)
        self.assertEqual(other, {kind: store['files'][relative]['entries']['2'] for kind, store in after_reports.items()})
        self.finish(claim, reviewed_blocks=[1])
        verify = self.q.claim(self.token)
        self.assertEqual(verify['job']['review_scope']['blocks'], [1])
        self.finish(verify)
        parsed = self.q.helper().parse_merge((self.root / relative).read_bytes())
        self.assertEqual(self.q.block_signature(parsed[2]), scope['block_hashes']['2'])
        self.assertEqual(self.q.status()['counts']['done'], 1)

    def test_scoped_unchanged_vi_retains_merge_bytes(self):
        relative, payload = self.scoped_fixture()
        raw = (self.root / relative).read_bytes()
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n,Tower,Tháp,term,塔,塔\n,Apple,Táo,term,林檎,苹果\n')
        self.assertEqual(claim['job']['review_scope']['blocks'], [2])
        payload['files'][0]['blocks'] = payload['files'][0]['blocks'][1:]
        self.q.helper().run(self.root, payload)
        self.finish(claim, reviewed_blocks=[2])
        self.finish(self.q.claim(self.token))
        self.assertEqual(raw, (self.root / relative).read_bytes())

    def test_scoped_edit_outside_scope_is_rejected(self):
        relative, _ = self.scoped_fixture()
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        self.write(relative, (self.root / relative).read_text(encoding='utf-8-sig').replace('Táo', 'Edited'))
        with self.assertRaisesRegex(ValueError, 'unaffected block'):
            self.finish(claim, reviewed_blocks=[1])

    def test_scoped_receipt_cannot_omit_required_block(self):
        self.scoped_fixture()
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        with self.assertRaisesRegex(ValueError, 'exactly the affected'):
            self.finish(claim, reviewed_blocks=[])

    def test_deleted_term_uses_old_definition_to_find_block(self):
        self.scoped_fixture()
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n')
        self.assertEqual(claim['job']['review_scope']['blocks'], [1])
        self.assertIsNone(claim['job']['review_scope']['changes'][0]['after'])

    def test_legacy_baseline_seed_only_when_fingerprint_matches(self):
        self.done()
        original, state = self.q.read()
        job = state['jobs'][0]
        job.pop('glossary_baseline', None)
        for cp in job['checkpoints'].values():
            cp['glossary'].pop('definitions', None)
        self.q.save(original, state)
        self.q.start()
        self.assertEqual(self.q.status()['counts']['done'], 1)
        self.q.stop(self.q.status()['run']['token'], 'Stopped fixture')
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        self.assertEqual(claim['job']['review_scope']['blocks'], [1])

    def test_missing_legacy_baseline_does_not_guess_old_definitions(self):
        self.done()
        original, state = self.q.read()
        job = state['jobs'][0]
        job.pop('glossary_baseline', None)
        for cp in job['checkpoints'].values():
            cp['glossary'].pop('definitions', None)
        self.q.save(original, state)
        self.write('glossary/glossary.csv', 'id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        self.q.start()
        self.assertEqual(self.q.status()['counts']['blocked'], 1)
        self.assertIn('Missing glossary baseline', self.q.status()['jobs'][0]['error'])

    def test_block_matching_names_tokens_boundaries_and_not_static_codes(self):
        block = {'speaker': '??', 'source': {'EN': 'herring ==SEX5==', 'JP': '木の葉', 'CN': '树叶'},
                 'source_code': 'Tower'}
        row = {'id': '', 'EN': 'her', 'JP': '', 'CN': ''}
        self.assertFalse(self.q.row_in_block(row, block))
        self.assertTrue(self.q.row_in_block({**row, 'EN': '??'}, block))
        self.assertTrue(self.q.row_in_block({**row, 'id': 'SEX/==SEX5==/0', 'EN': ''}, block))
        self.assertTrue(self.q.row_in_block({**row, 'EN': '', 'JP': '木の葉'}, block))
        self.assertFalse(self.q.row_in_block({**row, 'EN': 'Tower'}, block))
        block['source'] = {'EN': '<color=Red>Tower</color>', 'JP': '心<r=x></r>相', 'CN': ''}
        self.assertFalse(self.q.row_in_block({**row, 'EN': 'Red'}, block))
        self.assertTrue(self.q.row_in_block({**row, 'EN': '', 'JP': '心相'}, block))

    def test_two_glossary_updates_before_review_keep_union_of_affected_blocks(self):
        self.scoped_fixture()
        self.write('glossary/glossary.csv', 'id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        self.token = self.q.start()['token']
        self.write('glossary/glossary.csv', 'id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n,Apple,Táo,term,林檎,苹果\n')
        claim = self.q.claim(self.token)
        self.assertEqual(claim['job']['review_scope']['blocks'], [1, 2])

    def test_review_packet_contains_only_affected_blocks_and_optional_context(self):
        self.scoped_fixture()
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        state = self.q.path.read_bytes()
        packet = self.q.review_packet(claim['job']['id'])
        self.assertEqual([b['block_order'] for b in packet['payload']['files'][0]['blocks']], [1])
        self.assertEqual(packet['context_blocks'], [])
        self.assertEqual(self.q.review_packet(claim['job']['id'], 1)['context_blocks'][0]['block_order'], 2)
        self.assertEqual(state, self.q.path.read_bytes())
        self.q.helper().validate_payload(self.root, packet['payload'])

    def test_glossary_term_in_static_code_only_does_not_queue_model_review(self):
        self.scoped_fixture()
        self.write('glossary/glossary.csv', 'id,EN,target,category,JP,CN\n,Tower,Tháp,term,塔,塔\n,A/1,Do not translate codes,term,,\n')
        self.q.start()
        self.assertEqual(self.q.status()['counts']['done'], 1)
        self.assertNotIn('review_scope', self.q.status()['jobs'][0])

    def test_reverted_glossary_change_cancels_pending_scope_without_worker(self):
        self.scoped_fixture()
        self.write('glossary/glossary.csv', 'id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n')
        self.token = self.q.start()['token']
        self.write('glossary/glossary.csv', 'id,EN,target,category,JP,CN\n,Tower,Tháp,term,塔,塔\n')
        result = self.q.claim(self.token)
        self.assertTrue(result['stop'])
        self.assertEqual(self.q.status()['counts']['done'], 1)
        self.assertNotIn('review_scope', self.q.status()['jobs'][0])

    def test_character_target_change_uses_speaker_not_technical_id(self):
        for lang in ('EN', 'JP', 'CN'):
            path = self.root / self.scope / ('Test_' + lang + '.txt')
            self.write(path.relative_to(self.root), path.read_text(encoding='utf-8-sig') + '\ncharacter_123\n')
        self.write('glossary/glossary.csv', 'id,EN,target,category,JP,CN\n,Tower,Tháp,term,塔,塔\ncharacter_123,Name,Tên,character_name,名前,名\n')
        self.done('story')
        claim = self.scoped_claim('id,EN,target,category,JP,CN\n,Tower,Tháp,term,塔,塔\ncharacter_123,Name,Tên mới,character_name,名前,名\n')
        self.assertEqual(claim['job']['stage'], 'translate')
        self.assertEqual(claim['job']['review_scope']['blocks'], [1])

    def test_init_empty_idempotent(self):
        raw = self.q.path.read_bytes()
        self.assertFalse(self.q.init()["initialized"])
        self.assertEqual(raw, self.q.path.read_bytes())
        with self.assertRaises(ValueError): self.q.start()

    def test_explicit_recursion_and_dedup(self):
        with self.assertRaises(ValueError): self.q.enqueue([w.RESOURCE])
        self.source_set(w.RESOURCE + "/Other", "Test")
        self.assertEqual(self.q.enqueue([w.RESOURCE], True)["total"], 2)
        self.assertEqual(self.q.enqueue([self.scope])["added"], [])

    def test_path_escape(self):
        for path in ("../outside", w.RESOURCE + "/../outside", "D:/elsewhere"):
            with self.assertRaises(ValueError): self.q.enqueue([path])

    def test_missing_each_language(self):
        for lang in ("EN", "JP", "CN"):
            with self.subTest(lang=lang):
                path = self.root / self.scope / f"Test_{lang}.txt"
                raw = path.read_bytes(); path.unlink()
                claim = self.begin()
                self.assertTrue(claim["stop"])
                self.assertEqual(self.q.status()["counts"]["blocked"], 1)
                self.assertFalse((self.root / self.scope / "Test_Merge.txt").exists())
                path.write_bytes(raw)

    def test_source_warning_inside_valid_records(self):
        self.write(self.scope + "/Test_JP.txt", "valid\n[KHÔNG CÓ KHÓA TRONG NGUỒN JP]\nvalid")
        self.assertTrue(self.begin()["stop"])
        self.assertIn("JP", self.q.status()["jobs"][0]["error"])

    def test_no_language_source_warning(self):
        self.write(self.scope + "/Test_JP.txt", "KHÔNG CÓ NGUỒN JP TRONG PHẠM VI ĐÃ KIỂM")
        self.assertTrue(self.begin()["stop"])

    def test_language_declaration(self):
        self.write(self.scope + "/Test_EN.txt", "Test | JP | source\nhello")
        self.assertTrue(self.begin()["stop"])

    def test_game_warning_allowed(self):
        self.write(self.scope + "/Test_EN.txt", "ErrorCode\nWarning! Error ahead\n[EMPTY_SOURCE]")
        self.assertEqual(self.begin()["job"]["stage"], "merge")

    def test_valid_set_continues_after_invalid(self):
        self.source_set(self.scope, "A")
        (self.root / self.scope / "A_JP.txt").unlink()
        claim = self.begin()
        self.assertEqual(claim["job"]["base"], "Test")
        self.assertEqual(self.q.status()["counts"]["blocked"], 1)

    def test_static_full_cycle(self): self.done()
    def test_story_full_cycle(self): self.done("story")

    def test_term_stage_verified_save(self):
        proposals = [{"EN": "New Term", "JP": "", "CN": "", "context": "A name", "source_ref": "A/1"}]
        claim = self.inspect(proposals)
        self.assertEqual(claim["agent"]["model"], "gpt-6-luna")
        with self.assertRaises(ValueError):
            self.finish(claim, outcomes=[{"EN": "New Term", "target": "Từ mới", "status": "added"}])
        with (self.root / "glossary/glossary.csv").open("a", encoding="utf-8", newline="") as out:
            out.write(",New Term,Từ mới,term,,\r\n")
        self.finish(claim, outcomes=[{"EN": "New Term", "target": "Từ mới", "status": "added"}])
        self.assertEqual(self.q.claim(self.token)["job"]["stage"], "translate")

    def test_unresolved_term_can_continue(self):
        claim = self.inspect([{"EN": "Maybe", "JP": "", "CN": "", "context": "uncertain", "source_ref": "A/1"}])
        self.finish(claim, outcomes=[{"EN": "Maybe", "status": "unresolved", "reason": "Insufficient evidence"}])
        self.assertEqual(self.q.claim(self.token)["job"]["stage"], "translate")

    def test_duplicate_claim_and_stale_completion(self):
        claim = self.begin()
        self.assertTrue(self.q.claim(self.token)["wait"])
        self.q.stop(self.token, "Stopped worker")
        run = self.q.start()
        with self.assertRaises(ValueError): self.finish(claim, ui_type="static", term_proposals=[])
        self.assertNotEqual(self.token, run["token"])

    def test_recover_requires_explicit_flag(self):
        self.begin()
        with self.assertRaises(ValueError): self.q.start()
        run = self.q.start(recover=True)
        self.assertEqual(self.q.claim(run["token"])["job"]["stage"], "merge")

    def test_attempt_cap(self):
        claim = self.begin()
        for _ in range(2):
            self.q.fail(self.token, claim["job"]["id"], claim["job"]["claim"]["token"], "Worker failure")
            claim = self.q.claim(self.token)
        self.assertTrue(claim["stop"])
        self.assertEqual(self.q.status()["counts"]["failed"], 1)
        self.q.retry(self.q.status()["jobs"][0]["id"])
        self.assertEqual(self.q.status()["counts"]["pending"], 1)

    def test_item_budget(self):
        self.source_set(self.scope, "ZZ")
        claim = self.begin(max_items=1)
        path, _ = self.merge(claim)
        self.finish(claim, ui_type="static", term_proposals=[], snapshot_path=str(path))
        claim = self.q.claim(self.token)
        self.assertTrue(self.q.claim(self.token)["wait"])
        _, payload = self.merge(claim, "Translated")
        self.q.helper().run(self.root, payload)
        self.finish(claim)
        self.finish(self.q.claim(self.token))
        self.assertEqual(self.q.claim(self.token)["run"]["status"], "limited")

    def test_time_budget(self):
        self.begin()
        self.q.stop(self.token, "Stopped worker")
        run = self.q.start()
        original, state = self.q.read()
        state["run"]["deadline"] = "2000-01-01T00:00:00+00:00"
        self.q.save(original, state)
        self.assertEqual(self.q.claim(run["token"])["run"]["status"], "limited")

    def test_source_changed_during_stage(self):
        claim = self.begin()
        self.write(self.scope + "/Test_EN.txt", "Changed")
        with self.assertRaises(ValueError): self.finish(claim, ui_type="static", term_proposals=[])

    def test_relevant_glossary_change_requeues(self):
        self.done()
        self.write("glossary/glossary.csv", "id,EN,target,category,JP,CN\n,Tower,Tháp mới,term,塔,塔\n")
        self.q.start()
        self.assertEqual(self.q.status()["jobs"][0]["stage"], "translate")

    def test_unrelated_glossary_change_keeps_done(self):
        self.done()
        with (self.root / "glossary/glossary.csv").open("a", encoding="utf-8", newline="") as out:
            out.write(",Unrelated,Khác,term,,\r\n")
        self.q.start()
        self.assertEqual(self.q.status()["counts"]["done"], 1)

    def test_manual_vi_kept_and_requeued(self):
        job = self.done()
        path = self.root / job["merge_path"]
        self.write(job["merge_path"], path.read_text(encoding="utf-8-sig").replace("Tháp", "Bản hiệu đính"))
        raw = path.read_bytes()
        self.q.start()
        self.assertEqual(self.q.status()["jobs"][0]["stage"], "translate")
        self.assertEqual(raw, path.read_bytes())

    def test_missing_reports_stops(self):
        claim = self.through_merge()
        self.merge(claim, "Tháp")
        with self.assertRaises(ValueError): self.finish(claim)
        self.assertEqual(self.q.status()["run"]["status"], "needs_attention")
        self.assertEqual(self.q.status()["counts"]["done"], 0)

    def test_corrupt_report_prevents_next_translation(self):
        claim = self.begin()
        path, _ = self.merge(claim)
        self.finish(claim, ui_type="static", term_proposals=[], snapshot_path=str(path))
        self.write("reports/translation-conflicts.html", "corrupt")
        self.assertEqual(self.q.claim(self.token)["run"]["status"], "needs_attention")

    def test_source_changed_in_translated_merge_rejected(self):
        claim = self.through_merge()
        _, payload = self.merge(claim, "Tháp")
        path = self.root / claim["job"]["merge_path"]
        self.write(claim["job"]["merge_path"], path.read_text(encoding="utf-8-sig").replace("Tower", "Different"))
        payload["files"][0]["merge_sha256"] = w.digest(path.read_bytes())
        payload["files"][0]["blocks"][0]["source"]["EN"] = "Different"
        self.q.helper().run(self.root, payload)
        with self.assertRaises(ValueError): self.finish(claim)
        self.assertEqual(self.q.status()["counts"]["done"], 0)

    def test_corrupt_state_not_reset(self):
        self.q.path.write_bytes(b"corrupt")
        with self.assertRaises(ValueError): self.q.init()
        self.assertEqual(self.q.path.read_bytes(), b"corrupt")

    def test_merger_cannot_modify_glossary(self):
        claim = self.begin()
        path, _ = self.merge(claim)
        with (self.root / "glossary/glossary.csv").open("ab") as out: out.write(b",New,New,term,,\r\n")
        with self.assertRaises(ValueError):
            self.finish(claim, ui_type="static", term_proposals=[], snapshot_path=str(path))

    def test_snapshot_stale_hash_rejected(self):
        claim = self.begin()
        path, _ = self.merge(claim)
        with (self.root / claim["job"]["merge_path"]).open("ab") as out: out.write(b"changed")
        with self.assertRaises(ValueError): self.finish(claim, ui_type="static", term_proposals=[], snapshot_path=str(path))

    def test_changed_source_reopens_done(self):
        job = self.done()
        raw_merge = (self.root / job["merge_path"]).read_bytes()
        self.write(self.scope + "/Test_EN.txt", "Updated source")
        self.q.start()
        self.assertEqual(self.q.status()["jobs"][0]["stage"], "merge")
        self.assertEqual(raw_merge, (self.root / job["merge_path"]).read_bytes())

    def test_invalid_source_preserves_old_merge_and_glossary(self):
        path = self.write(self.scope + "/Test_Merge.txt", "Original manual VI")
        original = path.read_bytes()
        glossary = (self.root / "glossary/glossary.csv").read_bytes()
        self.write(self.scope + "/Test_CN.txt", "[KHÔNG CÓ KHÓA TRONG NGUỒN CN]")
        self.assertTrue(self.begin()["stop"])
        self.assertEqual(original, path.read_bytes())
        self.assertEqual(glossary, (self.root / "glossary/glossary.csv").read_bytes())

    def test_state_path_tampering_rejected(self):
        self.begin()
        original, state = self.q.read()
        state["jobs"][0]["sources"]["EN"] = w.RESOURCE + "/another.txt"
        self.q.save(original, state)
        with self.assertRaises(ValueError): self.q.status()

    def test_atomic_failure_preserves_previous_state(self):
        original = self.q.path.read_bytes()
        with patch.object(w.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError): self.q.enqueue([self.scope])
        self.assertEqual(self.q.path.read_bytes(), original)
        self.assertTrue(list(self.q.directory.glob("*.pending")))

    def finish_merge(self, claim, proposals=None):
        path, _ = self.merge(claim)
        return self.finish(claim, ui_type="static", term_proposals=proposals or [], snapshot_path=str(path))

    def finish_translation(self, claim):
        _, payload = self.merge(claim, "VI")
        self.q.helper().run(self.root, payload)
        return self.finish(claim)

    def add_lookahead(self):
        self.source_set(self.scope, "ZZ1")
        self.source_set(self.scope, "ZZ2")

    @staticmethod
    def proposal(en="New Term"):
        return [{"EN": en, "JP": "", "CN": "", "context": "Named concept", "source_ref": "A/1"}]

    def test_pipeline_holds_terms_and_third_merge_until_verify(self):
        self.add_lookahead()
        translator_a = self.through_merge()
        merger_b = self.q.claim(self.token)
        self.assertEqual(merger_b["job"]["base"], "ZZ1")
        self.assertEqual(self.q.status()["counts"]["running"], 2)
        self.finish_merge(merger_b, self.proposal())
        self.assertTrue(self.q.claim(self.token)["wait"])
        self.finish_translation(translator_a)
        verify_a = self.q.claim(self.token)
        self.assertEqual(verify_a["job"]["stage"], "verify")
        self.assertTrue(self.q.claim(self.token)["wait"])
        self.finish(verify_a)
        terms_b = self.q.claim(self.token)
        self.assertEqual(terms_b["job"]["stage"], "terms")
        self.assertTrue(self.q.claim(self.token)["wait"])
        self.finish(terms_b, outcomes=[{"EN": "New Term", "status": "unresolved", "reason": "No matching concept"}])
        translator_b = self.q.claim(self.token)
        merger_c = self.q.claim(self.token)
        self.assertEqual(translator_b["job"]["base"], "ZZ1")
        self.assertEqual(translator_b["job"]["stage"], "translate")
        self.assertEqual(merger_c["job"]["base"], "ZZ2")
        self.assertEqual(merger_c["job"]["stage"], "merge")

    def test_no_term_lookahead_still_blocks_third_merge(self):
        self.add_lookahead()
        translator_a = self.through_merge()
        self.finish_merge(self.q.claim(self.token))
        self.assertTrue(self.q.claim(self.token)["wait"])
        self.finish_translation(translator_a)
        self.finish(self.q.claim(self.token))
        self.assertEqual(self.q.claim(self.token)["job"]["base"], "ZZ1")
        self.assertEqual(self.q.claim(self.token)["job"]["base"], "ZZ2")

    def test_incomplete_active_merge_edit_does_not_invalidate_claim(self):
        self.add_lookahead()
        translator_a = self.through_merge()
        self.merge(translator_a, "Partial VI")
        self.q.claim(self.token)
        current = next(j for j in self.q.status()["jobs"] if j["base"] == "Test")
        self.assertEqual(current["claim"]["token"], translator_a["job"]["claim"]["token"])
        self.assertEqual(current["status"], "running")

    def test_report_failure_preserves_concurrent_merger_checkpoint(self):
        self.add_lookahead()
        translator_a = self.through_merge()
        merger_b = self.q.claim(self.token)
        self.merge(translator_a, "VI")
        with self.assertRaises(ValueError): self.finish(translator_a)
        self.finish_merge(merger_b, self.proposal())
        self.assertEqual(self.q.status()["run"]["status"], "needs_attention")
        b = next(j for j in self.q.status()["jobs"] if j["base"] == "ZZ1")
        self.assertEqual(b["stage"], "terms")
        self.assertIn("merge", b["checkpoints"])
        with self.assertRaises(ValueError): self.q.claim(self.token)

    def test_recover_two_live_claims_and_reject_both_old_tokens(self):
        self.add_lookahead()
        a = self.through_merge()
        b = self.q.claim(self.token)
        run = self.q.start(recover=True)
        old_token = self.token
        self.token = run["token"]
        self.assertNotEqual(old_token, self.token)
        with self.assertRaises(ValueError): self.finish(a)
        with self.assertRaises(ValueError): self.finish_merge(b)
        self.assertEqual(self.q.claim(self.token)["job"]["stage"], "translate")
        self.assertEqual(self.q.claim(self.token)["job"]["stage"], "merge")

    def test_glossary_update_goes_directly_to_translator(self):
        self.write("glossary/glossary.csv", "id,EN,target,category,JP,CN\n")
        terms = self.inspect(self.proposal("Tower"))
        merge_bytes = (self.root / terms["job"]["merge_path"]).read_bytes()
        self.write("glossary/glossary.csv", "id,EN,target,category,JP,CN\n,Tower,VI,term,,\n")
        self.finish(terms, outcomes=[{"EN": "Tower", "status": "added", "target": "VI"}])
        translator = self.q.claim(self.token)
        self.assertEqual(translator["job"]["stage"], "translate")
        self.assertEqual(merge_bytes, (self.root / terms["job"]["merge_path"]).read_bytes())

    def test_term_controller_is_exclusive(self):
        self.add_lookahead()
        terms = self.inspect(self.proposal())
        self.assertEqual(terms["job"]["stage"], "terms")
        self.assertTrue(self.q.claim(self.token)["wait"])
        self.assertEqual(self.q.status()["counts"]["running"], 1)

    def test_expired_budget_drains_workers_without_invalidating_claims(self):
        self.add_lookahead()
        translator = self.through_merge()
        merger = self.q.claim(self.token)
        original, state = self.q.read()
        state["run"]["deadline"] = "2000-01-01T00:00:00+00:00"
        self.q.save(original, state)
        self.assertTrue(self.q.claim(self.token)["wait"])
        self.finish_translation(translator)
        self.finish_merge(merger)
        self.assertEqual(self.q.claim(self.token)["run"]["status"], "limited")
        self.assertEqual(self.q.status()["counts"]["running"], 0)

    def test_migration_preserves_history_and_does_not_invent_merge(self):
        claim = self.begin()
        self.q.stop(self.token, "Workers stopped")
        original, state = self.q.read()
        state["schema_version"] = 1
        job = state["jobs"][0]
        job["stage"] = "inspect"
        job["checkpoints"] = {"inspect": {"summary": "legacy inspected"}, "terms": {"summary": "legacy terms applied"}}
        self.q.save(original, state)
        with self.assertRaises(ValueError): self.q.start()
        self.assertTrue(self.q.migrate()["migrated"])
        job = self.q.status()["jobs"][0]
        self.assertEqual(job["stage"], "merge")
        self.assertEqual(job["checkpoints"], {})
        self.assertIn("terms", job["legacy_checkpoints"])
        self.assertFalse((self.root / job["merge_path"]).exists())
        self.assertFalse(self.q.migrate()["migrated"])

    def test_migration_refuses_live_v1_run(self):
        self.begin()
        original, state = self.q.read()
        state["schema_version"] = 1
        self.q.save(original, state)
        with self.assertRaises(ValueError): self.q.migrate()

    def test_state_file_excludes_inspect_in_v2(self):
        self.begin()
        original, state = self.q.read()
        state["jobs"][0]["stage"] = "inspect"
        self.q.save(original, state)
        with self.assertRaises(ValueError): self.q.status()

    def test_vi_term_change_does_not_reset_retry_counter_forever(self):
        self.done()
        self.write("glossary/glossary.csv", "id,EN,target,category,JP,CN\n,Tower,New VI,term,,\n")
        run = self.q.start()
        self.token = run["token"]
        claim = self.q.claim(self.token)
        self.assertEqual(claim["job"]["stage"], "translate")
        for _ in range(2):
            self.q.fail(self.token, claim["job"]["id"], claim["job"]["claim"]["token"], "Worker could not finish")
            claim = self.q.claim(self.token)
        self.assertTrue(claim["stop"])
        self.assertEqual(self.q.status()["counts"]["failed"], 1)

    def test_manual_vi_edit_does_not_reset_retry_counter_forever(self):
        job = self.done()
        path = self.root / job["merge_path"]
        self.write(job["merge_path"], path.read_text(encoding="utf-8-sig").replace("Tháp", "Manual VI"))
        run = self.q.start()
        self.token = run["token"]
        claim = self.q.claim(self.token)
        for _ in range(2):
            self.q.fail(self.token, claim["job"]["id"], claim["job"]["claim"]["token"], "Worker could not finish")
            claim = self.q.claim(self.token)
        self.assertTrue(claim["stop"])
        self.assertEqual(self.q.status()["counts"]["failed"], 1)

    def test_claim_does_not_read_glossary_while_term_writer_is_active(self):
        self.add_lookahead()
        self.inspect(self.proposal())
        # A direct writer may have a temporary incomplete CSV; claim must only wait.
        with patch.object(self.q, 'glossary', side_effect=AssertionError('concurrent glossary read')):
            self.assertTrue(self.q.claim(self.token)['wait'])

    def test_merge_claim_does_not_read_report_pair_while_translator_writes(self):
        self.done()
        self.add_lookahead()
        self.q.enqueue([self.scope])
        self.token = self.q.start()['token']
        merger_b = self.q.claim(self.token)
        self.finish_merge(merger_b)
        translator_b = self.q.claim(self.token)
        self.assertEqual(translator_b['job']['stage'], 'translate')
        # Pair replacement is two files: a reader must not observe the midpoint.
        with patch.object(self.q, 'checked_reports', side_effect=AssertionError('concurrent pair read')):
            merger_c = self.q.claim(self.token)
        self.assertEqual(merger_c['job']['stage'], 'merge')
        self.assertEqual(self.q.status()['counts']['running'], 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=PROJECT)
    args, remaining = parser.parse_known_args()
    PROJECT = args.project_root.resolve()
    unittest.main(argv=[__file__, *remaining])
