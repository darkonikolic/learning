# Napomene za dalje — Što naučiti nakon graduation projekta

## HTTPS od prvog dana

Svaki lokalni setup u ovom pathu koristi nginx kao reverse proxy ispred aplikacije. App kontejner nikad nije direktno eksponiran prema hostu — uvijek ide kroz nginx koji drži TLS certifikat.

Pattern koji se ne mijenja:

```
Browser → nginx :443 (TLS) → app :8080 (interni network)
```

Certifikat se mijenja po okruženju (mkcert lokalno, ACM na AWS), ali nginx pattern ostaje isti. Naučiš ga u oblasti 01, koristiš svuda.

---

Nakon završetka graduation projekta, ovo su prirodni sljedeći koraci. Sortirani po prioritetu.

---

## 1. API Versioning

**Zašto:** Jednom kada frontend i mobilni klijenti počnu koristiti API, mijenjanje API-ja bez verzioniranja znači breaking change za sve klijente.

**Pristupi:**
```
URL versioning (najpraktičniji):
  /api/v1/auth/login   ← stara verzija (ostaje raditi)
  /api/v2/auth/login   ← nova verzija (dodana polja)

Header versioning:
  Accept: application/vnd.api+json;version=2

Query param versioning:
  /api/auth/login?api_version=2
```

**Implementacija u Go:**
```go
// Router setup
v1 := mux.PathPrefix("/api/v1").Subrouter()
v1.HandleFunc("/auth/login", authHandler.LoginV1).Methods("POST")

v2 := mux.PathPrefix("/api/v2").Subrouter()
v2.HandleFunc("/auth/login", authHandler.LoginV2).Methods("POST")
```

**Kada početi:** Kada imaš eksternog klijenta (mobilna app, partner API). Za interni SPA (Vue) — URL versioning je dovoljan.

**Za naučiti:** OpenAPI/Swagger spec za dokumentaciju svake verzije.

---

## 2. Kubernetes Cluster Upgrade

**Zašto:** EKS verzija 1.29 postaje end-of-life → AWS prestaje s podrškom. Mora se upgradovati.

**Ključni koncepti:**
- EKS objavljuje novu K8s verziju otprilike svaka 3-4 mjeseca
- Minor version upgrade: 1.29 → 1.30 (ne može preskočiti verziju)
- Redosled: Control plane prvo, nodovi nakon
- Blue-green cluster upgrade: kreira novi cluster pa migrira workloade

**Terraform upgrade:**
```hcl
resource "aws_eks_cluster" "main" {
  version = "1.30"   # Promijeni s 1.29 na 1.30
  # terraform apply → upgrade control planea
}

resource "aws_eks_node_group" "main" {
  version = "1.30"   # Upgrade nodova (rolling)
}
```

**Upozorenja:**
- Provjeri kompatibilnost svih add-ona (ALB Controller, EBS CSI) s novom verzijom
- Provjeri deprecated APIs (`kubectl api-resources --verbs=list | grep -v NAME`)
- Uvijek upgrade staging PRVO

**Za naučiti:** EKS upgrade dokumentacija, `pluto` tool za deprecated API detekciju.

---

## 3. Cost Optimization — Reserved Instances i Right-sizing

**Zašto:** On-Demand instances su ~40-60% skuplje od Reserved/Savings Plans.

**Savings Plans (fleksibilniji od Reserved Instances):**
```
Compute Savings Plan: fiksna $ /sat potrošnja, 1 ili 3 godine
  1-godina, no upfront: ~23% uštede
  1-godina, all upfront: ~36% uštede
  3-godine, all upfront: ~54% uštede

Kada kupovati: kad znaš da će environment biti up > 6 mj
Terraform: aws_ce_cost_allocation_tag + ručna kupovina u konzoli
```

**Right-sizing:**
```bash
# AWS Cost Explorer → Right Sizing Recommendations
# Prikazuje: "Ova instanca koristi 15% CPU — smanji na t3.small"
aws ce get-rightsizing-recommendation \
  --service "AmazonEC2" \
  --query 'RightsizingRecommendations[*].[CurrentInstance.ResourceId,RightsizingType]' \
  --output table
```

