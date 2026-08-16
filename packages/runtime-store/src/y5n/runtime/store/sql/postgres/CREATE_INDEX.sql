CREATE INDEX IF NOT EXISTS idx_index_lookup
ON index_entries(domain, kind, space, index_key, value, entity_id);