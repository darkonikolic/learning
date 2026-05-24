# Unit 1 — Scope: workflows & orchestration beyond “HTTP callback hope”

## Intent

Represent **multi-step** business journeys (order → payment → inventory → shipping) that span **network partitions**, **ambiguous RPC answers**, **human approvals**, **retries**.

## Architectural primitives

- **Step boundaries**: side-effectful work isolated with explicit retry/timeout envelopes.
- **Checkpoints**: enough durable state survives process death—you don’t “remember progress” only inside RAM.
- **Compensations**: partial success arcs may require reversing earlier steps asymmetrically honestly (refunds/restores—not always automatic SQL rollback).
- **Observability**: workflow IDs + correlated traces/logs/metrics bridging incident triage.

## Positioning honesty

Heavyweight workflow engines excel when histories & replay ergonomics amortise sprawling hand-rolled sagas—but they bring **operational and coding discipline costs** too. Decide with evidence—not résumé keywords.

