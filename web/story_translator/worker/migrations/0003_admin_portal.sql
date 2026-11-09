-- Apply once after the collaboration v2 migration.
CREATE TABLE IF NOT EXISTS admin_exports (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('snapshot','delta','handoff')),
 chapter_id TEXT NOT NULL, dataset_version TEXT NOT NULL, base_export_id TEXT,
 created_by TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ready',
 manifest_json TEXT NOT NULL, files_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS admin_exports_scope ON admin_exports(chapter_id,created_at DESC);
