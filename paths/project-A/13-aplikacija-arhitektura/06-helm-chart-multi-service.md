# 06 — Helm chart: multi-service deployment

## Struktura chart-a

```
helm/project-a/
├── Chart.yaml
├── values.yaml
├── values/
│   ├── local.yaml       # kind lokalni override
│   ├── staging.yaml
│   └── production.yaml
└── templates/
    ├── _helpers.tpl
    ├── configmap-nginx.yaml
    ├── deployment-nginx.yaml
    ├── deployment-php.yaml
    ├── deployment-go.yaml
    ├── service-nginx.yaml
    ├── service-php.yaml
    ├── service-go.yaml
    ├── ingress.yaml
    ├── hpa-go.yaml
    └── external-secrets.yaml
```

---

## Chart.yaml

```yaml
apiVersion: v2
name: project-a
description: Vue.js + PHP proxy + Go backend + MySQL + Redis
type: application
version: 0.1.0
appVersion: "1.0.0"
```

---

## values.yaml — centralni config za sve servise

```yaml
global:
  namespace: project-a
  imageRegistry: registry.example.com/project-a

nginx:
  image:
    repository: nginx-frontend
    tag: "latest"
    pullPolicy: IfNotPresent
  replicaCount: 2
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 128Mi
  service:
    type: ClusterIP
    port: 80

phpService:
  image:
    repository: php-service
    tag: "latest"
    pullPolicy: IfNotPresent
  replicaCount: 2
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi
  service:
    type: ClusterIP
    port: 9000

goService:
  image:
    repository: go-service
    tag: "latest"
    pullPolicy: IfNotPresent
  replicaCount: 3
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 300m
      memory: 128Mi
  service:
    type: ClusterIP
    port: 8080
  hpa:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    cpuTargetUtilization: 70

ingress:
  enabled: true
  className: nginx
  host: project-a.example.com
  tls:
    enabled: true
    secretName: project-a-tls

externalSecrets:
  enabled: true
  secretStoreName: aws-secrets-manager
  refreshInterval: 1h
```

---

## Deployment za Go servis (pattern koji se ponavlja)

```yaml
# templates/deployment-go.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "project-a.fullname" . }}-go
  namespace: {{ .Values.global.namespace }}
  labels:
    app.kubernetes.io/component: go-service
    {{- include "project-a.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.goService.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/component: go-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero downtime deployment
  template:
    metadata:
      labels:
        app.kubernetes.io/component: go-service
    spec:
      # Init container čeka MySQL i Redis prije nego startu Go servis
      initContainers:
        - name: wait-for-mysql
          image: busybox:1.36
          command: ['sh', '-c',
            'until nc -z mysql-master 3306; do echo "waiting for mysql"; sleep 2; done']
        - name: wait-for-redis
          image: busybox:1.36
          command: ['sh', '-c',
            'until nc -z redis 6379; do echo "waiting for redis"; sleep 2; done']

      containers:
        - name: go-service
          image: {{ .Values.global.imageRegistry }}/{{ .Values.goService.image.repository }}:{{ .Values.goService.image.tag }}
          imagePullPolicy: {{ .Values.goService.image.pullPolicy }}
          ports:
            - containerPort: 8080
              name: http
          env:
            - name: MYSQL_MASTER_DSN
              valueFrom:
                secretKeyRef:
                  name: project-a-secrets
                  key: mysql-master-dsn
            - name: MYSQL_REPLICA_DSN
              valueFrom:
                secretKeyRef:
                  name: project-a-secrets
                  key: mysql-replica-dsn
            - name: REDIS_ADDR
              value: redis.{{ .Values.global.namespace }}.svc.cluster.local:6379
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: project-a-secrets
                  key: redis-password

          # Liveness: da li je proces živ? Ako ne, K8s restartuje pod
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 15
            failureThreshold: 3

          # Readiness: da li je spreman primiti zahtjeve?
          # Provjera čeka MySQL konekciju — ne šalje saobraćaj dok DB nije dostupan
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3

          resources:
            requests:
              cpu: {{ .Values.goService.resources.requests.cpu }}
              memory: {{ .Values.goService.resources.requests.memory }}
            limits:
              cpu: {{ .Values.goService.resources.limits.cpu }}
              memory: {{ .Values.goService.resources.limits.memory }}

          # Graceful shutdown: K8s šalje SIGTERM, daj servisu 15s da završi zahtjeve
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
          # terminationGracePeriodSeconds mora biti > preStop sleep + shutdown timeout
      terminationGracePeriodSeconds: 30
```

---

## PHP Deployment sa init containerom koji čeka Go servis

