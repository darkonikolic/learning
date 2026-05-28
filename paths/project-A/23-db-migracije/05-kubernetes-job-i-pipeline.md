# 05 — Kubernetes Job i GitLab CI Pipeline

## Princip: Migrate Job PRIJE app deploymenta

```
CI/CD redoslijed:
  build:migration-image  →  migrate:env  →  deploy:env
                                 ↑
                    K8s Job čeka da baza bude spremna,
                    primijeni migracije, izađe s kodom 0 ili 1.
                    deploy počinje SAMO ako je Job uspješan.
```

---

## K8s Job manifest (Helm template)

```yaml
# helm/project-a/templates/db-migrate-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate-{{ .Values.image.tag | trunc 20 | trimSuffix "-" }}
  namespace: {{ .Release.Namespace }}
  labels:
    app: {{ .Release.Name }}
    component: db-migrate
  annotations:
    "helm.sh/hook": pre-upgrade,pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  backoffLimit: 3                  # Pokušaj do 3 puta
  activeDeadlineSeconds: 300       # Timeout: 5 minuta ukupno
  ttlSecondsAfterFinished: 3600    # Auto-briši Job 1h nakon završetka
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
        component: db-migrate
    spec:
      restartPolicy: Never         # Ne restartuj Pod — Job retry kreira novi Pod
      serviceAccountName: {{ .Values.serviceAccount.name }}
      initContainers:
        - name: wait-for-mysql
          image: mysql:8.0
          command:
            - sh
            - -c
            - |
              set -e
              MAX_ATTEMPTS=30
              ATTEMPT=0
              until mysqladmin ping \
                  -h "$DB_HOST" \
                  -u healthcheck \
                  --password="$HEALTH_PASS" \
                  --silent \
                  --connect-timeout=3; do
                ATTEMPT=$((ATTEMPT + 1))
                if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
                  echo "ERROR: MySQL not ready after ${MAX_ATTEMPTS} attempts"
                  exit 1
                fi
                echo "Waiting for MySQL... attempt $ATTEMPT/$MAX_ATTEMPTS"
                sleep 3
              done
              echo "MySQL is ready."
          env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: host
            - name: HEALTH_PASS
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: healthcheck-password
      containers:
        - name: migrate
          image: {{ .Values.migrationImage.repository }}:{{ .Values.image.tag }}
          args:
            - -path=/migrations
            - -database
            - "mysql://$(DB_USER):$(DB_PASSWORD)@tcp($(DB_HOST):$(DB_PORT))/$(DB_NAME)?multiStatements=true"
            - up
          env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: host
            - name: DB_PORT
              value: "3306"
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            - name: DB_NAME
              value: {{ .Values.database.name }}
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          volumeMounts:
            - name: migrations
              mountPath: /migrations
              readOnly: true
      volumes:
        - name: migrations
          configMap:
            name: db-migrations-{{ .Values.image.tag | trunc 20 | trimSuffix "-" }}
```

---

## ConfigMap za migration fajlove (Helm)

```yaml
# helm/project-a/templates/migrations-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: db-migrations-{{ .Values.image.tag | trunc 20 | trimSuffix "-" }}
  namespace: {{ .Release.Namespace }}
  annotations:
    "helm.sh/hook": pre-upgrade,pre-install
    "helm.sh/hook-weight": "-10"   # Kreira se PRIJE Job-a
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
data:
{{ range $path, $content := .Files.Glob "../../migrations/*.sql" }}
  {{ base $path }}: |
{{ $content | indent 4 }}
{{ end }}
```

---

## Alternativa: Migration image iz Go service-a

Umjesto ConfigMap-a, migration SQL fajlovi su upakovani direktno u Docker image:

```dockerfile
# services/go-service/Dockerfile

# --- Builder: instalira migrate binary ---
FROM golang:1.22-alpine AS migration-builder
RUN apk add --no-cache git
RUN go install -tags 'mysql' \
    github.com/golang-migrate/migrate/v4/cmd/migrate@v4.17.0

# --- Migration image: mali, samo binary + SQL ---
FROM alpine:3.19 AS migration
RUN apk add --no-cache ca-certificates
COPY --from=migration-builder /go/bin/migrate /usr/local/bin/migrate
COPY migrations/ /migrations/
ENTRYPOINT ["/usr/local/bin/migrate", "-path", "/migrations", "-database"]
# Koristi se: docker run ... "mysql://..." up

# --- App image (standardni, ne sadrži migracije) ---
FROM golang:1.22-alpine AS app-builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server ./cmd/server

FROM alpine:3.19 AS app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=app-builder /app/server /server
ENTRYPOINT ["/server"]
```

