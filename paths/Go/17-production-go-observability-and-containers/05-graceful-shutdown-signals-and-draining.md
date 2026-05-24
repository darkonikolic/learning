# Unit 5 — Graceful shutdown: signals, draining, and worker collaboration

Production stops processes—rolling deploys, spot interruptions, human maintenance.

Pattern outline:

```
Listen for SIGINT/SIGTERM via signal.Notify
Stop accepting new HTTP connections (http.Server.Shutdown with context budget)
Finish in-flight requests / drain worker pools cooperatively
Flush logs / exporters if needed (bounded time)
exit cleanly
```

## Practice

Extend a queue worker or HTTP server in `prod-service/` with shutdown that **does not** drop active work instantly.

## Interview prompts

Draining vs hard kill trade-offs; how shutdown interacts with Kubernetes `terminationGracePeriodSeconds` (conceptual).
