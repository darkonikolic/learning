# Unit 2 — HTTP handler lifecycle fundamentals (`net/http` mental clarity)

Interpret HTTP not as “`/users` ⇒ JSON magically” caricature—but orchestrated interplay:

```
Request semantics (method/path/headers/body/stream)
⇒ Middleware transformations (ordering matters)
⇒ Handler adapter glue
⇒ Response writer semantics + status/header/body choreography
⇒ Deferred resource closure responsibilities
```

## Practice warmup

Initially optional bare `ServeMux` / `HandleFunc` if clarifies layering—migrate promptly toward disciplined router structuring next unit bridging chi.

Expose:

```
GET /health  (200 minimal JSON heartbeat)
GET /users   (temporary slice static / or stub eventual repository seam)
```

## Lab reflection

Enumerate **panic recovery** layering discussion preview—defer full patterns until middleware unit but conceptual placement begins now.

Articulate pitfalls mutating **`http.Request`** context replacement misuse historically tripping juniors (`r.WithContext` disciplined usage later intensifies).

Interview checklist item: summarise **lifecycle** verbally without textbook quote regurgitation.
