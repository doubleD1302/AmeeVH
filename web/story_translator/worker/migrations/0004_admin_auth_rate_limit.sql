-- Apply after the admin portal export migration.
CREATE TABLE IF NOT EXISTS admin_auth_attempts (
 key_hash TEXT PRIMARY KEY, failures INTEGER NOT NULL DEFAULT 0,
 window_started TEXT NOT NULL, locked_until TEXT
);
