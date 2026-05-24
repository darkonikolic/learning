# Unit 1 — Scope: frontend testing posture (confidence, not coverage theatre)

Mindset shift: from “manual click QA” toward **signals that refactoring is safe enough.**

## Learning outcomes

- **Pyramid framing**: pragmatic balance of unit, component/integration, Playwright-class E2E — what each buys.
- **Unit tests**: pure helpers (`formatPrice`, discounts, carts) via **Vitest** (or aligned runner).
- **Isolation & mocks**: forbid accidental network reach from fast tests; fixture discipline.
- **Component tests**: **Vue Test Utils** — render, interactions, emits, accessibility smoke where useful.
- **Store tests**: Pinia actions/mutations boundaries with mocked API seams.
- **E2E**: thin happy paths + one failure-mode journey (Playwright or equivalent).
- **Contract drift**: frontend expectations vs backend JSON shape mismatches — how tests catch breakage before prod.
- **Regression discipline**: purposeful “break tests” exercises to validate signal.
