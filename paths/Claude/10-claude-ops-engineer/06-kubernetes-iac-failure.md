# Kubernetes + IaC failure

**Theme:** Platform truth mutates deliberately *and* accidentally—observe **desired vs actual**.

### Kubernetes failure patterns

CrashLoop backoff nuance  

**Readiness vs liveness** mis-spec causing traffic to sick instances  

Mis-scaled Horizontal Pod Autoscaler oscillation / metric blind spots  

Rolling update stuck mid-maxUnavailable geometry  

Admission webhook / quotas / PDB interactions

### IaC confrontation

**Terraform:**

`plan` / `apply` divergence vs reality  

State drift origins & locking contention  

Destructive replacements masked as benign tweaks  

Cross-stack resource contention

**Helm:**

Release revision skew  

Template ordering bugs  

Hooks failing silently leaving partial manifests

### LAB deliverable sketch

Produce end-to-end **incident timeline doc** marrying cluster events ↔ Terraform diff ↔ GitOps revision hypotheses.

### Checklist

- [ ] Blast radius enumerated for `kubectl delete`/forced replacement shortcuts.  
