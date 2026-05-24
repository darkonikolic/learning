# Unit 2 — Dependency injection mastery beyond autowire defaults

Senior depth

- **Autowiring heuristics** limitations: collisions, ambiguous service ids, generics typing blind spots requiring explicit binds.
- **Decorators**: layered cross-cutting collaborators (audit, metering) without rewriting core handlers.
- **`#[Autoconfigure]`/`#[Exclude]` nuances** sparingly—not attribute soup replacing architectural thinking.
- **Compiler passes & tagged iterator patterns** consolidating plugin-like extension strategies.

Practice

Pick one cross-cutting collaborator (audit / metrics façade). Outline decorator layering **before** proposing event listener proliferation—justify compositional coherence.
