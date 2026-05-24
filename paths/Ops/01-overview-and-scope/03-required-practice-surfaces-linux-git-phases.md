# Required practice surfaces — Linux stack through platform engineering arcs

Operate only machines and tenants you ethically control.

**Linux labs:** authorised Ubuntu VMs, disposable directories, scripted reversible failures, reproducible notes (never paste secrets).

**Git / GitLab labs:** Symfony (or analogous) codebase plus local GitLab (or compliant equivalent) for merge/release rehearsal without customer data leakage.

## Downstream corridors (`04` … `23`)

| Area | Typical lab ingredients *(adapt to local policy)* |
|------|--------------------------------|
| CI/CD GitLab (`04-*`) | `gitlab-runner`, Docker-capable runners, PHPUnit/Composer, PHPStan/static gates, pipeline secret hygiene |
| Docker (`05-*`) | Docker Engine + Compose plugin + Symfony mocks; trailing units (**`11-*` onward**) deepen **supply-chain & hardening posture** responsibly |
| Podman (`06-*`) | `podman`, compose compatibility quirks, systemd unit generation |
| Container networking (`07-*`) | User-defined bridges, internal DNS drills, constrained packet capture tuition |
| Kubernetes (`08-*`) | Lightweight clusters (**k3d**, kind…), disposable playgrounds; trailing units broaden **capacity, PDB, quotas, NetworkPolicies** ethically |
| Helm (`09-*`) | Charts on lab clusters; trailing units practise **schemas, hooks/tests, OCI registries, GitOps hand-off language** consciously |
| Terraform / IaC (`10-*`,`19-*`) | Terraform/OpenTofu + AWS learner accounts responsibly; **`10-*` trailing worksheets** widen backend/apply safety; **`19-*`** extends AWS breadth |
| App networking foundations (`11-*`) | Host `nginx`, `openssl`, `dig`, `ss`, cautious `tcpdump` |
| Edge proxies & shaping (`12-*`) | Nginx ↔ Traefik, TLS offload, timeouts, selective compression, sane rate limits |
| Monitoring (`13-*`) | Prometheus, exporters, PromQL playgrounds, alerting hooks |
| Logging (`14-*`) | Grafana Loki ingestion stack, correlation IDs across Symfony + Go |
| Tracing (`15-*`) | OpenTelemetry Collector (+ Tempo/Jaeger-class backends sized for labs) |
| Observability synthesis (`16-*`) | Grafana boards merging metrics/logs/traces |
| Secrets (`17-*`) | Vault OSS sandbox optional · GitLab protected variables · K8s Secret realism |
| DevSecOps (`18-*`) | Trivy, SBOM, SAST/additional scanners in CI |
| AWS operations (`19-*`) | Core IAM/VPC/compute/storage/ECS/EKS introductions; **`15-*` onward** previews org networking, ECS vs EKS trade space, edges, resilience & cost framing—ethical learner accounts only |
| Reliability rituals (`20-*`) | Rollbacks, backup/restore rehearsals, rollout strategy narratives |
| Incident labs (`21-*`) | Controlled chaos across cluster, nets, pipelines, datastore edges |
| Performance (`22-*`) | Symfony Profiler, Go `pprof`, Redis caches, Postgres plans, synthetic load tooling |
| Platform engineering arcs (`23-*`) | Golden paths templates summarising repeatable paved roads |

## Reference materials *(verify listings stay current)*

| Track | Surface | Guidance |
|-------|---------|-----------|
| Linux starter | LinuxJourney | Core modules reinforcing shell/systemd/logs |
| Linux course | Marketplace “Linux Administration Bootcamp” (titles vary)| Skip enterprise-only tangents unless you branch deliberately |
| Docker + Kubernetes practical course | Frequently titled **“Docker & Kubernetes: Practical Guide”** style offerings | Fits Docker → networking → Kubernetes → partial Helm scaffolding; deepen AWS/observability here in vault worksheets |
| K8s exam-prep supplements | KodeKloud CKA flavours / similar | Disposable clusters—not production tenants |
| Observability backends | Grafana, Prometheus, Loki, OTLP Collector, Jaeger/Tempo docs | Compose minimal stacks; watch resource burn |
| Scanners | Trivy, optional Syft/Grype, GitLab Ultimate security tiers if licensed | Tune severities thoughtfully |
| Performance | Symfony Profiler docs, Go `pprof` guide, Postgres performance primers | Cross-link `MySQL-Database-Engineering` parallels for relational debugging habits |
| AWS | Official Foundations + IAM guides + Well-Architected primer | Honour spend alarms + least-privilege rehearsals |

## Baseline toolchain hint (Ubuntu-oriented)

After `sudo apt update`, habitual helpers often include `htop`, `tmux`, `jq`, `curl`, `rsync`, `tree`, `vim`; reconcile `net-tools` nostalgia vs `ip`/`ss` modern defaults consciously.

Maintain a lab workspace such as `opslab/` for reproducible scripted exercises and incident notebooks scrubbed of secrets.