**Spot Instances za EKS (već pokriveno u modulu 07)** — 70% uštede za dev node-ove.

**Za naučiti:** AWS Cost Explorer, Infracost (Terraform cost estimation u CI).

---

## 4. GitOps sa ArgoCD

**Zašto:** Umjesto da pipeline PUSH-uje deploymente, K8s cluster PULL-uje željeno stanje iz git-a.

```
Helm push approach (šta imamo):
  GitLab CI → helm upgrade → EKS

GitOps approach (ArgoCD):
  git push → ArgoCD detektuje promjenu → ArgoCD sync → EKS
  K8s je uvijek u sync sa git-om
```

**Ključna razlika:** Pipeline nema kubectl/kubeconfig → bolja sigurnost. ArgoCD ima web UI za pregled stanja svih deploymenta.

**Za naučiti:** ArgoCD instalacija (Helm), ApplicationSet za multi-env, sync policies.

---

## 5. Service Mesh — Istio

**Zašto:** Kada imaš 5+ servisa, mTLS, traffic management, distributed tracing postaju teži bez service mesh-a.

**Što Istio daje:**
- Automatski mTLS između svih podova (bez cert-manager po servisu)
- Traffic shifting (canary bez ALB weighted routing)
- Distributed tracing (Jaeger/Zipkin integracija)
- Circuit breaker pattern

**Upozorenje:** Istio je značajna kompleksnost. Dodati SAMO kada imaš konkretan problem koji rješava.

**Za naučiti:** Istio instalacija, VirtualService, DestinationRule, Kiali (vizualizacija).

---

## 6. Multi-region i Disaster Recovery

**Zašto:** AWS eu-west-1 region pada (rijetko, ali dešava se). 99.999% availability zahtijeva multi-region.

**Što to znači:**
- Second region (npr. eu-central-1): replika EKS clustera, cross-region RDS read replica
- Route53 health checks + failover routing
- RPO: minuti (RDS async replication), RTO: 5-15 minuta (DNS failover)

**Kada razmatrati:** Kad SLA zahtijeva > 99.9% (što znači < 8.76h downtime/god).

**Za naučiti:** Route53 failover, RDS cross-region replica, Aurora Global Database.

---

## 7. Observability — Distributed Tracing

**Zašto:** Logi i metrike govore šta i kada. Tracing govori ZAŠTO je request spor (koji servis, koji poziv).

**Stack:**
- OpenTelemetry SDK za Go i PHP (instrumentacija)
- Jaeger ili Tempo (Grafana Cloud) za storage/vizualizaciju
- Primjer: request traje 800ms — tracing pokazuje: PHP 50ms, Go 100ms, MySQL 650ms → bottleneck je query

**Za naučiti:** OpenTelemetry Go SDK, Grafana Tempo, trace → log korelacija.

---

## 8. Database — Advanced

**Connection pooling proxy:** PgBouncer (PostgreSQL) ili ProxySQL (MySQL)
- Smanjuje broj konekcija na DB
- Korisno kada imaš 50+ pod-ova koji se konektuju na MySQL

**Schema management:** Liquibase kao alternativa golang-migrate za kompleksnije migracije

**Database sharding:** Tek kada jedna instanca nije dovoljna (99% ecommerce ne dolazi do ovoga)

---

---

## 9. On-Call i Incident Management

**Zašto:** Monitoring i alerting su postavljeni — ali ko odgovara u 3 ujutro i kako?

**Što naučiti:**
- PagerDuty ili OpsGenie: on-call rotacija, eskalacijska politika
- Runbook format: standardizirani koraci za svaki tip incidenta
- Incident severity levels: P1/P2/P3/P4 sa definisanim RTO po nivou
- Post-mortem kultura: blameless post-mortem, 5 Why analiza
- Status page: Statuspage.io ili self-hosted za obavještavanje korisnika

