# Unit 2 — Labs: edge failure, purge discipline, and multi-layer cache coherence

## Lab A — failure at edge

CDN partial outage or misconfiguration: narrate user-visible symptoms + monitoring triage + fallback (origin load spike ethics).

## Lab B — purge choreography

Design safe purge for **price change** vs **legal takedown** urgency difference—show policy table.

## Lab C — multi-layer cache story

Stack browser → CDN → app cache → DB read path: document **staleness budget** per layer & who owns invalidation truth.

## Trade-off matrix

| Strategy | Operationally cheap? | Staleness risk | Notes |
|----------|----------------------|----------------|-------|
| Long CDN TTL + rare purge | | | |
| Short TTL + low purge | | | |
| Surrogate key / tag purge (conceptual) | | | |

