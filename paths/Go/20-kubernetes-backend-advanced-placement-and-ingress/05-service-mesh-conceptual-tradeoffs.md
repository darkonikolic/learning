# Unit 5 — Service Mesh: Conceptual Tradeoffs

## Concept

A service mesh injects a sidecar proxy (Envoy) into every pod. All inter-service traffic flows through these proxies, which gives you mutual TLS between services, fine-grained traffic control (retries, circuit breaking, canary weights), and consistent observability (metrics, traces) without changing application code. The cost is real: each pod runs an extra container consuming ~50-100 MB RAM and adding 1-5 ms of latency per hop. The operational complexity of Istio or Linkerd is significant. Add a mesh when you have a concrete, unsolved problem — not because it is fashionable.

## Code

```
Feature comparison: with mesh vs without

FEATURE                   WITHOUT MESH              WITH MESH (Istio/Linkerd)
─────────────────────────────────────────────────────────────────────────────
mTLS between services     Manual cert rotation       Automatic, transparent
Retries / timeouts        Code in each service       VirtualService YAML
Circuit breaking          Library (hystrix/etc.)     DestinationRule YAML
Traffic splitting         Deploy new version         Weight: 90/10 in YAML
Per-service metrics       Instrument each service    Automatic from Envoy
Distributed tracing       Propagate headers in code  Partial auto + headers
Latency overhead          0 ms                       1-5 ms per hop
RAM overhead per pod      0 MB                       50-100 MB (sidecar)
Operational complexity    Low                        High (CRDs, upgrades)
Debug difficulty          Standard Go tools          Must understand Envoy

When to add a mesh:
  - You have 20+ services and mTLS is a compliance requirement
  - You need canary deployments without code changes
  - You need uniform circuit breaking across a large fleet

When NOT to add a mesh:
  - You have < 10 services
  - Your team is not yet operating Kubernetes confidently
  - You can solve the problem (retries, mTLS) at the application layer
```

## Exercise

**Build:** Audit your e-commerce service against the feature table above.
**Input:** The list of services in your system (API, auth, inventory, payments).
**Output:** A written decision: would you add a service mesh? For which specific feature?
**Acceptance:** For each mesh feature, answer: (1) Do I need this? (2) Can I implement it at the application layer instead? (3) What is the cost of the application-layer solution vs the mesh solution? Your answer should conclude with a concrete threshold: "we would add a mesh when X."

## Interview

- What problem does mutual TLS (mTLS) solve that regular TLS does not?
- A team says "we need Istio for observability." What would you suggest instead?
- Service mesh adds latency. Under what traffic pattern does 5 ms per hop become significant?
