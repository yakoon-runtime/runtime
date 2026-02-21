-- Yakoon Session Schema: Initial Structure

CREATE TABLE IF NOT EXISTS sessions (
    __key__ TEXT PRIMARY KEY,
    __scope__ TEXT,
    __created_at__ TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lang TEXT,
    data TEXT,
    last_active TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_scope ON sessions (__scope__);
CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions (last_active);

-- Shards

CREATE TABLE IF NOT EXISTS shards (
    prefix TEXT NOT NULL,
    shard_id INTEGER NOT NULL,
    range_start INTEGER NOT NULL,
    range_end INTEGER NOT NULL,
    value INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (prefix, shard_id),
    CHECK (range_start < range_end),
    CHECK (value >= 0)
);
