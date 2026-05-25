# Ops / Platform / Cloud — mindset and phased roadmap

This path supports **hands-on comprehension** of how modern backends are **built**, **tested**, **packaged**, **distributed**, **deployed**, **observed**, **maintained**, **incident-handled**, and **safely improved** — not trivia memorised separately from systemic behaviour.

## What deep understanding means here

How an artefact survives from source control curiosity into repeatable production behaviours: pipelines, artefacts, rollout surfaces, observable runtime, corrective action, guarded evolution.

## Area map (numeric order = topic progression)

```
01  Overview & scope
── FUNDAMENT ──────────────────────────────────────────────────────────────────
02  Linux administration        Host triage, bash scripting, systemd, ssh
03  Shell scripting for ops     set -euo pipefail, jq, yq, idempotency, trap, retry
04  Python for ops              boto3, subprocess, requests, click, K8s client
05  Git & release workflow      Branches, merges, tags, recovery
06  Network flow                DNS, TLS, NAT, routing, firewall
── CONTAINERS ─────────────────────────────────────────────────────────────────
07  Docker                      Images, Dockerfile, compose, multi-stage, hardening
08  Podman + Quadlets           Rootless runtime, systemd-native Quadlet units
09  Container networking        Bridges, DNS, NAT, inter-service communication
── KUBERNETES & HELM ──────────────────────────────────────────────────────────
10  Kubernetes                  Workloads, RBAC, networking, storage, ingress, ops
11  Helm                        Charts, values, lifecycle, OCI registry, GitOps
── INFRASTRUCTURE AS CODE ─────────────────────────────────────────────────────
12  Terraform + LocalStack + CDK  State, modules, drift, local AWS testing, CDK intro
13  Ansible                     Playbooks, roles, vault, dynamic inventory, EC2 fleet
── CI/CD & DELIVERY ───────────────────────────────────────────────────────────
14  GitLab CI/CD                Pipelines, runners, docker build, gates, deploy
15  DevSecOps / supply chain    Scanners, SBOM, SAST, secret scan, pipeline gates
16  Production reliability      Blue/green, canary, rollbacks, DR, postmortem
── AWS ────────────────────────────────────────────────────────────────────────
17  AWS                         IAM, VPC, EC2, RDS, S3, ALB, ECS Fargate, EKS,
                                CloudFront, WAF, Secrets, DR + Fargate lab +
                                CodePipeline/CodeDeploy
── OBSERVABILITY ──────────────────────────────────────────────────────────────
18  Edge / reverse proxy        Nginx, Traefik, TLS termination, LB, traffic shaping
19  Prometheus & PromQL         Golden signals, scrape, exporters, alerting
20  Loki & logging              Structured logs, correlation, forensic discipline
21  OpenTelemetry & tracing     Spans, context propagation, sampling, collector
22  Unified observability       Grafana multi-signal, SLOs, error budgets, incidents
23  Secrets management          Vault, K8s secrets, rotation, CI variable hygiene
24  Incident troubleshooting    K8s, networking, datastore, pipeline scenario labs
25  Performance optimization    Profiling, bottleneck triage, load testing
26  Platform engineering        IDPs, golden paths, self-service, paved roads
```
