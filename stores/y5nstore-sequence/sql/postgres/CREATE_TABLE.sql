CREATE TABLE id_shards (
    prefix TEXT,
    shard_id BIGINT,
    range_start BIGINT NOT NULL,
    range_end BIGINT NOT NULL,
    value BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (prefix, shard_id)
);
