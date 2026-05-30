# 05 — Trivy i Vulnerability Scanning

## Trivy — opseg skeniranja za project-a

Trivy nije samo image scanner. Za naš stack pokriva:

| Tip skeniranja | Šta pronalazi | Kada pokrenuti |
|---|---|---|
| `trivy image` | OS paketi, language libs, secret u image layerima | Na svaki push, blokirajući |
| `trivy config` | IaC misconfigurations (Terraform, K8s YAML) | Na svaki Terraform plan |
| `trivy fs --scanners secret` | Hardkodirani credentials u source kodu | Na svaki push |
| `trivy sbom` | Ranjivosti u SBOM fajlu | Periodično, compliance |
| `trivy k8s` | Running K8s workload scan | Sedmično, na clusteru |

---

## GitLab CI — kompletan trivy pipeline

```yaml
# .gitlab-ci.yml

variables:
  TRIVY_VERSION: "0.50.0"
  TRIVY_CACHE_DIR: "$CI_PROJECT_DIR/.trivycache"
  # Non-interactive mode
  TRIVY_NO_PROGRESS: "true"
  TRIVY_TIMEOUT: "10m0s"

.trivy-base:
  image: aquasec/trivy:$TRIVY_VERSION
  cache:
    key: trivy-db-$CI_COMMIT_REF_SLUG
    paths:
      - $TRIVY_CACHE_DIR/
  before_script:
    # Update vulnerability DB (jednom po cache expiry, ne po jobu)
    - trivy image --download-db-only

# ============================================================
# Posao 1: Image scanning — blokirajući za HIGH/CRITICAL
# ============================================================
trivy-image:
  extends: .trivy-base
  stage: security
  script:
    # Skeniranje go-service image-a
    - |
      trivy image \
        --exit-code 1 \
        --severity HIGH,CRITICAL \
        --ignore-unfixed \
        --format template \
        --template "@/contrib/gitlab.tpl" \
        --output gl-container-scanning-go.json \
        --ignorefile .trivyignore \
        "$CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA"

    # Skeniranje php-service image-a
    - |
      trivy image \
        --exit-code 1 \
        --severity HIGH,CRITICAL \
        --ignore-unfixed \
        --format template \
        --template "@/contrib/gitlab.tpl" \
        --output gl-container-scanning-php.json \
        --ignorefile .trivyignore \
        "$CI_REGISTRY_IMAGE/php-service:$CI_COMMIT_SHA"

    # Skeniranje nginx image-a
    - |
      trivy image \
        --exit-code 1 \
        --severity HIGH,CRITICAL \
        --ignore-unfixed \
        --format template \
        --template "@/contrib/gitlab.tpl" \
        --output gl-container-scanning-nginx.json \
        --ignorefile .trivyignore \
        "$CI_REGISTRY_IMAGE/nginx:$CI_COMMIT_SHA"

  artifacts:
    reports:
      container_scanning: gl-container-scanning-*.json
    expire_in: 90 days  # Čuvati za audit
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_PIPELINE_SOURCE == "merge_request_event"

# ============================================================
# Posao 2: IaC scanning — Terraform misconfigurations
# ============================================================
trivy-iac:
  extends: .trivy-base
  stage: security
  script:
    - |
      trivy config \
        --exit-code 1 \
        --severity HIGH,CRITICAL \
        --format template \
        --template "@/contrib/gitlab.tpl" \
        --output gl-sast-iac.json \
        --ignorefile .trivyignore \
        terraform/

    # K8s YAML skeniranje
    - |
      trivy config \
        --exit-code 1 \
        --severity HIGH,CRITICAL \
        --format template \
        --template "@/contrib/gitlab.tpl" \
        --output gl-sast-k8s.json \
        --ignorefile .trivyignore \
        k8s/

  artifacts:
    reports:
      sast: gl-sast-*.json
    expire_in: 90 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - terraform/**/*
        - k8s/**/*

# ============================================================
# Posao 3: Secret scanning u source kodu
# ============================================================
trivy-secrets:
  extends: .trivy-base
  stage: security
  script:
    - |
      trivy fs \
        --scanners secret \
        --exit-code 1 \
        --format template \
        --template "@/contrib/gitlab.tpl" \
        --output gl-secret-detection.json \
        --ignorefile .trivyignore \
        .

  artifacts:
    reports:
      secret_detection: gl-secret-detection.json
    expire_in: 90 days
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_PIPELINE_SOURCE == "merge_request_event"

# ============================================================
# Posao 4: SBOM generisanje (samo na main, za compliance)
# ============================================================
trivy-sbom:
  extends: .trivy-base
  stage: security
  script:
    - |
      for SERVICE in go-service php-service nginx; do
        trivy image \
          --format cyclonedx \
          --output "sbom-${SERVICE}.json" \
          "$CI_REGISTRY_IMAGE/${SERVICE}:$CI_COMMIT_SHA"
      done

    # Upload SBOM u S3 za long-term retention
    - |
      aws s3 cp sbom-*.json \
        "s3://project-a-compliance/sbom/$CI_COMMIT_SHA/" \
        --recursive

  artifacts:
    paths:
      - sbom-*.json
    expire_in: 5 years  # SBOM dugoročno za compliance audite
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ============================================================
# Posao 5: Running cluster scan (scheduled, ne per-push)
# ============================================================
trivy-cluster:
  extends: .trivy-base
  stage: security
  script:
    - aws eks update-kubeconfig --name project-a-prod --region eu-west-1
    - |
      trivy k8s \
        --exit-code 0 \
        --severity HIGH,CRITICAL \
        --report summary \
        --format template \
        --template "@/contrib/gitlab.tpl" \
        --output gl-k8s-scan.json \
        --namespace project-a \
        cluster

  artifacts:
    paths:
      - gl-k8s-scan.json
    expire_in: 30 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        SCAN_TYPE: "cluster"
```

