# Unit 3 — Rolling deployments, restart scenarios, and rollout safety (backend angle)

Explore what happens during `Deployment` rollouts:

```
maxUnavailable / maxSurge interplay (high level)
ReplicaSet history and rollback idea
readiness preventing bad revisions from receiving traffic
```

## Practice narrative

Describe failure mode: new version fails readiness—how does Kubernetes behave? How do you detect it before user impact if readiness is correct?

## Interview prompts

Blue/green & canary contrasts (even if you only run rolling in practice).
