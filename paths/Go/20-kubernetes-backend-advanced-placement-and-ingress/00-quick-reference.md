# Quick Reference — Kubernetes for Go Backends

## Resource sizing
requests: scheduler placement (always set)
limits:   safety ceiling (OOM if memory exceeded, throttled if CPU exceeded)

Typical Go service starting point:
  requests: cpu: 50m, memory: 64Mi
  limits:   cpu: 500m, memory: 256Mi

## HPA triggers
CPU utilization (most common)
Custom metrics via Prometheus adapter (RPS, queue depth)

## Rolling update (zero downtime)
maxSurge: 1, maxUnavailable: 0
+ readinessProbe must pass before old pods are removed

## Key kubectl commands
kubectl rollout status deployment/name
kubectl rollout undo deployment/name
kubectl rollout history deployment/name
kubectl top pods                         # requires metrics-server
kubectl describe pod <name>              # events, resource usage
kubectl exec -it <pod> -- /bin/sh        # debug (if shell exists)

## Pod lifecycle hooks
terminationGracePeriodSeconds: 30        # time for graceful shutdown
preStop hook: sleep briefly to let LB drain connections before SIGTERM
