# Unit 10 — JSON / hot-path serialization performance benching (`encoding/json` first)

Bench:

```
small structs vs medium vs large payloads
Decoder reuse vs naive patterns where applicable thoughtfully
alternative codecs only as optional appendix if curious—maintain honesty verifying semantics compatibility trade-offs consciously
```

## Lab

Document where JSON becomes bottleneck vs database/network overshadowing guesses—articulate investigative question ordering for “slow endpoints” bridging next latency ownership unit.

Interview focus: schema shape & field count ripple effects—not just “JSON slow” slogans.
