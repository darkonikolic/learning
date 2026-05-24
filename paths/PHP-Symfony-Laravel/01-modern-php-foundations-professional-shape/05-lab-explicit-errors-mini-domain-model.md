# Unit 5 — Lab: miniature domain slice with explicit invariants

## Brief

Implement (or blueprint in pseudocode structured enough that you could paste into a spike repo) **one bounded slice**: e.g. `OrderReservation` issuing stock holds with deterministic failure modes.

Requirements

- Entities / value objects (language-level classes) encapsulate invariants—not generic arrays everywhere.
- **No framework ORM leakage** inside the pure calculation core (Doctrine / Eloquent only at edges later).
- **Explicit failure mapping** surfaced to hypothetical HTTP layer—not generic `RuntimeException`.

## Acceptance checklist

Domain core unit tests asserting:

- invariant violation paths,
- deterministic output for happy path transitions,
- no hidden globals / static façade dependencies.
