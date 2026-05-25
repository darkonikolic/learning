# Unit 9 — Kubernetes backend mindset (not admin exam)

You are not aiming to be the cluster SRE on day one—you need **enough vocabulary to reason about how your Go binary lives**.

Core nouns:

```
Pod
Deployment (rollout/replicas)
Service (cluster networking abstraction)
ConfigMap / Secret (config & sensitive material injection—still “secrets in etcd” caveats)
```

## Practice (paper acceptable)

Sketch: `api` pod(s) → `Service` → dependency `database` (managed or not) showing where readiness gates traffic.

## Interview prompts

Why Deployments create new ReplicaSets; what happens during rollouts to in-flight connections (high level).
