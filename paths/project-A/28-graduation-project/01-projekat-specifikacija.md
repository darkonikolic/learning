# Graduation Project — Specifikacija

## Šta gradiš

Multi-service web aplikacija sa login funkcionalnošću. Minimalan feature set, maksimalan infrastrukturni kompleksitet — ovo je template za svaki produkcioni projekat koji dolazi posle.

## Funkcionalna specifikacija aplikacije

**Login stranica** (`/`)
- Email + password forma
- Submit → `POST /api/auth` sa JSON body `{"email": "...", "password": "..."}`
- Uspješan login → `200 OK` + JWT → Vue prikazuje: **"Hello World, user@firma.com"**
- Neuspješan login → `401 Unauthorized` → Vue prikazuje error poruku ispod forme
- JWT se čuva u `localStorage`, šalje se u `Authorization: Bearer <token>` header na API pozive
- `/api/health` → `200 OK {"status":"ok","service":"php"}` (health check endpoint)

**Login flow kroz stack:**
```
Vue form → POST /api/auth
         → nginx proxy → PHP service → Go service
                                     → MySQL: SELECT user WHERE email=? AND password_hash=?
                                     → Redis: SET session:{uuid} {user_json} EX 3600
                                     → Go → PHP: {token: "jwt...", user: {email}}
                         PHP → nginx → Vue
```

## Finalni URLovi

| URL | Okruženje | Cert |
|-----|-----------|------|
| `https://app.firma.com` | AWS EKS prod | ACM |
| `https://app.dev.firma.com` | AWS EKS dev | ACM |
| `https://app.staging.firma.com` | AWS EKS staging | ACM |
| `https://mr-42.dev.firma.com` | AWS EKS review | ACM wildcard `*.dev.firma.com` |
| `https://app.local` | kind (lokalno) | self-signed |

## Repo struktura

```
project-a/
├── services/
│   ├── nginx/
│   │   ├── Dockerfile               # FROM nginx:1.25-alpine
│   │   └── nginx.conf               # reverse proxy config
│   ├── frontend/
│   │   ├── Dockerfile               # multi-stage: node:20-alpine → nginx:alpine
│   │   ├── src/
│   │   │   ├── App.vue
│   │   │   ├── main.js
│   │   │   └── components/
│   │   │       └── LoginForm.vue
│   │   ├── package.json
│   │   └── vite.config.js
│   ├── php-service/
│   │   ├── Dockerfile               # FROM php:8.3-fpm-alpine
│   │   ├── public/
│   │   │   └── index.php            # entry point
│   │   ├── src/
│   │   │   └── AuthController.php
│   │   └── composer.json            # slim/slim + guzzlehttp/guzzle
│   └── go-service/
│       ├── Dockerfile               # multi-stage: golang:1.22-alpine → scratch
│       ├── main.go
│       ├── internal/
│       │   ├── auth/
│       │   │   └── handler.go
│       │   ├── db/
│       │   │   └── mysql.go         # master write, replica read
│       │   └── cache/
│       │       └── redis.go
│       └── go.mod
├── helm/
│   └── project-a/
│       ├── Chart.yaml
│       ├── values.yaml              # defaults
│       └── values/
│           ├── local.yaml           # kind dev, pullPolicy: Never
│           ├── dev.yaml             # AWS dev, ECR image, RDS endpoint
│           ├── staging.yaml
│           └── prod.yaml            # replica count 2+, PDB, strict resources
├── terraform/
│   ├── bootstrap/
│   │   └── main.tf                  # S3 state bucket + DynamoDB lock (jednom)
│   ├── modules/
│   │   ├── vpc/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── eks/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── rds/                     # MySQL 8.0 master + read replica
│   │   │   ├── main.tf              # aws_db_instance x2 + subnet group
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf           # outputs: master_endpoint, replica_endpoint
│   │   ├── elasticache/             # Redis 7
│   │   │   ├── main.tf              # aws_elasticache_replication_group
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── iam/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   └── envs/
│       ├── dev/
│       │   ├── main.tf
│       │   ├── dev.tfvars
│       │   └── backend.tf
│       ├── staging/
│       │   ├── main.tf
│       │   ├── staging.tfvars
│       │   └── backend.tf
│       ├── prod/
│       │   ├── main.tf
│       │   ├── prod.tfvars
│       │   └── backend.tf
│       └── dynamic/
│           ├── main.tf              # review environments (mr-{N})
│           └── variables.tf         # var: mr_number, branch_slug
├── docker-compose.yml               # lokalni dev: svih 7 kontejnera
└── .gitlab-ci.yml                   # kompletan pipeline
```

## Prerekviziti

**Završeni moduli 01–10** — pretpostavlja se da znaš pisati Dockerfile, Helm chart, `.gitlab-ci.yml`, Terraform module, i da si deployjao na EKS bar jednom.

**Nalozi i alati:**
- AWS nalog — IAM user sa: `IAM`, `VPC`, `EKS`, `RDS`, `ElastiCache`, `S3`, `Route53`, `ACM`, `SecretsManager`, `EC2`
- GitLab nalog — projekt sa enabled Container Registry
- Domen pod kontrolom (DNS NS ili hosted zone u Route53)
- Docker Desktop

**Ne treba lokalno instalirati:** terraform, kubectl, helm, aws CLI, go, node, php, mysql-client — sve se pokreće kao Docker image.

## AWS troškovi — procjena po okruženju

Ovo je zašto `terraform destroy` mora biti automatizovan.

### Dev okruženje (EKS + RDS + ElastiCache + ALB + NAT)

| Resurs | Spec | $/sat | $/dan (8h rad) |
|--------|------|-------|----------------|
| EKS control plane | managed | $0.10 | $0.80 |
| EC2 node group | 2x t3.medium | $0.083 | $0.66 |
| RDS MySQL master | db.t3.micro | $0.017 | $0.14 |
| RDS MySQL replica | db.t3.micro | $0.017 | $0.14 |
| ElastiCache Redis | cache.t3.micro | $0.017 | $0.14 |
| ALB | 1 kom | $0.008 | $0.06 |
| NAT Gateway | 1 AZ | $0.045 | $0.36 |
| **Ukupno** | | **~$0.29/h** | **~$2.30/dan** |

### Review env (ephemeral, po MR-u)

Review env dijeli EKS cluster sa dev-om (namespace izolacija), ali dobija sopstvenu RDS instancu i ElastiCache za izolovano testiranje. Troši ~$0.08/h dok je aktivan, auto-destroy na MR close.

### Staging i Prod

Staging = dev spec + multi-AZ RDS (~$0.50/h).
Prod = t3.large nodovi, Multi-AZ RDS, Redis cluster mode, Reserved instances ako je dugoročno.

**Pravilo:** Destroy dev i staging kad ne radiš. Ukupno za učenje: ~$20–40.
