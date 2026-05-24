# Unit 8 — Capstone narration: payment → verified event emission → inventory reaction

Produce written architecture & sequence justification (diagram optional) practising earlier motifs—not necessarily full infra cluster fidelity now.

Mandatory reasoning hooks (tick each explicitly in prose):

```
transactional persistence + outbox (or explicit refusal with compensating design + risks stated)
partitioning key coherence vs hotspots / skew honesty
inbox / idempotent consumer interplay OR alternative dedupe discipline stated
bounded retries vs poison isolation + replay governance story
Lag / backlog ageing metrics intuition (even if dashboards are stubs)
RabbitMQ vs Kafka trade matrix from your Areas 12 ↔ 14 story—no slogan absolutism
```

Deliver **short design note** citing:

| Section | Requirement |
|---------|--------------|
| Data path | Payment commit → emission → inventory acknowledgement. |
| Failure modes | Poison, duplication, partitioning skew, saga compensation tie-in at least verbally. |
| Interview compare | Structured bullet **RabbitMQ vs Kafka** without absolutism—state operational triggers choosing each. |

Oral rehearsal: summarise end-to-end in ≤3 minutes calmly staff-style.

