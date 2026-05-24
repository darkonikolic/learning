# Large system thinking

**Theme:** Draw the **whole** animal—not only one service file—when reasoning about payments-scale platforms.

### Layer stack rehearsal (adjust to reality)

Symfony and/or Laravel services  

Go workers / APIs  

**MySQL**, optional **Redis** / cache tiers  

Terraform modules & environment matrix  

Kubernetes runtime + networking  

Observability (logs / metrics / traces)  

AI assist layer sitting **above** repos (agents, retrieval, Rules/Skills) affecting change velocity **and** risk

### Mandatory graphs (even rough)

**Dependency graph** — build / import / infra edges truthfully.  

**Ownership graph** — teams or roles per runtime component.  

**Failure graph** — primary blast paths and cascading edges (queues, retries, partial deploy).

**LAB artefact**

Produce one **large system map** consolidating these three—digital whiteboard snapshot or structured doc section.

Discuss **boundary discipline** crossing PHP ↔ Go ↔ data ↔ IaC ↔ K8s—where contracts must be typed and monitored.

Discuss **SECURITY** overlays: IAM paths, secret flows, review gates per band.

### Checklist

- [ ] Map updated when **major dependency** added—CI hook or quarterly review cue.  
