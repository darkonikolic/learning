# Replication lag & read replica routing consistency

**Theme:** Replica reads are eventually consistent **unless proven otherwise.**

### Contracts

Declare per endpoint: **PRIMARY only** • **eventually OK with lag SLA** • **monotonic read hacks** where needed (`read-after-write` bridging strategies).

Expose **seconds behind** (& appropriate equivalent)—not only dashboards but **routing policy**.

### Incident class

Stale balance / stale authorization cache style bugs—tie to **verification pattern** (`37` JWT/session overlap awareness).
