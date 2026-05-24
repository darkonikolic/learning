# Unit 2 — Worker pipelines: fan-out / fan-in + backpressure awareness

Elevate pooling toward pipeline topology:

```
source → replicated workers (fan-out) → aggregation join (fan-in)
```

## Learning outcomes

Maintain **explicit backpressure**:

- Bounded intermediate channels preventing unbounded intermediary memory explosion when stages skew rates.

Enumerate completion signalling strategies preventing aggregator goroutine stalls silently.

Practice sketch—even if artificially small dataset—articulating hypothetical metrics hooking placeholders for future Prometheus instrumentation bridging ops mindset elsewhere in vault optionally.

Interview lenses map to enterprise throughput debugging stories verbally even if hypothetical.

## Acceptance criteria checklist

 Narrative diagram (ASCII permissible) illustrating data motion + choke points—not single mystery function monolith intangible.
