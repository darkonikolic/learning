# Unit 2 — Requests, limits, QoS, eviction, and noisy neighbour reality

Kubernetes uses **requests** (scheduling guarantees) and **limits** (caps) to approximate resource isolation.

Study the mental model:

```
under-provisioned CPU request ⇒ throttling risk
memory limit too tight ⇒ OOMKill risk
no requests set ⇒ scheduling lies + cluster instability
```

Understand **eviction** pressures when nodes run out of memory/disk—your pod may disappear even if “the code is fine.”

## Interview prompts

“requests vs limits” in one sentence each; what **Guaranteed vs Burstable QoS** implies for eviction priority (conceptual—verify current kube docs when preparing).
