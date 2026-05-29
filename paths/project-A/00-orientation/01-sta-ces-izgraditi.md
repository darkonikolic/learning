# Šta ćeš izgraditi

Na kraju ovog patha imaš multi-service aplikaciju sa login funkcionalnošću koja radi u produkciji na AWS EKS. Stack je production-grade: Vue.js SPA, PHP API proxy, Go backend, MySQL master/replica, Redis — sve orkestrirano Helmom, sve infrastrukture kroz Terraform, sve tajne u AWS Secrets Manageru.

## Arhitektura sistema

```
Browser
  └── Vue.js SPA (HTTPS)
         │
         ▼ HTTP/JSON
       nginx:1.25-alpine
       (reverse proxy + static files)
         │
         ├── /api/*  ──► PHP 8.3-fpm-alpine (API proxy)
         │                    │
         │                    ▼ HTTP/JSON
         │               Go 1.22 (scratch)
         │               business logic service
         │                    │
         │           ┌────────┼────────────┐
         │           ▼        ▼            ▼
         │      MySQL 8.0  MySQL 8.0   Redis 7
         │      Master     Replica     (cache +
         │      (write)    (read)       session)
         │
         └── /*      ──► Vue.js SPA (static build)
```

**Login flow:** Vue login form → `POST /api/auth` → PHP proxy → Go validates → MySQL user lookup → Redis session → JWT response → Vue stores JWT → authenticated.

## Docker images (5)

| Image | Baza | Svrha |
|-------|------|-------|
| `nginx:1.25-alpine` | — | Reverse proxy + Vue static files |
| `node:20-alpine → nginx:alpine` | multi-stage | Vue.js SPA build |
| `php:8.3-fpm-alpine` | — | PHP API proxy service |
| `golang:1.22-alpine → scratch` | multi-stage | Go business logic |
| `mysql:8.0` + `redis:7-alpine` | — | Data layer |

## Finalni URLovi

```
https://app.firma.com              ← produkcija
https://app.dev.firma.com          ← development
https://app.staging.firma.com      ← staging
https://mr-42.dev.firma.com        ← review env za MR #42 (dinamično)
https://monitoring.firma.com       ← Grafana prod
https://monitoring.dev.firma.com   ← Grafana dev
```

## Repo strategija — svjesna odluka

**Mono-repo.** Svi servisi, infrastruktura i testovi žive u jednom repozitorijumu.

```
project-a/
├── services/frontend/    ← Vue.js
├── services/php-service/ ← PHP proxy
├── services/go-service/  ← Go backend
├── helm/                 ← Helm chart
├── terraform/            ← Infrastruktura
├── tests/e2e/            ← Playwright
└── .gitlab-ci.yml
```

**Zašto mono-repo (i zašto je to ispravna odluka, ne kompromis):**

`docker compose up` pokreće cijeli stack. Nema developera koji kaže "moram mockati PHP jer nemam Go lokalno" — obje su tu. Svi integration bug-ovi se otkrivaju lokalno, ne na stagingu. Atomski commit kada se mijenja API kontrakt između PHP i Go.

Za 90% ecommerce projekata mono-repo nikad ne postaje problem. Jedini realni razlozi za ekstrakciju: PCI-DSS compliance za payment servis, ili shared service koji koriste 5+ različitih produkata. Sve ostalo — katalog, košarica, narudžbe, admin — ostaje u mono-repo.

**Path-based CI** sprečava build svih servisa pri svakom commitu:
```yaml
build:go:
  rules:
    - changes: [services/go-service/**/*]
```

## Tri ne-pregovaračka principa

### 1. Docker everywhere — nula bare metal

Ni jedan alat se ne instalira lokalno. Terraform, kubectl, helm, aws CLI, mysql client — sve se pokreće kao Docker kontejner. Verzije su zaključane, tim radi identično okruženje.

