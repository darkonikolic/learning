# Unit 4 — Request/response boundaries: handlers stop being database scripts

## Anti-pattern diagnosis

Flattened handler descending raw SQL monstrosities interleaved JSON marshalling + domain rules—“works day one, rots iteration two.”

Prefer explicit adaptation layer:

```
HTTP DTO/request shape → validated domain/command structure → persisted model distinctions if justified
```

## Practice trajectory

Implement `POST /users`/`CreateUser` style flow:

- Incoming JSON → **request DTO**.
- Transformation / validation segregation upcoming unit intensifies interplay.
- Outgoing response shaping intentionally omitting leaky internal fields exposing DB surprises.

Interview lens contrasts **transport models** versus **persisted aggregates** thoughtfully—not dogmatic cloning always—just conscious mapping.
