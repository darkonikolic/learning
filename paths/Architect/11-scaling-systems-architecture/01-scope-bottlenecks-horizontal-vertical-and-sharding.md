# Unit 1 — Scope: scaling the bottleneck that actually binds you

Bridging roadmap intent (**scaling**) with storage/replication realism from earlier areas.

Identify what saturates: **CPU, IO, connection pools, contention, egress, queue backlog, organisational deploy cadence** — scale the causal axis first.

Articulate horizontal vs vertical trade-offs honestly; separate **mostly stateless tiers** vs **sticky or strongly consistent subsystems**.

Read replicas help read-heavy dashboards—budget **staleness UX** consciously.

Sharding unlocks partitioned growth—accept **cross-shard correctness tax** consciously early.

