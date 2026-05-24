# Network policy ownership

**Theme:** Namespaces pretending isolation without **NetworkPolicy** truth remain cardboard walls—assume breach and design segmentation **as code**.

Contrast:

| Posture | Outcome expectation |
|---------|---------------------|
| Permissive defaults | Faster bootstrap; brittle blast radius lateral movement |
| Intentionally layered deny + explicit allow lanes | Operational overhead; sharper incident containment narratives |

Articulate selectors (`podSelector`, `namespaceSelector`), egress DNS realities, kube-apiserver accessibility nuance versus workload mesh—CNI dictates enforceability.

### Labs table ideas

Synthetic microservice tiers: frontend → API → database proxy **only necessary edges** enumerated.

Deliberately break policy—measure observability breadcrumbs proving blocked flows vs silent timeouts misdiagnosed as app bugs.

### Checklist

- [ ] Policies version controlled & reviewed analogous to infra PR gravity—not orphaned operator console edits drifting untracked.  
