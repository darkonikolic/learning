# Unit 1 — Durable workflows & Temporal-style engines (conceptual)

> **Bridging cadence cue:** about three–four thematic blocks once distributed motifs feel grounded—numbering is topic order, not a timetable.

Queues and hand-rolled sagas handle plenty of workloads. They become painful when work is **long-running**, crosses **slow humans or partners**, accumulates complex **retry + compensation graphs**, or must survive **process crashes** without losing deterministic progress bookkeeping.

Engines such as **Temporal** (conceptual label here—confirm vendor docs/SLO realities before organisational adoption commitments) elevate ideas like:

```
workflow = durable state machine coordinating activities
activities = retries/timeout/compensation wrappers around side-effects
replayable histories reconstructing unfinished work after outages
```

## Positioning prompts (write answers, not trivia)

Contrast three recovery owners for staged failures (`payment authorised`, `inventory commit fails shipping prep`, `cancellation requested mid-flight`) under:

| Approach | Strengths | Pain you accept |
|-----------|-----------|----------------|
| Bounded queue choreography | simplicity, clear operational story | brittle state bookkeeping if durations stretch |
| Hand-rolled saga/orchestration | maximal control code-side | sprawling logic + divergence across teams unless disciplined |
| Durable workflow engine | explicit timelines + deterministic replay story | infra/operational sophistication + deterministic workflow code obligations |

Add:

1. A short **sequence sketch** for `payment → inventory → shipping`, with inventory failing and a compensation/refund arc.
2. For each ambiguity class (**timeout unsure**, **duplicate retry**, **late success after cancel**), name the **stored source of truth** (table/state/history/event) your design relies on—as you would defend it in review.
3. One closing paragraph naming when a workflow engine’s **replay/determinism** obligations outweigh the operational overhead, versus staying with queues + explicit sagas.