---

## Triage policy — šta znači koji severity

**CRITICAL + exploit postoji + network reachable:**  
Build blokiran. Nema merge, nema deploy. Fix odmah ili eksplicitni `.trivyignore` unos sa justifikacijom i JIRA tiketom.

**CRITICAL + no known exploit:**  
Build blokiran. Ali može se dodati u `.trivyignore` sa `--ignore-unfixed` flagom ako patch nije dostupan. `ignore-unfixed` je globalna opcija — pazi da ne ignorišeš previše.

**HIGH severity:**  
`--exit-code 0` u MR jobovima (warn, ne blok). `--exit-code 1` na main branch. Obavezno planirati fix unutar 30 dana.

**MEDIUM:**  
Logovan u artifact, prikazan u GitLab Security Dashboard. Quarterly review.

**LOW:**  
Ignorisan u pipeline-u (`--severity HIGH,CRITICAL`). Annual review.

---

## .trivyignore — disciplina u upravljanju izuzecima

```
# .trivyignore
# Svaki unos MORA imati:
# - CVE-ID
# - Datum review-a
# - Razlog (zašto je prihvatljiv rizik)
# - Rok za revisit ili fix

# Format:
# CVE-YYYY-XXXXX  # [DATE REVIEWED] [REASON] [FIX-BY or PERMANENT]

# Go stdlib — koristimo samo HTTPS, ne HTTP server koji je pogođen
# Reviewed: 2024-02-15 | HTTP/2 header exhaustion DoS, naš servis ne eksponira H2 direktno
# Fix-by: 2024-04-01 (Go 1.22.1 fix)
CVE-2023-45288

# Alpine musl — samo eksploitabilan uz local code execution, container nema shell
# Reviewed: 2024-01-10 | Local-only exploit, scratch image bez shell-a
# Permanent (dok se Alpine ne ažurira automatski putem Renovate)
CVE-2023-51780

# OpenSSL — koristimo 1.3.0+ koji nije pogođen
# Reviewed: 2024-03-05 | Affects 3.0.x, mi koristimo 3.2.x
# Remove when: Alpine 3.20 postane stable
CVE-2024-0727
```

**Audit .trivyignore periodično:**

```bash
#!/bin/bash
# scripts/audit-trivyignore.sh
# Provjera da li ignorisane CVE-je imaju fix sada

while IFS= read -r line; do
    [[ "$line" =~ ^CVE ]] || continue
    CVE=$(echo "$line" | cut -d' ' -f1)
    
    # Provjeriti da li postoji fix
    RESULT=$(trivy image --list-all-pkgs --format json "alpine:3.19" 2>/dev/null | \
        jq --arg cve "$CVE" '.Results[].Vulnerabilities[]? | select(.VulnerabilityID == $cve) | .FixedVersion')
    
    if [ -n "$RESULT" ]; then
        echo "FIX AVAILABLE for $CVE: $RESULT — remove from .trivyignore"
    fi
done < .trivyignore
```