```bash
# Build i push oba image-a
APP_IMAGE="$CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA"
MIGRATE_IMAGE="$CI_REGISTRY_IMAGE/go-service-migrate:$CI_COMMIT_SHA"

docker build --target migration -t "$MIGRATE_IMAGE" ./services/go-service
docker build --target app       -t "$APP_IMAGE"     ./services/go-service
docker push "$MIGRATE_IMAGE"
docker push "$APP_IMAGE"
```

---

## GitLab CI pipeline s migracijama

```yaml
# .gitlab-ci.yml

stages:
  - build
  - test
  - tf-plan
  - tf-apply
  - migrate
  - deploy
  - verify

# --- BUILD ---
build:go-service:
  stage: build
  image: docker:24
  services: [docker:24-dind]
  script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    # App image
    - docker build --target app
        -t "$CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA"
        ./services/go-service
    - docker push "$CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA"
    # Migration image
    - docker build --target migration
        -t "$CI_REGISTRY_IMAGE/go-service-migrate:$CI_COMMIT_SHA"
        ./services/go-service
    - docker push "$CI_REGISTRY_IMAGE/go-service-migrate:$CI_COMMIT_SHA"
  only:
    changes:
      - services/go-service/**/*

# --- MIGRATE ---
.migrate-template: &migrate-template
  stage: migrate
  image:
    name: $CI_REGISTRY_IMAGE/go-service-migrate:$CI_COMMIT_SHA
    entrypoint: [""]
  script:
    - >
      /usr/local/bin/migrate
      -path /migrations
      -database "mysql://${DB_USER}:${DB_PASS}@tcp(${DB_HOST}:3306)/${DB_NAME}"
      up
  after_script:
    - >
      /usr/local/bin/migrate
      -path /migrations
      -database "mysql://${DB_USER}:${DB_PASS}@tcp(${DB_HOST}:3306)/${DB_NAME}"
      version

migrate:dev:
  <<: *migrate-template
  needs: [tf-apply:dev, build:go-service]
  variables:
    DB_HOST:   $DEV_DB_HOST
    DB_USER:   $DEV_DB_USER
    DB_PASS:   $DEV_DB_PASS
    DB_NAME:   project_a_dev
  environment:
    name: development
  only: [develop]

migrate:staging:
  <<: *migrate-template
  needs: [tf-apply:staging, build:go-service]
  variables:
    DB_HOST:   $STAGING_DB_HOST
    DB_USER:   $STAGING_DB_USER
    DB_PASS:   $STAGING_DB_PASS
    DB_NAME:   project_a_staging
  environment:
    name: staging
  only: [main]

migrate:prod:
  <<: *migrate-template
  needs: [tf-apply:prod, build:go-service, migrate:staging]
  variables:
    DB_HOST:   $PROD_DB_HOST
    DB_USER:   $PROD_DB_USER
    DB_PASS:   $PROD_DB_PASS
    DB_NAME:   project_a_prod
  environment:
    name: production
  when: manual            # Prod migracija: ručni trigger
  only: [main]

# --- DEPLOY (čeka na migrate) ---
deploy:dev:
  stage: deploy
  needs: [migrate:dev]    # Deploy SAMO ako je migracija prošla
  image: alpine/helm:3.14
  script:
    - helm upgrade --install project-a ./helm/project-a
        --namespace project-a-dev
        --set image.tag="$CI_COMMIT_SHA"
        --set migrationImage.repository="$CI_REGISTRY_IMAGE/go-service-migrate"
        --wait --timeout=5m
  environment:
    name: development
  only: [develop]

deploy:prod:
  stage: deploy
  needs: [migrate:prod]
  image: alpine/helm:3.14
  script:
    - helm upgrade --install project-a ./helm/project-a
        --namespace project-a-prod
        --set image.tag="$CI_COMMIT_SHA"
        --set migrationImage.repository="$CI_REGISTRY_IMAGE/go-service-migrate"
        --wait --timeout=10m
  environment:
    name: production
  when: manual
  only: [main]
```

---

## Provjera statusa Job-a na Kubernetesu

```bash
# Lista svih migration Job-ova
kubectl get jobs -n project-a-dev -l component=db-migrate

# Provjeri log zadnjeg
kubectl logs -n project-a-dev \
  -l component=db-migrate \
  -c migrate \
  --tail=50

# Provjeri status (0=Sukces, 1=Fail)
kubectl get job db-migrate-abc123 \
  -n project-a-dev \
  -o jsonpath='{.status.conditions[*].type}'
# Output: Complete  ili  Failed

# Ako Job padne: pogledaj detaljno
kubectl describe job db-migrate-abc123 -n project-a-dev
kubectl describe pod -n project-a-dev -l job-name=db-migrate-abc123
```

---

## Helm values za migration Job

```yaml
# helm/project-a/values.yaml
image:
  tag: "latest"

migrationImage:
  repository: registry.gitlab.example.com/project-a/go-service-migrate

database:
  name: project_a

serviceAccount:
  name: go-service
```
