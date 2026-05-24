# Unit 2 — Labs: invalidation, staleness budgeting, outages

Produce **three** mini designs (each with diagram bullets + explicit trade-off):

## Lab A — Product catalogue freshness

Invalidate or TTL when price/stock volatility matters; define staleness tolerated by UX.

## Lab B — Abuse / thundering herd

Sketch stampede mitigation (singleflight-style thinking, probabilistic TTL jitter, guarded refresh) tied to observable metrics.

## Lab C — Operational failure

Warm cache vanished after deploy/cluster restart—articulate graceful degradation posture + warm-up choreography optionality ethically scoped.

## Interview drill

Articulate **`cache-aside` vs write-through`** with one scenario each where you’d veto the other—even if politely.