```bash
# Ne: terraform plan
docker run --rm -v $(pwd):/workspace -w /workspace \
  hashicorp/terraform:1.7 plan

# Ne: kubectl get pods
docker run --rm -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get pods -n app-dev

# Ne: mysql -u root -p
docker run --rm -it mysql:8.0 \
  mysql -h rds.firma.internal -u app -p"${DB_PASS}" appdb
```

### 2. Secrets u AWS SM — nula plaintext credentials bilo gde

Nema credentials u `.env` fajlovima koji idu na git. Nema hardkodovanih lozinki u `values.yaml`. Nema `DB_PASSWORD=secret123` u GitLab CI variables (ni tamo, u External Secrets Operatoru).

Jedini izuzetak: `.env.local` za lokalni dev (git-ignored), koji nikad ne sadrži produkcione tajne.

```
Produkcija/Dev/Staging → AWS Secrets Manager → External Secrets Operator
                         → K8s Secret → montiran kao env var u container
```

### 3. Terraform create i destroy — ephemeral sve osim prod

Svaki resurs koji Terraform napravi, Terraform može obrisati. Nema ručno kreiranog resursa van Terraforma. `terraform destroy` mora raditi pouzdano — to je onaj koji štedi novac.

```
dev/staging/review → ephemeral (destroy posle MR / kraj radnog dana)
prod               → trajan, ali Terraform-managed (nikad klikanjem u konzoli)
```

## Graduation project: šta isporučuješ

- **Radeća login stranica**: `https://app.firma.com` — email + password → Hello World, {email}
- **Multi-service K8s deployment**: svih 5 servisa, health checks, resource limits, HPA
- **Kompletan pipeline**: build → scan → Terraform plan → deploy → smoke test → optional destroy
- **Secrets management**: nula plaintext, External Secrets Operator konfigurisan
- **Monitoring**: Prometheus metrike za svaki servis, Grafana dashboard, Loki logovi
- **Review environments**: `mr-{broj}.dev.firma.com` sa sopstvenom DB kopijom, auto-destroy na MR close
- **Infrastruktura kao kod**: `terraform apply` u dev → identično okruženje u stagingu i produ

## Redosled modula

Svaki modul gradi na prethodnom. Princip: **ručno → Terraform → pipeline**.

```
00  Orientation — šta gradiš, principi, redosled
01  Docker — 5 servisa lokalno, config, volumes, targets
02  GitLab CI — osnove, registry, image build
03  Kubernetes — LOCAL (kind), workloads, networking
04  Helm — chart, values per env
05  Terraform fundamenti — IaC, state, destroy
06  AWS koncepti — VPC, EKS, RDS, IAM
07  AWS RUČNO — konzola, credentials, manual create/destroy
08  Terraform AWS — ista infrastruktura kao 07, ali kod
09  Shutdown i resume — cost management, destroy workflow
10  GitLab Pipelines — CI/CD, env lifecycle via pipeline
11  Monitoring — Prometheus, Grafana, Loki, SLO
12  AI-assisted DevOps — workflow sa Claude
13  Aplikacija arhitektura — Vue+PHP+Go, email, JWT, feature flags
14  AWS RDS + ElastiCache — MySQL master/slave, Redis, backup
15  AWS Secrets Manager — zero plaintext, External Secrets
16  Sigurnost — container, AppSec, cert-manager
17  DB kopija okruženja — mysqldump, pipeline
18  SSH i produkcija — SSM, kubectl exec, self-service
19  Load Balancer — ALB konzola + K8s Ingress
20  Testiranje — Go/PHP unit, Playwright, synthetic
21  Xdebug i Delve — radeći debug PHP i Go
22  Deployment strategije — Rolling, Blue-Green, Canary
23  DB migracije — golang-migrate, expand-contract
24  AppSec — OWASP, SAST, DAST, dependency scan
25  Performance testing — k6, SLO, profiling
26  Async i queues — Redis Streams, Worker, CronJobs
27  gRPC — notification service, protobuf, Go-to-Go
28  GRADUATION — kompletan stack od koda do produkcije
```