**Minimalni runbook format:**
```
Incident: [naziv]
Severity: P1/P2/P3
Symptoms: [šta korisnici vide]
Diagnosis: [kubectl/aws komande za dijagnozu]
Mitigation: [brzi fix]
Resolution: [pravi fix]
Prevention: [kako spriječiti ponavljanje]
```

---

## 10. GDPR i Data Privacy

**Zašto:** Čim imaš EU korisnike — ovo je zakonska obaveza, ne opcija.

**Što implementirati:**
- Right to erasure (pravo na brisanje): `DELETE FROM users WHERE id = ?` + sve vezane tablice + S3 fajlovi
- Data export: korisnik može preuzeti sve svoje podatke (JSON export endpoint)
- Consent management: billing za GDPR compliance alati (CookieYes, iubenda)
- Data retention policy: automatski brisati stare podatke (CronJob)
- Privacy by design: ne skupljaj podatke koje ne trebaš

**Za naučiti:** GDPR Article 17 (erasure), Article 20 (portability), Data Processing Agreements.

---

## 11. Chaos Engineering

**Zašto:** Jedini način da znaš da sistem izdrži kvar je da ga namjerno izazoveš u kontrolisanim uvjetima.

**Alati:**
- Chaos Mesh (K8s native): kill random pods, network latency injection, disk failures
- AWS Fault Injection Simulator (FIS): simulira EC2, RDS, AZ outage-ove

**Primjeri eksperimenata:**
```
Experiment 1: Što se desi kada MySQL replica pukne?
  → App mora raditi (degraded, sve ide na master)

Experiment 2: Što se desi kada email worker crashne?
  → Emailovi moraju biti u queue, worker restart ih šalje

Experiment 3: Što se desi kada Redis pukne?
  → Session loss, ali app ne smije crashnuti
```

**Za naučiti:** Game Day procedure, hypothesis-driven chaos experiments.

---

## 12. Compliance (SOC2 / ISO 27001)

**Zašto:** Enterprise klijenti često zahtijevaju compliance certifikate.

**SOC2 Type II:** Audit sigurnosnih kontrola tokom perioda (obično 6-12 mj)
- Relevantni Trust Service Criteria: Security, Availability, Confidentiality
- Kontrole koje ovaj path pokriva: ✓ Access control (IAM/RBAC), ✓ Encryption (TLS/KMS), ✓ Monitoring (CloudTrail), ✓ Incident response

**Šta još treba za SOC2:**
- Vendor risk management (treće strane)
- Background checks za zaposlenike
- Formal change management process
- Business continuity plan

**Za naučiti:** Vanta ili Drata (compliance automation), SOC2 readiness assessment.

---

## Što ovaj path NAMJERNO ne pokriva

```
Multi-cloud strategija     → AWS je dovoljan za početak; GCP/Azure su 80% isti
Change Advisory Board      → Organizacijski proces, ne tehnički
Legal/Regulatory specifics → Ovisi o industriji (healthcare=HIPAA, finance=PCI-DSS)
Chaos engineering          → Tek kada je sistem stabilan > 3 mj u produkciji
SOC2/ISO27001              → Tek kada klijenti eksplicitno zahtijevaju
```

---

## Preporučeni redosled učenja

```
Odmah nakon graduation:
  1. API versioning          → produktivno odmah
  2. Cost optimization       → ušteda odmah
  3. K8s cluster upgrade     → operational necessity
  4. Runbook pisanje         → pripremi se prije prvog incidenta

Nakon 3-6 mjeseci u produkciji:
  5. GitOps (ArgoCD)         → bolja sigurnost, bolji pregled
  6. Distributed tracing     → debugging u distribuiranom sistemu
  7. On-call setup           → PagerDuty ili OpsGenie

Kad naraste tim/produkt:
  8. GDPR implementacija     → čim imaš EU korisnike
  9. Service mesh (Istio)    → > 5 servisa
  10. Multi-region DR        → SLA > 99.9%
  11. Chaos engineering      → kad je sistem stabilan > 3 mj
  12. SOC2/ISO27001          → kad enterprise klijenti zahtijevaju
```
