# Unit 3 — Router shaping (`chi`): resources, verbs, `{id}` parameters

## Practice route map scaffold

Establish coherent resource tree aligning REST-ish pragmatics (don’t feud pedantic REST theology yet—focus cleanliness):

```
GET /health
GET /users
POST /users
/users/{userID}
GET /orders
...
```

Choose parameter naming bridging chi patterns (` chi.URLParam` etc.) responsibly—document uniformity conventions early preventing drift.

Routing layer remains **thin**: parameter extraction + delegating—not SQL embed hideouts.

Interview dimension: Discuss **ownership** delineation—mux knows path shapes; handlers adapt to typed service calls—not deeply nested closures anonymous obscuring coverage.
