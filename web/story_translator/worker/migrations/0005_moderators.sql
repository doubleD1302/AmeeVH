-- Per-person Moderator codes.
-- ALREADY APPLIED on the live D1 database (tramvh-collaboration). It is recorded here so a fresh
-- database can be rebuilt; do NOT run it again on live (the ALTER TABLE statement would fail).
-- schema.sql already contains the final shape for new databases.
CREATE TABLE IF NOT EXISTS moderator_codes (
 id TEXT PRIMARY KEY, code_hash TEXT NOT NULL UNIQUE, label TEXT NOT NULL,
 bound_name TEXT, bound_name_norm TEXT, created_by TEXT NOT NULL, created_at TEXT NOT NULL,
 claimed_at TEXT, revoked_at TEXT, code_cipher TEXT
);
ALTER TABLE users ADD COLUMN moderator_code_hash TEXT;
