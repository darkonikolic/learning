# Unit 4 — Capacity estimation: back-of-envelope numbers that prevent fantasy designs

Use explicit toy scenario from source:

```
100k users • 10 req/s • 1 MB payload • 30-day retention window (example only)
```

Derive defensible **orders-of-magnitude** for:

```
storage growth
egress / ingress bandwidth attention points
database row & index pressure intuition
```

Document assumptions table (peak factor, compression, dedupe, replication multipliers).

## Lab deliverable

One-page calculation sheet + **sensitivity table** (“if payload 2× larger, what breaks first?”).
