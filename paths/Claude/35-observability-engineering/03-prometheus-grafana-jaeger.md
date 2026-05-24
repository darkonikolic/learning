# Prometheus • Grafana • Jaeger operating model

**Theme:** Scrapes, panels, traces—**artifact ownership**, not ephemeral UI clicks.

### Prometheus

- Naming & label cardinality discipline (**avoid high-cardinality explosion**—user id as label is usually wrong class).  

- Histogram buckets aligned to SLO thresholds (meaningful p95 / p99, not arbitrary).  

- **Recording rules & alerts** versioned beside code/IaC; change review like application logic.

### Grafana

- Dashboards as **code** (Terraform / provisioning JSON)—environment parity.  

- Annotations tying deploys/incidents to graph shifts (**causal hygiene**).

### Jaeger (or compatible backend)

- Service map sanity vs reality of mesh/ingress.  

- Compare **sync path** vs **async consumer** trace completeness—close blind spots deliberately.

### Alerting strategy (reprise)

Each alert answers: **symptom**, **SLO link**, **owner**, **first triage step**, **expected false-positive rate class**.
