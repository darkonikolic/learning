# Unit 5 — Doctrine at senior depth (not accidental Active Record)

Understand

- **Unit of Work** mental model identity map staleness pitfalls when mixing raw SQL casually.
- **Lazy vs eager** loading trade-offs & N+1 recognition patterns—not only profiler blame.
- **Transaction boundaries spanning domain + integrations**: flushing order vs messenger dispatch bridging (consistency pitfalls).
- **Mapping inheritance strategies** repercussions (JOINED vs SINGLE_TABLE) altering query shape subtly.

Interview talking points

Hydration explosions, partial object graphs via DTO projections, **read model vs aggregate write model** divergence.
