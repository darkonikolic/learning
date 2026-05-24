# Unit 01 — Index as structure, not superstition

Contrast full scan vs indexed lookup on `orders(id, customer_id, status, created_at)` shaped lab rows.

Observe predicate `WHERE customer_id = ?` performance before vs after auxiliary index introduction.

Articulate logarithmic retrieval intuition rooted in balanced tree ordered keys (conceptual drawing welcome).

Interview: coarse B-tree mental model versus linear scan asymptotics at scale narratives.
