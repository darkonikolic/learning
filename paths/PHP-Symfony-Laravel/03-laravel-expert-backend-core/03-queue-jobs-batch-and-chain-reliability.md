# Unit 3 — Queued jobs as distributed transactions’ distant cousins

Depth

- **Job middleware** structuring retry / timeout policy consistency—avoid scattering `public $timeout` arbitrarily.
- **Batch semantics** bridging partial successes / compensations—when saga-like choreography emerges from naive fan-out failures.
- **Failed job inspection discipline** aligning ops expectations with code-level naming & payload clarity.
- **`ShouldQueue` listeners** interplay with transactional DB boundaries identical conceptual hazards as Symfony bridging.
