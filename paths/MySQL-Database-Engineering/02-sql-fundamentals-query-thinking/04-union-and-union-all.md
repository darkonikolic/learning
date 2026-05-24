# Unit 04 — UNION vs UNION ALL semantics

Practice combining heterogeneous slices—for example partitioned yearly order tables (`orders_2025`, `orders_2026`) mocked in sandbox.

Goals:

- Harmonise column signatures.
- Decide when duplicate elimination (`UNION`) costs extra work vs `UNION ALL` fidelity.

Lab: Produce combined reporting totals and explain duplication handling strategy.

Interview: performance implication of DISTINCT pass inside UNION, and when uniqueness is logically guaranteed beforehand.
