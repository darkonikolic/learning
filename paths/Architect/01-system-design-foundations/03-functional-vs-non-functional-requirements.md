# Unit 3 — Functional vs non-functional requirements (measurable envelopes)

Senior engineers ship features—architects keep **measurable NFR envelopes** aligned with risk.

Contrast deliberately:

```
Functional behaviours  (capabilities users/companies visibly obtain)
Non-functional envelopes (latency, uptime, correctness under concurrency, auditability, sovereignty…)
Trade-off ledger        (what improving one NFR costs another dimension)
```

## Practice

For a representative HTTP API (Symfony monolith acceptable), produce three parallel lists:

1. Functional requirements (atomic, testable statements).
2. Non-functional requirements with **numbers** (even rough).
3. Trade-off notes where numbers conflict (cost vs latency vs complexity).

## Interview drill

Name one NFR you would **not** promise on day one—and the **metric** that would force reopening the decision.
