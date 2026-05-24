# Unit 07 — Window functions (ranking and running analytics)

Functions: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, framing with `OVER (PARTITION BY … ORDER BY …)`.

Deliver:

- Top purchasers per month buckets.
- Product leaderboards with tie semantics called out.
- Running totals / moving metrics on order streams you generate.

Lab articulate **aggregate collapse** (`GROUP BY`) vs **per-row analytic** (`OVER`): when each mental model fits.

Interview: windows for ranking & cumulative metrics; aggregates for dataset compression.
