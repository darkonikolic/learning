# Database MCP

**Theme:** Treat DB capabilities as **surgical optics** supporting schema fidelity, correctness, pacing—not chatty dumping of entire tables unsupervised.

### Coverage bands

Dialect introspection responsibly  

Targeted analytical **queries & EXPLAIN workflows** respecting row limits  

**Index / constraint reasoning** tethered to access patterns surfaced earlier  

Controlled **migration review** interplay (destructive deltas escalated deliberately)

Symfony + MySQL common lab arcs:

Observe **slow query** artefact externally (log / APM)—then escalate through **schema → query shape → indexing → iterative validation** layering.

Parallel Go angle: annotate **transactional flow** hotspots—where isolation expectations meet ORM/driver defaults.

Mandatory **minimum three hypotheses** enumerated **prior** optimisation / rewrite attempts—reuse failure-class vocabulary from observability syllabus when helpful.

Risk register explicit for broad `SELECT *` automation, ambiguous prod vs staging datasource confusion, unintended write statements.

Rollback awareness: DDL rarely trivially reversible—plan dual-phase compatibility when MCP-assisted proposals touch production-like sandboxes.

### Checklist

- [ ] Queries include safeguards (`LIMIT`, indexed predicates) proving discipline—not accidental prod table scans.  
