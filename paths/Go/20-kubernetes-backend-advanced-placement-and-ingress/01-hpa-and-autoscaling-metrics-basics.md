# Unit 1 — HPA and Autoscaling: Metrics Basics

## Concept

A HorizontalPodAutoscaler watches a metric — typically CPU utilization — and adjusts the number of replicas in a Deployment to keep the metric near a target. When average CPU across all pods exceeds 70%, HPA adds replicas. When load drops, HPA removes replicas, but gradually to avoid flapping. HPA requires `metrics-server` to be installed in the cluster. Scale-down has a stabilization window (default 5 minutes) so a brief traffic drop does not immediately shrink your fleet.

## Code

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 2           # HPA overrides this once active
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: api-server
        image: myregistry/api-server:latest
        resources:
          requests:
            cpu: "250m"    # HPA uses this as the baseline for utilization %
          limits:
            cpu: "500m"
---
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 2        # never scale below 2 (availability floor)
  maxReplicas: 10       # never scale above 10 (cost ceiling)
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70   # scale up when avg CPU > 70% of requests
```

## Exercise

**Build:** Deploy your API service with the HPA configuration above to a local Kubernetes cluster (minikube or kind).
**Input:** A running Deployment with CPU requests set and `metrics-server` installed.
**Output:** HPA that scales replicas based on CPU load.
**Acceptance:** Run `hey -z 60s -c 50 http://localhost:8080/` to generate load. Run `kubectl get hpa -w` in another terminal. Observe `REPLICAS` count increase beyond 2. Stop the load. Wait 5 minutes and observe scale-down back to 2.

## Interview

- Why must `resources.requests.cpu` be set for HPA to work?
- What is the risk of setting `minReplicas: 1` in production?
- Why does scale-down have a stabilization window but scale-up does not?
