# Unit 1 — Scope: senior interview rehearsal (JS + TypeScript + Vue + SPA systems)

Mindset shift: from “knowing definitions” toward **articulating hypotheses, trade-offs, fixes, and documentation.**

## Working pattern (reuse for every drill)

problem → observable symptom → investigation plan → hypotheses → validation steps → proposed fix → trade-offs → documented outcome.

## Module map

1. **JS runtime traps**: synthetic event-loop/`Promise`/`setTimeout` orderings + closure memory stories.
2. **TypeScript depth**: generics + constraints, discriminated unions + exhaustiveness, guards vs schema validation, `satisfies`/`as const`, branded IDs, module/`import type` hygiene, composition vs inheritance for DTO layers.
3. **Vue internals**: reactive graph, intentional vs accidental rerenders, watcher misuse, `vue-tsc` failure triage.
4. **SPA/system design**: whiteboard ecommerce modules (catalog, cart, checkout, notifications) with router + store boundaries.
5. **API adversity**: stalled checkout, flaky retries, cancellation, optimistic rollback storytelling.
6. **Production pathology**: stale assets post-deploy, CORS regressions, memory growth, unexplained timeouts.
7. **Performance narratives**: oversized bundles, gigantic lists — tie actions to tooling readouts.

Use prior phase artefacts (**`frontend-lab`**, **`browser-lab`**, **`ts-professional-lab`**, **`vue-lab`**, **`shop-spa/**`) instead of toy isolated snippets wherever possible.