```yaml
# templates/deployment-php.yaml (relevantni dio)
spec:
  template:
    spec:
      initContainers:
        # PHP proxy treba Go servis da bude zdravo dostupan
        - name: wait-for-go-service
          image: curlimages/curl:8.5.0
          command:
            - sh
            - -c
            - |
              until curl -sf http://go-service.{{ .Values.global.namespace }}.svc.cluster.local:8080/health; do
                echo "waiting for go-service healthcheck..."
                sleep 3
              done
              echo "go-service is healthy"
```

---

## Ingress — routing po putanji

```yaml
# templates/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "project-a.fullname" . }}
  namespace: {{ .Values.global.namespace }}
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    # HTTPS redirect
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: {{ .Values.ingress.className }}
  tls:
    - hosts:
        - {{ .Values.ingress.host }}
      secretName: {{ .Values.ingress.tls.secretName }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          # /api/ → nginx container (koji proksira na php-service FastCGI)
          # Sve ostalo → nginx container (koji servira Vue.js statiku + SPA fallback)
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "project-a.fullname" . }}-nginx
                port:
                  number: 80
```

Napomena: oba patha idu na nginx servis jer nginx interno rutira `/api/` na PHP-FPM i servira Vue.js statiku direktno. Nije potreban zasebni Ingress rule za API — nginx.conf konfiguracija to rješava.

---

## External Secrets Operator — ne hardkodirati tajne

```yaml
# templates/external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: project-a-secrets
  namespace: {{ .Values.global.namespace }}
spec:
  refreshInterval: {{ .Values.externalSecrets.refreshInterval }}
  secretStoreRef:
    name: {{ .Values.externalSecrets.secretStoreName }}
    kind: ClusterSecretStore
  target:
    name: project-a-secrets  # Ime K8s Secret-a koji se kreira
    creationPolicy: Owner
  data:
    - secretKey: mysql-master-dsn
      remoteRef:
        key: project-a/production  # AWS Secrets Manager path
        property: mysql_master_dsn
    - secretKey: mysql-replica-dsn
      remoteRef:
        key: project-a/production
        property: mysql_replica_dsn
    - secretKey: redis-password
      remoteRef:
        key: project-a/production
        property: redis_password
    - secretKey: php-session-secret
      remoteRef:
        key: project-a/production
        property: php_session_secret
```

Alternativa za timove bez External Secrets Operator-a: `helm secrets` plugin sa SOPS enkriptovanim values fajlom. Nikad ne koristiti plain text credentials u `values.yaml` koji idu u git.

---

## ConfigMap za nginx.conf

```yaml
# templates/configmap-nginx.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: {{ .Values.global.namespace }}
data:
  nginx.conf: |
    # Puna nginx.conf konfiguracija (ista kao u Dockerfileu)
    # Mountovana u nginx pod na /etc/nginx/nginx.conf
    upstream php_fpm {
      server php-service.{{ .Values.global.namespace }}.svc.cluster.local:9000;
      keepalive 16;
    }
    ...
```

```yaml
# U deployment-nginx.yaml
volumes:
  - name: nginx-config
    configMap:
      name: nginx-config
containers:
  - name: nginx
    volumeMounts:
      - name: nginx-config
        mountPath: /etc/nginx/nginx.conf
        subPath: nginx.conf
```

ConfigMap montiran kao fajl omogućava promjenu nginx konfiguracije bez rebuild image-a. Dovoljno je update ConfigMap-a i nginx pod restart.

---

## HPA za Go servis

```yaml
# templates/hpa-go.yaml
{{- if .Values.goService.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "project-a.fullname" . }}-go
  namespace: {{ .Values.global.namespace }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "project-a.fullname" . }}-go
  minReplicas: {{ .Values.goService.hpa.minReplicas }}
  maxReplicas: {{ .Values.goService.hpa.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.goService.hpa.cpuTargetUtilization }}
{{- end }}
```

HPA za PHP servis je manje korisno jer PHP-FPM ima fiksni `pm.max_children` limit. Skaliranje PHP-a znači dodavanje novih pod-ova, ali svaki ima isti pool limit. HPA za Go je direktniji — Go goroutines automatski koriste više CPU-a.

---

## Deploy komande

```bash
# Instaliraj chart na kind klaster
helm upgrade --install project-a ./helm/project-a \
  -f helm/project-a/values/local.yaml \
  --namespace project-a \
  --create-namespace

# Provjeri status
helm status project-a -n project-a

# Rollback na prethodnu verziju
helm rollback project-a 1 -n project-a

# Debug: provjeri generirane template-ove bez deployanja
helm template project-a ./helm/project-a -f values/local.yaml
```
