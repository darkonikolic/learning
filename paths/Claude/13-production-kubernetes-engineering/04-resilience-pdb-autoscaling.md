# Resilience budgets and autoscaling

**Theme:** **Surge & stability** interplay—scaling amplifies latent misconfiguration storms without guardrails like **PodDisruptionBudget**.

### PodDisruptionBudget (PDB) ownership

Articulate interplay with Deployments rolling strategy, voluntary disruptions (cluster upgrades / node drains) vs accidental Pod failures—they differ taxonomically.

Anti-pattern: PDB so strict upgrades stall endlessly; PDB so lax customer-visible brownouts unnoticed until load peaks.

### Autoscaling strata

Workload **HPA** metrics selection (latency proxy vs saturation vs custom/external metrics), cooldown myth debunk via measured oscillation logs where possible.

Possible cluster-level **nodes autoscaler** interaction—scaling out nodes hides scheduling Pending only after queue drain reveals deeper scheduling faults.

Discuss **limits / requests** interplay honestly—autoscaler reacts to observable utilisation artefacts shaped by stale resource guesses.

Labs: provoke oscillation ethically in sandbox analysing metric noise vs purposeful surge.

### Checklist

- [ ] Correlate **scaling events timeline** explicitly with ingress latency / saturation dashboards—not isolated pod counts twitching.  
