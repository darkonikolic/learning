# Unit 7 — Production incident triage scripting (latency + errors + resource pressure)

Incident recipe:

```
Start from user-visible symptom
Query metrics hypotheses (SATURATION? ERRORS?)
Drill traces for slow spans
Align logs via correlation identifiers
Iterate until single dominant factor emerges OR honest multi-factor story accepted
```

## Deliverable

Template you can reuse: fields for timeline, hypotheses, proofs, rollout.

Practice with synthetic DB slowdown + retry amplification scenario.
