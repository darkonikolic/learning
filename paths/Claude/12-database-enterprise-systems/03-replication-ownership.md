# Replication ownership

**Theme:** Separate **writes** (authoritative durability path) vs **reads** routed to replicas—explicit **ownership** kills ghost consistency assumptions.

### Core tensions

Replica **lag visibility** shaping UI / API staleness disclaimers  

**Split-brain** avoidance patterns during failover rehearsals  

Promotion choreography & **routing flips**

Binary / statement / mixed historical replication quirks—consult engine docs—not generic blog cargo cults.

### LAB — replica lag scenario narrative

Observe workload under churn: artificially delay apply thread or saturate replica I/O—expose **reading your own writes** gaps and reconcile strategies (sticky session to primary narrow slice, versioning headers, TTL hints honestly labeled).

Metrics ownership: replication lag gauges (exact names vary by MySQL/MariaDB major version — use `SHOW REPLICA STATUS` / instrumentation your edition documents) interpreted against apply latency—not a single naive scalar story.

### Checklist

- [ ] Operational runbook cites **fallback read path authority** clarity when replicas diverge dangerously.  
