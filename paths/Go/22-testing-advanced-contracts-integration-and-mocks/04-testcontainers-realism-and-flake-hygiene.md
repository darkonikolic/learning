# Unit 4 — Testcontainers discipline (realism without endless flakes)

Practise patterns:

```
container lifecycle per package vs shared suite hooks trade-offs
migrations applied before tests deterministically
parallelism cautions hitting same ports—use ephemeral bindings
tear down hygiene even after panic fails (t.Cleanup idioms)
```

Deliverable: list your top five flake sources you’d defend against before blaming CI infra.
