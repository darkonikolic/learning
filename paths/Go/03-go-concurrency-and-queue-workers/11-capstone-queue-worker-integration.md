# Unit 11 — Capstone integration: disciplined `queue-worker/` journey

Compose features holistically—not isolated toys:

```
producer emits → bounded buffer/channel → worker pool draining
context cancellation/timeouts cooperating
shutdown discipline narrated plainly
race detector cleanliness targets (no knowingly ignored diagnostics)
```

## Fault injection arcs (ethical “break then heal” rehearsal)

Produce **alternate scratch branches or tagged commits capturing intentional pathologies**:

| pathology | pedagogical payoff |
|-----------|---------------------|
| **deadlock** | lock/channel ordering cognition |
| **goroutine leak** | forgotten join / ignoring cancellation |
| **data race** | detector literacy + refactor |

Heal each cleanly documenting **cause → structural fix rationale**—“because sleep(10ms) waved problem away” disqualifies academically.

Interview consolidation emphasises:

```
goroutines • channels (+buffering contrasts) • mutex • select contexts
timeouts • cancellations • `-race` • worker pooling • graceful shutdown choreography
```

## Deliverables

 runnable reference path README chunk emphasising WHY boundaries chosen—not merely command invocation screenshots.
