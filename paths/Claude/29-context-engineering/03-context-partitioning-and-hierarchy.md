# Context partitioning + hierarchy

**Theme:** Fifty documents & hundreds of SPEC fragments fail if loaded **flat**. Build **levels** + **lanes**.

### Hierarchy sketch (adapt naming)

**L1** Strategic goal / OKR bridging slice  

**L2** Authoritative SPEC / ADR excerpts per bounded capability  

**L3** Implementation references (symbols, migrations, infra modules) gated until L2 pinned  

**L4** Live operational overlays (active incident, anomalies) loaded only during relevant phase

### Partitioning lanes (examples)

**Symfony lane** keyed by aggregate / integration boundary—not whole bounded context cosmos every time  

**Go lane** keyed by worker + queue + retry policy ownership  

**Ops lane** cluster/env scoped—no cross-environment noise unless comparing

Discuss **dependency ownership**: partition boundaries coincide with organisational truth—ambiguous lanes invite pollution.

### LAB artefact

Author **`CONTEXT_HIERARCHY_MAP`**: artefacts × level × default inclusion rule (+ escalation path pulling deeper tier).

Discuss **scaling**: hierarchical lazy expansion prevents token flood yet preserves drill-down fidelity.

### Checklist

- [ ] Map audited when **ownership** lines move—prevent stale partitioning silently misrouting newcomers.  
