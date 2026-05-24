# Unit 6 — Middleware cross-cutting fibres: tracing hooks, audit, auth placeholders

## Learning outcome catalogue

Treat middleware onion ordering intentionally:

Suggested outer→inner illustrative ordering (adapt consciously):

```
panic/recovery sentinel (thin)
logging / correlation id enrichment
authentication / authorization scaffolding (possibly stub verifying header presence minimally)
metrics future hook comment anchors
routing entry
```

Practice capabilities:

```
request id attribution (propagate contextual logging downstream)
rudimentary structured logging scaffolding bridging next unit amplification
opaque future auth verifying static bearer token minimally if time permits—not security theatre pretending completeness—label clearly educational stubbing
```

## Lab essay

Articulate distinctions **middleware vs handler** responsibilities preventing domain logic creep upward accidentally.

Enumerate danger compressing heavyweight DB transactions inside middleware—justify rarely exceptional cases if any—even hypothetical negatives primarily.
