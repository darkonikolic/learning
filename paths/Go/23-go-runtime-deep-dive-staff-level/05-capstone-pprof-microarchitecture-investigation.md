# Unit 5 — Capstone: micro-architecture suspicion → evidence → guarded change

Compose a single performance mystery in `perf-lab/` with **plausible** confusion between:

```
lock contention vs false sharing vs allocation/GC noise vs scheduler wait (use trace)
```

You must:

```
form alternate hypotheses explicitly
select minimal measurement to falsify each (CPU profile, heap profile, trace, race if relevant)
pick the smallest behavioural change with before/after artefacts
document trade-offs (readability, API shape, pooling hazards)
```

Interview rehearsal: defend your decision path in ≤4 minutes without tooling open—prove you internalised the investigative recipe from Areas `15`–`16` and this staff unit.
