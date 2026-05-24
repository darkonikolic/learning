# Unit 02 — B-tree mental model: ordering, ranges, sabotaged predicates

Index on `created_at`; query rolling windows (`created_at >= …`).

Highlight why leading wildcards (`LIKE '%token%'`) sabotage typical B-tree seek usage.

Lab: predict plan shape, confirm with `EXPLAIN` (version-specific column naming—note your server).

Interview: complexity comparison scan vs seek; selective range vs ambiguous pattern matching.
