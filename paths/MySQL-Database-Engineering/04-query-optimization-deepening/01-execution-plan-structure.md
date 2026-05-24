# Unit 01 — Execution plan as contract with the optimiser

Map `EXPLAIN` fields (`id`, `select_type`, `table`, `type`, `rows`, `key`, `Extra`) to mental story of join order and access path.

Predict then verify on `orders` filtered by `customer_id`.

Interview: interpret `rows` estimate; interpret `type` degradation.
