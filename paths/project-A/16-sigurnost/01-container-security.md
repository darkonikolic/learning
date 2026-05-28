# 01 — Container Security

## CIS Docker Benchmark — ključne točke za project-a

CIS Docker Benchmark dokumentira 80+ kontrola. Za naš stack, kritične su:

**4.1 — Non-root user:** Container procesi koji rade kao root su direktan eskalacijski vektor. Container escape (ranjivost u container runtimeu) + root process = root na hostu.

**4.6 — HEALTHCHECK instrukcija:** K8s liveness/readiness probe ne zamjenjuje Docker HEALTHCHECK — ali za K8s deploje, probe konfiguracija je dovoljna.

**4.9 — ADD umjesto COPY:** `ADD` može raspakivati arhive i fetchati URL-ove — potencijalni vektor za supply chain napad. Uvijek koristiti `COPY`.

**5.25 — Container memory limit:** Bez memory limit, jedan container može konzumirati sav host memory (DoS). Uvijek setovati `resources.limits.memory` u K8s.

---

## Dockerfile security checklist za project-a

### Go service — production Dockerfile

```dockerfile
# go-service/Dockerfile

# Build stage — koristiti specifičan digest, ne samo tag
FROM golang:1.22.3-alpine3.19@sha256:cdc86d9f363e8786845bea2040312b4efa321b828acdeb26f393faa864d533d AS builder

WORKDIR /app

# Kreirati non-root user u build stageu
RUN addgroup -g 10001 -S appgroup && \
    adduser -u 10001 -S appuser -G appgroup

# Kopiraj samo dependency fajlove prvo (bolji layer caching)
COPY go.mod go.sum ./
RUN go mod download && go mod verify  # verify = checksum validation

# Kopiraj source
COPY . .

# Build sa sigurnosnim flagovima
RUN CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64 \
    go build \
    -ldflags="-w -s -extldflags '-static'" \
    -trimpath \
    -o /app/server \
    ./cmd/server

# Verify binary nije linked
RUN ldd /app/server 2>&1 | grep -q "not a dynamic executable" || \
    { echo "Binary is dynamically linked!"; exit 1; }

# Final stage — scratch za minimalni attack surface
FROM scratch

# Kopiraj CA certificates (potrebni za TLS/HTTPS calls)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Kopiraj passwd/group za non-root user (scratch nema /etc/passwd)
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Kopiraj binary
COPY --from=builder /app/server /server

# Non-root user (UID 10001)
USER 10001:10001

EXPOSE 8080

ENTRYPOINT ["/server"]
```

### PHP service — production Dockerfile

```dockerfile
# php-service/Dockerfile

FROM php:8.3.7-fpm-alpine3.19@sha256:abc123def456... AS builder

# Security: pin dependency versions, --no-cache eliminira apk cache
RUN apk add --no-cache \
    libpq-dev=16.2-r0 \
    oniguruma-dev=6.9.9-r0 \
    && docker-php-ext-install -j$(nproc) pdo_mysql mbstring \
    && docker-php-ext-enable opcache

WORKDIR /var/www/html

# Composer install — bez dev dependencies, sa autoloader optimization
COPY composer.json composer.lock ./
RUN composer install \
    --no-dev \
    --no-interaction \
    --prefer-dist \
    --optimize-autoloader \
    --no-scripts  # Ne pokretati arbitrary composer scripts

COPY . .

# Ownership na www-data (uid 82 u alpine php image)
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html \
    && chmod -R 644 /var/www/html/public

FROM php:8.3.7-fpm-alpine3.19@sha256:abc123def456...

# Kopirati samo runtime dependencies
COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
COPY --from=builder /var/www/html /var/www/html

# Security headers u PHP-FPM konfiguraciji
RUN echo "expose_php = Off" >> /usr/local/etc/php/php.ini && \
    echo "display_errors = Off" >> /usr/local/etc/php/php.ini && \
    echo "log_errors = On" >> /usr/local/etc/php/php.ini && \
    echo "error_log = /proc/1/fd/2" >> /usr/local/etc/php/php.ini && \
    echo "allow_url_fopen = Off" >> /usr/local/etc/php/php.ini && \
    echo "allow_url_include = Off" >> /usr/local/etc/php/php.ini

USER www-data

EXPOSE 9000
CMD ["php-fpm"]
```

