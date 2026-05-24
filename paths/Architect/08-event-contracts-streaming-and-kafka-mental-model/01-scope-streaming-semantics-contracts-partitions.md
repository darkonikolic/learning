# Unit 1 — Scope: event contracts & streaming semantics (Kafka mental model)

## Log vs mailbox intuition

Logs with retention enable **replay** and auditable timelines; classic queues emphasise transient handoff—the operational and compliance calculus differs materially.

## Partitions & ordering

Use **partition keys** deliberately for correlated timelines. Ordering is strongest **within** a partition, not globally. Hot keys imply skew risk.

## Consumer groups & rebalancing

Deployments and scaling shift partition assignments briefly—consumers remain **duplicate-tolerant**.

## Delivery posture

Default **at-least-once** mental model unless dedupe artefacts exist (inbox/idempotent writes).

## Failure classes

Name policies for poison messages, partition stalls, and controlled replays—with safety around money-moving flows.

