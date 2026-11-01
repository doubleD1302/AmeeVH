PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS lines (
 chapter_id TEXT NOT NULL, line_id TEXT NOT NULL, en TEXT NOT NULL, source_hash TEXT NOT NULL,
 new_vi TEXT NOT NULL DEFAULT '', translator TEXT NOT NULL DEFAULT '', status TEXT NOT NULL CHECK(status IN ('untranslated','pending','approved','needs_review','machine_pending')),
 translation_origin TEXT NOT NULL DEFAULT 'unknown' CHECK(translation_origin IN ('human','machine','unknown')),
 notes TEXT NOT NULL DEFAULT '', revision INTEGER NOT NULL DEFAULT 0 CHECK(revision>=0), updated_at TEXT,
 approved_by TEXT, approved_at TEXT, legacy_status TEXT, provenance TEXT NOT NULL DEFAULT 'legacy_import',
 PRIMARY KEY(chapter_id,line_id)
);
CREATE TABLE IF NOT EXISTS proposals (
 id TEXT PRIMARY KEY, chapter_id TEXT NOT NULL, line_id TEXT NOT NULL, text_vi TEXT NOT NULL,
 translator TEXT NOT NULL, origin TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', reason TEXT NOT NULL, reason_detail TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','accepted','rejected')),
 base_revision INTEGER NOT NULL, base_source_hash TEXT NOT NULL, base_text TEXT NOT NULL,
 reviewed_by TEXT, reviewed_at TEXT,
 FOREIGN KEY(chapter_id,line_id) REFERENCES lines(chapter_id,line_id)
);
CREATE INDEX IF NOT EXISTS proposals_line ON proposals(chapter_id,line_id,state,created_at);
CREATE TABLE IF NOT EXISTS history (
 id TEXT PRIMARY KEY, chapter_id TEXT NOT NULL, line_id TEXT NOT NULL, event_type TEXT NOT NULL,
 actor TEXT NOT NULL, created_at TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '',
 old_text TEXT NOT NULL, new_text TEXT NOT NULL, old_status TEXT NOT NULL, new_status TEXT NOT NULL,
 revision INTEGER NOT NULL, source_hash TEXT NOT NULL, snapshot_json TEXT NOT NULL,
 FOREIGN KEY(chapter_id,line_id) REFERENCES lines(chapter_id,line_id)
);
CREATE INDEX IF NOT EXISTS history_line ON history(chapter_id,line_id,revision DESC,id DESC);
CREATE TABLE IF NOT EXISTS operations (
 request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, nonce TEXT NOT NULL,
 chapter_id TEXT NOT NULL, line_id TEXT NOT NULL, result_kind TEXT NOT NULL, proposal_id TEXT,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS operations_line ON operations(chapter_id,line_id,created_at);
CREATE TABLE IF NOT EXISTS collaboration_meta (key TEXT PRIMARY KEY,value TEXT NOT NULL);
INSERT OR IGNORE INTO collaboration_meta(key,value) VALUES('schema_version','1');
