# Unit 1 — Probes, Grace Periods, and Observability Contracts

## Concept

Kubernetes makes a contract with your service: readiness probe passes before any traffic arrives, liveness probe passes or the pod is restarted, and `terminationGracePeriodSeconds` gives you a window to drain before the hard kill. If your grace period is shorter than your longest in-flight request, Kubernetes will kill mid-flight requests during every rolling deploy. The shutdown budget in your Go code must be strictly less than `terminationGracePeriodSeconds` — set the Go shutdown timeout to 25s and `terminationGracePeriodSeconds` to 35s.

## Code

```yaml
# deployment.yaml — full probe and grace period configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    spec:
      # Grace period must exceed your Go shutdown timeout.
      # Go code: context.WithTimeout(ctx, 25*time.Second)
      # k8s kills: after 35s
      terminationGracePeriodSeconds: 35
      containers:
      - name: api-server
        image: myregistry/api-server:latest
        resources:
          requests:
            cpu: "250m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"

        # Liveness: restart pod if deadlocked.
        # Use a very light check — just HTTP 200.
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 10   # wait for startup
          periodSeconds: 10
          failureThreshold: 3       # 3 failures = restart

        # Readiness: stop sending traffic if deps are down.
        # DB ping here is correct — not in liveness.
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 2       # 2 failures = remove from LB
          successThreshold: 1       # 1 success = back in rotation
```

## Exercise

**Build:** Set `terminationGracePeriodSeconds: 5` deliberately too low, then observe the failure.
**Input:** Your API service with requests that take 10 seconds to complete.
**Output:** In-flight requests killed mid-flight during a rolling deploy.
**Acceptance:** (1) Deploy with grace period 5s. Start 10 slow requests. Trigger a rolling update. Observe connection resets or 502s. (2) Fix: set grace period to 35s and Go shutdown timeout to 25s. Repeat the test. All 10 requests complete with 200.

## Interview

- Your longest request takes 20 seconds. What should `terminationGracePeriodSeconds` be, and why not exactly 20?
- A readiness probe starts failing in production. What does Kubernetes do? What does it NOT do?
- What is `initialDelaySeconds` for, and what happens if it is set too low?
