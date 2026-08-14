-- id shards (sequencer)
CREATE TABLE IF NOT EXISTS id_shards (
  prefix TEXT,
  shard_id INT,
  range_start BIGINT,
  range_end BIGINT,
  value BIGINT,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (prefix, shard_id)
);
