# Unit 3 — `sqlx` patterns: readability + scanning ergonomics resisting ORM concealment relapse

Operational API familiarity anchors:

```
Get / Select scoped queries
Named parameters / NamedExec structuring dynamic fragments cautiously guarded against injection regressions—even if placeholders mostly static early
mapping rows → structs thoughtfully (nullable fields handling strategies preview)
```

## Practice repository scaffolding

Expose methods:

```
FindByID
Create
Delete (+ updates when flows demand)
```

## Interview comparisons

Enumerate ORM pitfalls abstractly hiding N+1 query explosions / implicit eager loading vs explicit SQL readability tax honestly accepted.

Lab micro note: annotate query text readability strategies (capitalisation / line breaks)—reviewer empathy signalling professionalism early.
