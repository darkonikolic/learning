# Unit 10 — Final staff-style lab: `payment-platform/` under composite failures

Inject simultaneously (or staged if overwhelmed—document staging honestly):

```
duplicate payment attempts
timeouts & ambiguous responses
queue backlog growth
goroutine leak
CPU pegged profile
latency SLO breach symptoms
worker slowdown
```

You must produce **one consolidated incident report** including:

```
problem statement
symptoms timeline
investigation evidence (race? pprof? metrics? traces? logs?)
root cause(s)
fix + trade-offs
prevention / guardrails
```

Explicitly cross-link reasoning to earlier areas (concurrency, distributed, prod, perf) in the narrative—this is integration of *thinking*, not isolated trivia.
