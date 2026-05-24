# Unit 2 — Labs: build the harness on `shop-spa/`

## Minimum bar

- `tests/unit/**` covering money/cart/domain helpers (≥10 purposeful tests).
- Component specs for **`ProductCard`**, **`Cart`** surface — props, emits, unhappy UI states.
- Pinia **`cartStore`** tests with mocked API adapter.
- **Playwright**: login → browse → cart → checkout smoke; second scenario for guarded route.

## Debugging lab

Deliver **intentionally broken branches** (wrong field name from API; broken emit wiring) — show failing tests narrowing root cause quickly.

Interview topics: pyramid trade-offs, mocking vs integration, flaky E2E control, regression vs refactor safety.
