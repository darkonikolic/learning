# Infrastructure ownership

**Unit:** `04` (week 4)—**production mindset**: Docker, **Kubernetes**, **Terraform**.

### Deliverables

**Deployment plan** — order of operations, health criteria, blast radius  

**Rollback plan** — what reverses first, irreversible forks called out  

**Health verification** — readiness/liveness semantics, probes that match real dependencies

### Practice

Docker: worker image lifecycle, env contract, sensible resource hints.  

Kubernetes (**production-facing concepts**—not demo defaults):

Core probes stay as-is; add **traffic & scheduling posture**:

**Ingress + TLS termination story** — how external clients reach Symfony API/worker admin surfaces; TLS at edge vs mesh  

**NetworkPolicy** — default deny + explicit egress to MySQL broker PSP DNS; label-scoped namespaces practice  

**PodDisruptionBudget (PDB)** — voluntary disruptions (node drain, rollout) cannot zero critical payment workers unknowingly  

**Affinity / anti-affinity** — keep noisy neighbours off hot nodes; spread replicas across topology zones where fake cluster allows  

**Taints / tolerations** — dedicated node pools vs spot mix if you simulate cost separation  

**Service mesh (conceptual only unless you deliberately adopt Istio/Linkerd)** — mTLS overlays, retries vs idempotency clashes, observable L7 hops—diagram **without** implying required mesh for this curriculum  

Terraform: module boundaries, **resource ownership** tags, plan discipline before apply.

### Adversarial LAB

Break a deploy path in a disposable environment — rehearse **repair** vs **rollback** with explicit ordering.

### Checklist

- [ ] Rollback is exercised at least once on paper or in sandbox—not only hoped for in prod.  

- [ ] **PDB / disruption** story articulated for at least deployment class you run (workers + API).  

- [ ] **NetworkPolicy** sketch exists—even if permissive—to prove you thought about egress blast radius to PSP/metadata APIs.  

- [ ] Ingress path documented (hostname, certs, backends); mesh decision explicit “adopt vs defer” rationale.  

Reference tables: **`09-enterprise-depth-appendix.md` § Kubernetes production.**
