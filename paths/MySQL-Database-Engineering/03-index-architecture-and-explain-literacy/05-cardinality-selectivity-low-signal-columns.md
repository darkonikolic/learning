# Unit 05 — Cardinality / selectivity: not every column earns an index

Build intentionally low-distinct indices (`status` tri-state) contrasting high-uniqueness (`email`-like).

Observe optimiser abandonment or downgrade where histograms signal poor payoff.

Interview: describing low cardinality index traps and mitigation (composite leading strong key, constraint redesign, conditional indexes if platform supports—note portability).
