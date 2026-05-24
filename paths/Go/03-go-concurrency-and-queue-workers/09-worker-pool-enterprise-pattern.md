# Unit 9 — Worker pool structuring: amortise goroutines deliberately

Corporate Go systems rarely spawn unbounded ephemeral goroutines for each remote event—economics degrade under fan-in storms.

Prefer **bounded worker goroutine set** draining shared job intake channel responsibly.

Practice assignment:

Design **email-ish sender** analogue:

```
1000 jobs total
≤ 5 simultaneous active workers draining queue
shutdown waits in-flight politely honoring context cancellation tightening
```

## Learning outcomes articulated

Enumerate **graceful draining** choreography:

- cease accepting inbound,
- cooperative completion,
- join / wait layering.

Articulate **`backpressure`**: sluggish workers imply queue growth—eventually producers must choke, throttle, or shed load—explicit policy decision not accidental memory ballooning unnoticed.

## Interview prompts

Sizing worker pools via metrics-informed loops vs arbitrary constants—risk articulation.

When pool too small induces SLA misses vs oversized spinning idle CPU waste.