---

## SBOM za compliance

Software Bill of Materials je inventar svih komponenti u image-u. Potreban za:
- SOC 2 Type II audit
- ISO 27001
- GDPR (znate šta vaša aplikacija procesira)
- Incident response (brzo identificirati koji projekti su pogođeni novom ranjivošću)

```bash
# Generisanje SBOM
trivy image \
    --format cyclonedx \
    --output sbom-go-service.json \
    123456789012.dkr.ecr.eu-west-1.amazonaws.com/project-a/go-service:sha256-abc123

# SBOM sadrži:
# - sve Go module dependency-je sa verzijama
# - OS pakete (Alpine apk)
# - licencne informacije
# - hash svakog paketa

# Provjera ranjivosti u SBOM fajlu (korisno za offline analizu)
trivy sbom sbom-go-service.json

# Kada nova CVE izaše, provjera svih SBOM-a bez rebuild-a image-a:
for SBOM in s3://project-a-compliance/sbom/*/sbom-*.json; do
    aws s3 cp "$SBOM" /tmp/current-sbom.json
    trivy sbom --exit-code 1 --severity CRITICAL /tmp/current-sbom.json
done
```

---

## Trivy u produkcijskom K8s clusteru — kontinuirano skeniranje

```hcl
# Trivy Operator — kontinuirano skeniranje running workloada
resource "helm_release" "trivy_operator" {
  name       = "trivy-operator"
  repository = "https://aquasecurity.github.io/helm-charts"
  chart      = "trivy-operator"
  version    = "0.20.0"
  namespace  = "trivy-system"
  create_namespace = true

  set {
    name  = "trivy.ignoreUnfixed"
    value = "true"
  }

  set {
    name  = "operator.scannerReportTTL"
    value = "24h"
  }

  # Scan policy: na svaki novi image push
  set {
    name  = "operator.vulnerabilityScannerEnabled"
    value = "true"
  }

  set {
    name  = "operator.configAuditScannerEnabled"
    value = "true"  # K8s config (securityContext, RBAC)
  }
}
```

Trivy Operator kreira `VulnerabilityReport` CRD za svaki radni workload:

```bash
# Prikaz vulnerability report za go-service
kubectl get vulnerabilityreports -n project-a -o wide

# Detaljni report
kubectl describe vulnerabilityreport replicaset-go-service-7d9f8b-go-service -n project-a

# Sve CRITICAL ranjivosti u namespace-u
kubectl get vulnerabilityreports -n project-a -o json | \
    jq '.items[].report.vulnerabilities[] | select(.severity == "CRITICAL") | 
    {resource: .resource, pkg: .installedVersion, cve: .vulnerabilityID, fix: .fixedVersion}'
```

---

## Grype — alternativa za offline ili air-gapped okruženja

```yaml
# .gitlab-ci.yml — Grype kao alternativni/paralelni scanner
grype-scan:
  image: anchore/grype:v0.73.0
  stage: security
  script:
    - grype "$CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA" \
        --fail-on high \
        --output template \
        --template /tmp/gitlab.tmpl
  # Koristiti zajedno sa Trivy za cross-validaciju nalaza
  allow_failure: true  # Secondary scanner, ne primarni gate
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

Grype vs Trivy za project-a:
- Trivy: širi scope (IaC, secrets, K8s), bolji GitLab integracija
- Grype: brži za čisti image scan, offline mode sa `grype db update`
- Preporuka: Trivy kao primarni CI gate, Grype za lokalni dev provjere

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi sigurnosne skenove. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 16: Sigurnost ===

security-scan-all: ## Pokreni sve security skenove: trivy + tfsec + kubesec
	@$(MAKE) trivy-scan
	@$(MAKE) tf-security
	@echo "Pokreni kubesec zasebno na svakom YAML-u: make kubesec-scan FILE=deployment.yaml"

kubesec-scan: ## Skeniraj Kubernetes manifest za sigurnosne probleme (FILE=deployment.yaml make kubesec-scan)
	docker run --rm \
	  -v $(PWD):/data \
	  kubesec/kubesec:latest scan /data/$(FILE)
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
make security-scan-all
FILE=k8s/deployment.yaml make kubesec-scan
make help | grep security
make help | grep kubesec
```
