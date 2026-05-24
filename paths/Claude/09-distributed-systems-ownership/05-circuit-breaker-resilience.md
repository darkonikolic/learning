# Circuit breaker — service protection

**Theme:** Isolate **upstream dependency failure** before it melts your thread pools, wallets, or customer trust.

Stateful guard mental model:

```
 healthy / closed  → sustained failures breach threshold →  OPEN (fast-fail shields)
OPEN timer elapses probing success → HALF-OPEN exploratory calls
confidence regained → recover / CLOSED
```

### Design probes

Failure classification: deterministic 4xx vs transient overload vs partner outage—**circuit policy differs**.

Half-open probing must remain **economical** — no thundering herd re-open storms.

Cascade containment pairs with timeouts, sane thread budgets, graceful degradation payloads.

### Checklist

- [ ] Fallback path semantics explicit (hard fail vs cached stale snapshot vs degraded read).  
