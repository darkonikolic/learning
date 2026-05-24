# Unit 4 — Hexagonal architecture framework adapters

Map **ports**:

- Persistence port implementation swap (Doctrine Repository vs Eloquent repository façade).
- External payment gateway façade isolating timeouts / idempotency key generation.
- Email / SMS notification port mocking contract tests cleanly.

Articulate dependency direction rule **domain core never referencing HTTP attributes**.
