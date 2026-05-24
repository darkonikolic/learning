# Partitioning, sharding tradeoffs & hot partitions

### Partition strategy heuristics

Range vs hash vs list—**replay / bulk export** ergonomics—not only write spread.

### Sharding realism

Operational tax: migrations, resharding dramas, transactional boundaries—**explicit non-goals** when deferring shards.

### Hot partition detection

Key skew metrics, monitoring tail latency per shard hypothetical—document **safeguard dashboards** you'd add before admitting multi-tenant growth.
