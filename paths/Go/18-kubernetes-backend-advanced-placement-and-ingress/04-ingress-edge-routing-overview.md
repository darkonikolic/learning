# Unit 4 — Ingress: routing edge traffic to Services (conceptual sketch)

Ingress sits at the edge (cloud load balancers / ingress controllers vary—avoid single-vendor absolutism).

Understand:

```
DNS / TLS termination often lives near ingress layers
path-based routing to different Services
timeouts and body size limits commonly configured here (not only in app)
```

## Practice (diagram)

Draw `client → ingress → service → pods` for your `api`, noting where health checks hit.

## Interview prompts

Ingress controller vs API gateway overlap (high level); where WAF/rate limits often live (hint: Area 21 overlaps).
