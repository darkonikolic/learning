# Ops + Reviewer agents

**Theme:** Run-the-system expertise and longitudinal code health critique stay distinct from QA’s behavioural conformance focus.

### Ops ownership cluster

Docker image lifecycle coherence  

Kubernetes deployment waves + health signalling discipline  

Terraform / IaC plan vs apply segregation respecting approval tiers  

Operational **incident** instrumentation: required **logs**, **metrics**, articulated **rollback** ladders

Practice vignette stylised:

Go worker **timeouts** cascading—Ops perspective narrates observable triage artefacts before raw restart impulse.

Mandatory Reviewer scaffolding for labs (numeric minima illustrative—scale up rigour with real severity):

Identify **minimum three DIFF risks** plausible (ordering hazards, unnoticed auth regression surface, partial migration coupling).  

Identify **minimum three maintainability critiques** honest (ambiguous naming hotspots, cohesion leaks, creeping cyclomatic burdens).

Separate **Reviewer** security lens from generic style—secret proximity, dubious dynamic execution, infra privilege escalations—even if speculative static scan pass absent.

Collaboration etiquette: Ops + Reviewer may bounce findings prompting Architect reconsideration—not silent Implementer override without Planner priority note when scope shifts materially.

### Checklist

- [ ] Ops artefacts always include rollback preconditions—even when change feels “tiny.”  
