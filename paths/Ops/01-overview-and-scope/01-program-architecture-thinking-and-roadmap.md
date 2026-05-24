# Ops / Platform / Cloud — mindset and phased roadmap

This path supports **hands-on comprehension** of how modern backends are **built**, **tested**, **packaged**, **distributed**, **deployed**, **observed**, **maintained**, **incident-handled**, and **safely improved** — not trivia memorised separately from systemic behaviour.

## What deep understanding means here

How an artefact survives from source control curiosity into repeatable production behaviours: pipelines, artefacts, rollout surfaces, observable runtime, corrective action, guarded evolution.

## Area map (numeric order = topic progression)

| # | Folder | Role |
|---|--------|------|
| `01-*` | Overview | Ethos, practise rule, resource index |
| `02-*` | Linux administration + troubleshooting | Host triage foundation |
| `03-*` | Git collaboration + release workflow | History, branches, merges, tags, recovery |
| `04-*` | GitLab CI/CD + delivery | `.gitlab-ci.yml`, runners, caches, gates, deploy hooks |
| `05-*` | Docker + container workflow | Images, Dockerfile, compose, registry, debug |
| `06-*` | Podman rootless + daemonless posture | Rootless, pods, systemd units, compose compat |
| `07-*` | Container networking + service comms | Bridges, DNS inside user networks, NAT, proxy shape |
| `08-*` | Kubernetes orchestration | Workloads, networking in-cluster, storage, ingress, ops |
| `09-*` | Helm packaging | Charts, values, upgrades, rollbacks |
| `10-*` | Terraform / IaC lifecycle | State, modules, environments, drift, cloud-ready sketches |
| `11-*` | Application networking + TLS + foundational proxies | DNS, routing, firewall, host-level Traefik/Nginx drills |
| `12-*` | Edge reverse proxy + traffic shaping | Compression, TLS termination, LB pools, timeouts, abusive traffic guardrails |
| `13-*` | Monitoring metrics + Prometheus | Golden signals, scrape model, exporters, PromQL essentials, alerting |
| `14-*` | Structured logging + Loki aggregation | JSON logs, correlation, central search & forensic discipline |
| `15-*` | Distributed tracing + OpenTelemetry | Spans propagation, collector, sampling realism |
| `16-*` | Unified observability + incident investigation hooks | Grafana multi-signal, correlation labs, introductory SLO talk |
| `17-*` | Secrets & credential lifecycle | env separation, K8s Secret realism, Vault concepts, CI variable hygiene |
| `18-*` | DevSecOps + supply-chain aware CI | Scanners, SBOM, SAST, pipeline gate storytelling |
| `19-*` | AWS foundations + operations skim | IAM→VPC→data→edge→ECS/EKS introductions + Terraform/AWS touchpoints ethically |
| `20-*` | Production reliability rituals | Rollback, backup scepticism, DR tabletop, rollout strategies, blameless retros |
| `21-*` | Incident troubleshooting scenario labs | K8s, resources, nets, pipelines, datastore timeout narratives |
| `22-*` | Performance & bottleneck optimisation | Profiler/pprof/cache/pools/load-tests + Postgres/Redis/queue tie-ins |
| `23-*` | Platform engineering abstraction | Developer platforms golden paths paved roads governance guardrails ethically |

Professional depth (**Docker · Kubernetes · Helm · Terraform · AWS**) continues inside those same folders as **`11+` / `13+` / `10+` / `13+` / `15+`** trailing worksheets—rather than a separate checklist-only area.

Beyond that, specialise only paths your workload demands (**FinOps mastery, SOC2 drills, alternate clouds**).
