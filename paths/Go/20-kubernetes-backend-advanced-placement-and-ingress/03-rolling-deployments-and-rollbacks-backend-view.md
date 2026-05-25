# Unit 3 — Rolling Deployments and Rollbacks

## Concept

A rolling update replaces old pods with new ones gradually. `maxUnavailable: 0` means Kubernetes waits for the new pod to pass its readiness probe before terminating an old pod — zero downtime. `maxSurge: 1` allows one extra pod to exist during the transition so replacement can proceed without waiting for an old pod to die first. If the new version is broken, `kubectl rollout undo` rolls back to the previous ReplicaSet immediately. Kubernetes keeps the previous ReplicaSet around for exactly this purpose.

## Code

```yaml
# deployment.yaml — rolling update strategy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0   # never kill an old pod before new pod is ready
      maxSurge: 1         # allow 1 extra pod during the transition (4 total)
  template:
    spec:
      containers:
      - name: api-server
        image: myregistry/api-server:v2
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
```

```bash
# Deploy v2
kubectl set image deployment/api-server api-server=myregistry/api-server:v2

# Watch rollout progress
kubectl rollout status deployment/api-server

# v2 is broken — roll back to v1 immediately
kubectl rollout undo deployment/api-server

# Verify rollback
kubectl rollout status deployment/api-server
kubectl get pods -l app=api-server
```

## Exercise

**Build:** Deploy v1 of your API service. Then deploy v2 with a deliberate bug (handler always returns 500).
**Input:** Two image tags: `api-server:v1` (working) and `api-server:v2` (broken).
**Output:** Successful rollback to v1 using `kubectl rollout undo`.
**Acceptance:** (1) After v2 deploy, hit the endpoint and confirm 500s. (2) Run `kubectl rollout undo`. (3) Hit the endpoint again and confirm 200s. (4) Time the rollback — it should complete in under 60 seconds with 3 replicas.

## Interview

- With `maxUnavailable: 0` and `maxSurge: 1`, what is the maximum number of pods running at any point during a rollout of a 3-replica deployment?
- What does Kubernetes use to decide whether a new pod is ready to receive traffic during a rolling update?
- How many previous ReplicaSets does Kubernetes keep by default? What controls this?
