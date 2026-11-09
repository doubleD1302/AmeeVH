-- Apply once to an existing v1 D1 database before deploying the v2 Worker.
CREATE TABLE IF NOT EXISTS dataset_state (
 id INTEGER PRIMARY KEY CHECK(id=1), version TEXT NOT NULL, phase TEXT NOT NULL CHECK(phase IN ('open','locked','publishing')),
 manifest_hash TEXT, updated_at TEXT NOT NULL, updated_by TEXT NOT NULL
);
INSERT OR IGNORE INTO dataset_state(id,version,phase,manifest_hash,updated_at,updated_by) VALUES(1,'legacy-1','open',NULL,datetime('now'),'migration');
CREATE TABLE IF NOT EXISTS dataset_events (
 id TEXT PRIMARY KEY, old_version TEXT NOT NULL, new_version TEXT NOT NULL, old_phase TEXT NOT NULL, new_phase TEXT NOT NULL,
 manifest_hash TEXT, actor TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, session_hash TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
ALTER TABLE proposals ADD COLUMN user_id TEXT;
ALTER TABLE proposals ADD COLUMN dataset_version TEXT;
ALTER TABLE proposals ADD COLUMN updated_at TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS proposals_one_per_user_version ON proposals(chapter_id,line_id,dataset_version,user_id) WHERE user_id IS NOT NULL;
UPDATE collaboration_meta SET value='2' WHERE key='schema_version';