### Nginx — production Dockerfile

```dockerfile
# nginx/Dockerfile

FROM nginx:1.25.3-alpine@sha256:def789ghi012...

# Ukloniti default config koji može eksponirati verziju
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY snippets/ /etc/nginx/snippets/

# nginx user već postoji u official image, UID 101
# Kreirati direktorije za nginx non-root run
RUN mkdir -p /var/cache/nginx /var/run/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/run/nginx && \
    # nginx.pid mora biti u writable lokaciji za non-root
    sed -i 's|/var/run/nginx.pid|/var/run/nginx/nginx.pid|g' /etc/nginx/nginx.conf

# Non-root port — koristiti 8080 interno, mapirati u K8s Service
# Nginx ne može bindovati port < 1024 bez CAP_NET_BIND_SERVICE
EXPOSE 8080

USER nginx
```

---

## securityContext u Kubernetes

Ovo ide na svaki Deployment u projektu:

```yaml
# k8s/base/go-service/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-service
  namespace: project-a
spec:
  replicas: 2
  selector:
    matchLabels:
      app: go-service
  template:
    metadata:
      labels:
        app: go-service
    spec:
      # Pod-level security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault  # Kubernetes default seccomp profile — dobar baseline
        # supplementalGroups: []  # Bez extra group memberships

      serviceAccountName: go-service-sa  # Dedicated SA, ne default
      automountServiceAccountToken: false  # Ne trebamo K8s API pristup

      containers:
        - name: go-service
          image: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/project-a/go-service:sha256-abc123

          # Container-level security context
          securityContext:
            runAsNonRoot: true
            runAsUser: 10001
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
              # Ne dodavati nikakve capabilities osim ako je apsolutno neophodno
              # add: ["NET_BIND_SERVICE"]  # Samo ako treba port < 1024

          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
              # Uvijek postaviti memory limit — OOM kill je predvidljiv, memory leak nije

          volumeMounts:
            - name: tmp-dir
              mountPath: /tmp  # Go aplikacija može trebati tmp za neke operacije
            - name: secrets
              mountPath: /run/secrets
              readOnly: true

      volumes:
        - name: tmp-dir
          emptyDir:
            medium: Memory  # tmpfs umjesto disk-a za /tmp
            sizeLimit: 64Mi
        - name: secrets
          secret:
            secretName: go-service-secrets
            defaultMode: 0440  # Samo čitanje za owner i group
```

### readOnlyRootFilesystem — gdje pisati

PHP je poseban slučaj jer treba writable direktorije za session storage, OPcache, i temp fajlove:

```yaml
# k8s/base/php-service/deployment.yaml — volumes za PHP
      volumes:
        - name: php-sessions
          emptyDir:
            medium: Memory
            sizeLimit: 128Mi
        - name: php-tmp
          emptyDir:
            medium: Memory
            sizeLimit: 64Mi
        - name: opcache
          emptyDir:
            sizeLimit: 256Mi

      containers:
        - name: php-service
          securityContext:
            readOnlyRootFilesystem: true
            # ...ostalo isto
          volumeMounts:
            - name: php-sessions
              mountPath: /var/lib/php/sessions
            - name: php-tmp
              mountPath: /tmp
            - name: opcache
              mountPath: /var/cache/php/opcache
```

---

## Trivy u GitLab CI — image i IaC scanning

