# Unit 2 — Resource Requests, Limits, and Pod Eviction

## Concept

`requests` is what Kubernetes uses to schedule a pod onto a node — it is the guaranteed allocation. `limits` is the hard ceiling the container cannot exceed. For CPU, exceeding the limit causes throttling. For memory, exceeding the limit causes an OOM kill (the container is killed and restarted). Set `requests` to what your service needs at normal load. Set `limits` at 2-3x requests to absorb spikes without evicting the pod. If a node runs out of memory, Kubernetes evicts pods with no requests set (BestEffort) first, then pods where usage exceeds requests (Burstable), then pods where usage is within requests (Guaranteed).

## Code

```yaml
# Good resource configuration for an HTTP API service.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  template:
    spec:
      containers:
      - name: api-server
        image: myregistry/api-server:latest
        resources:
          requests:
            cpu: "250m"       # 0.25 CPU cores — scheduler guarantee
            memory: "128Mi"   # 128 MB — scheduler guarantee
          limits:
            cpu: "500m"       # 0.5 CPU cores — throttle at this ceiling
            memory: "256Mi"   # 256 MB — OOM kill above this

# QoS classes (set automatically by Kubernetes):
#
#   Guaranteed:  requests == limits for all containers
#                → safest, last to be evicted
#
#   Burstable:   requests < limits (our config above)
#                → evicted if node pressure AND usage > requests
#
#   BestEffort:  no requests or limits set
#                → first to be evicted, avoid in production
```

## Exercise

**Build:** Deploy your API service with memory limit set to `64Mi`.
**Input:** An endpoint that allocates 128 MB of memory (e.g., `make([]byte, 128*1024*1024)`).
**Output:** OOM kill event visible in pod description.
**Acceptance:** Hit the endpoint. Run `kubectl describe pod <pod-name>` and find `OOMKilled` in the last state. Fix: either raise the limit to `256Mi` or reduce the allocation. Verify the pod no longer restarts after the fix.

## Interview

- What is the difference between CPU throttling and memory OOM kill?
- A pod is scheduled onto a node but the node runs out of memory. Which pods are evicted first?
- Why is it dangerous to set no resource limits in production?
