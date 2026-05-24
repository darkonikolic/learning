# Unit 04 — Temporary tables surfaced in plans

Observe `GROUP BY` operations elevating temporary storage or memory pressure (`Using temporary` in legacy `EXPLAIN` extras—align wording to your version docs).

Stress large fan-in grouping; hypothesise optimisation levers.

Interview: interplay of aggregate algorithms and memory thresholds (high-level honesty if exact engine thresholds unmemorised—look up authoritative docs when precision needed).