```yaml
# .gitlab-ci.yml

trivy-image-scan:
  stage: security
  image: aquasec/trivy:0.50.0
  variables:
    TRIVY_NO_PROGRESS: "true"
    TRIVY_CACHE_DIR: ".trivycache/"
    # Ignore unfixed vulnerabilities (nema smisla blokirati na CVE bez patcha)
    TRIVY_IGNORE_UNFIXED: "true"
  cache:
    paths:
      - .trivycache/
    key: trivy-$CI_COMMIT_REF_SLUG
  script:
    # Image scan — HIGH i CRITICAL blokiraju pipeline
    - trivy image
        --exit-code 1
        --severity HIGH,CRITICAL
        --format template
        --template "@/contrib/gitlab.tpl"
        --output gl-container-scanning-report.json
        $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA

    # IaC scan — Terraform misconfigurations
    - trivy config
        --exit-code 1
        --severity HIGH,CRITICAL
        --format template
        --template "@/contrib/gitlab.tpl"
        --output gl-sast-report.json
        terraform/

    # Secret scan u source kodu
    - trivy fs
        --scanners secret
        --exit-code 1
        .

  artifacts:
    reports:
      container_scanning: gl-container-scanning-report.json
      sast: gl-sast-report.json
    expire_in: 30 days
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_PIPELINE_SOURCE == "merge_request_event"
```

### .trivyignore — false positive management

```
# .trivyignore
# Format: CVE-ID [comment]
# OBAVEZNO: svaki entry mora imati justifikaciju i datum review-a

# CVE-2023-XXXXX - Alpine musl libc - eksploitacija zahtijeva local shell access
# Review: 2024-01-15 - Kontekst: container nema shell u production image-u (scratch)
# Remediation: Patch dostupan u Alpine 3.20, upgrade planiran Q2 2024
CVE-2023-XXXXX

# CVE-2024-YYYYY - openssl 3.x - MEDIUM severity, downgrade na INFO
# Review: 2024-03-01 - Ne utiče na naš use case (koristimo samo TLS 1.3)
# Razlog ignorisanja: Vendor procijenjio LOW u našem kontekstu
CVE-2024-YYYYY
```

**Triage policy:**
- `CRITICAL` + exploit postoji + network reachable = **blokirati build odmah**
- `CRITICAL` + exploit postoji + local only = **blokirati build, planirati hitni fix**
- `CRITICAL` + nema exploita = **warn, planirati fix u sljedećem sprintu**
- `HIGH` = warn u PR, ne blokirati (osim ako eksplicitno policy kaže drugačije)
- `MEDIUM/LOW` = log, quarterly review

### SBOM generisanje za compliance

```yaml
trivy-sbom:
  stage: security
  image: aquasec/trivy:0.50.0
  script:
    - trivy image
        --format cyclonedx
        --output sbom-go-service.json
        $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA
    - trivy image
        --format cyclonedx
        --output sbom-php-service.json
        $CI_REGISTRY_IMAGE/php-service:$CI_COMMIT_SHA
  artifacts:
    paths:
      - sbom-*.json
    expire_in: 1 year  # SBOM čuvati dugo za compliance audite
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Image pinning — digest umjesto taga

Tag `nginx:1.25.3-alpine` može se promijeniti bez upozorenja (image rebuild sa novom base). Digest je immutable:

```bash
# Dobiti digest za image koji želite pinirati
docker buildx imagetools inspect nginx:1.25.3-alpine \
    --format '{{json .Manifest.Digest}}'
# → "sha256:a17a7c5f..."

# Koristiti u Dockerfile:
FROM nginx:1.25.3-alpine@sha256:a17a7c5f...
```

> **Podman:** `podman history` / `podman inspect` — isti syntax, output format može minimalno varirati.

Automatizacija: Renovate Bot ili Dependabot mogu automatski otvarati MR-ove za ažuriranje digest-ova kada base image se ažurira:

```json
// renovate.json
{
  "extends": ["config:base"],
  "dockerfile": {
    "enabled": true,
    "pinDigests": true
  },
  "schedule": ["every week"]
}
```
