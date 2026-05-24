# Ingress ownership — K8s production framing

## Phase framing — Production Kubernetes Engineering (“Phase 6.4”)

**Units in this folder:** `01`–`06` (topic order only).

### Themes across units

**Ingress** controllers & HTTP(S) routing truth • **NetworkPolicy** segmentation • **affinity / anti-affinity** • **taints / tolerations** scheduling contracts • **PodDisruptionBudgets** voluntary eviction guardrails • **autoscaling** (workload + cluster semantics) • **service mesh** (conceptual: traffic shifting, resilience, telemetry) • **production ownership**

### Operating loop (reuse per change / incident slice)

```
 Deploy / roll forward  →  Observe signals  →  Scale posture (out / up / autoscaler tuning)  →  Recover deliberately
```

**Checkpoint mantra:** instincts shift from “`kubectl apply` succeeded” narrative toward owning **traffic path, isolation, eviction safety, elasticity, observable recovery**.

### Production cluster slice worksheet

| Column | Holds |
|--------|-------|
| **Ingress / routes** | Hosts, TLS, annotations, upstream Service mapping, health checks assumptions. |
| **Network boundaries** | Who may talk to whom (namespaces / workload identity); explicit default-deny ambition. |
| **Scheduling guarantees** | Node pools, affinity, taints—is critical workload actually landing where operations believe. |
| **Resilience budget** | PDB minAvailable / maxUnavailable + surge strategy sanity. |
| **Scale knobs** | HPA metrics, quotas, CAS interaction if applicable—documented—not mystery defaults. |
| **Observe + recover** | Dashboards/alerts tying deploy events to saturation and failure bursts. |

### Version / distribution reality

Ingress implementations (Gateway API vs classical Ingress controllers), NetworkPolicy enforcement (CNI-dependent), PDB semantics with DaemonSets / Jobs—**verify against your Kubernetes minor version + cloud/CNI**. Rules in this workspace expect you to open current vendor docs rather than trusting static YAML folklore.

---

**Theme (this unit):** **Ingress owns the north–south façade** exposed to humans and integrations—misconfiguration cascades amplify fastest here.

Topics to rehearse declaratively vs imperatively authored routes; TLS lifecycle (termination location, certificate rotation hooks); canonical Service `type` interplay (`ClusterIP` vs `LoadBalancer`); cross-namespace references risks when allowed.

Labs: annotate **traffic failure modes** deliberately (misrouted backend, stale Endpoints churn, websocket vs HTTP/2 quirks if relevant)—pair every hypothesis with observable signal from controller metrics / access logs—not blind pod restarts.

### Checklist

- [ ] **Health probes** differentiated from synchronous deep dependency checks dangerously coupled to cascading kill loops.  
