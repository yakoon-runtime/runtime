-- current state
CREATE TABLE current (
  domain TEXT,
  kind TEXT,
  space TEXT,
  entity_id TEXT,
  rev INT,
  data JSONB,
  updated_at TIMESTAMPTZ,
  PRIMARY KEY (domain, kind, space, entity_id)
);

-- revisions (append-only)
CREATE TABLE revisions (
  domain TEXT,
  kind TEXT,
  space TEXT,
  entity_id TEXT,
  rev INT,
  ts TIMESTAMPTZ,
  patch JSONB,
  patch_format TEXT,
  PRIMARY KEY (domain, kind, space, entity_id, rev)
);

-- index specs
CREATE TABLE index_specs (
  domain TEXT,
  kind TEXT,
  space TEXT,
  key TEXT,
  value_type TEXT,
  unique_flag BOOLEAN,
  PRIMARY KEY (domain, kind, space, key)
);

-- index values
CREATE TABLE index_entries (
  domain TEXT,
  kind TEXT,
  space TEXT,
  index_key TEXT,
  value TEXT,
  entity_id TEXT,
  written_at TIMESTAMPTZ
);