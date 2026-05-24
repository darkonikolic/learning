# Unit 08 — Operational anti-pattern catalogue remediation

Practice repairing:

Broad star projections.

Wildcard middle patterns.

Datetime functions sabotaging predicates (`WHERE YEAR(created_at)=…` rewritten to sane ranges).

N+1 application shapes (conceptual synergy with Phase 04 deeper unit).

Shoot for ~15 rewrites annotated with rationale.

Interview link: predicate sargability, index alignment.
