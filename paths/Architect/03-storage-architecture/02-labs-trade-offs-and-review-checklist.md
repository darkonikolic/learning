# Unit 2 — Labs, trade-offs, readiness checklist

## Design labs (minimum three documented)

Author short studies:

1. **Replication + read scaling** posture for read-heavy dashboards vs authoritative writes—state staleness UI expectations explicitly.
2. **Partitioning / sharding trigger** analysis: when single-node limits vs operational tax justifies split—include cross-shard query pain honesty.
3. **Backup/restore rehearsal narrative** (even tabletop): RPO/RTO targets + failure injection story.

## Trade-off matrix (template)

| Decision | Gain | Cost | Kill criteria (when you’d undo) |
|----------|------|------|----------------------------------|
| Add read replica | | | |
| Introduce caching layer | | | |
| Shard by tenant | | | |

## Interview rehearsal

Explain **one** storage choice you’d delay until metrics prove necessity—name the metric.
