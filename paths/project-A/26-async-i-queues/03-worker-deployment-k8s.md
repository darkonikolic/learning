# 03 — Worker Deployment (Kubernetes)

## K8s Deployment za email worker

Isti Docker image kao API server — razlika je samo u `command`.
`POD_NAME` se injektira kao environment varijabla da svaki pod ima jedinstven consumer name u Redis consumer groupu.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: email-worker
  namespace: project-a-prod
  labels:
    app: email-worker
    component: worker
spec:
  replicas: 2   # 2 workera paralelno — dijele queue:email stream
  selector:
    matchLabels:
      app: email-worker
  template:
    metadata:
      labels:
        app: email-worker
        component: worker
    spec:
      serviceAccountName: go-service   # IRSA za AWS SES (slanje emailova)
      terminationGracePeriodSeconds: 30
      containers:
        - name: email-worker
          image: registry.gitlab.com/user/project/go-service:v1.2.0
          command: ["/server", "worker", "email"]   # ← jedina razlika od API Deploymenta
          env:
            - name: APP_ENV
              value: production
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name   # Unique consumer name per pod (npr. email-worker-5d4b9-xkj2p)
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: url
            - name: DB_DSN
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: dsn
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - "redis-cli -u $REDIS_URL XPENDING queue:email email-workers - + 1 | wc -l"
            initialDelaySeconds: 30
            periodSeconds: 60
            failureThreshold: 3
          readinessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - "redis-cli -u $REDIS_URL PING | grep -q PONG"
            initialDelaySeconds: 5
            periodSeconds: 10
```

---

## Helm values za worker

```yaml
# helm/values/prod.yaml
emailWorker:
  enabled: true
  replicaCount: 2
  image:
    tag: "v1.2.0"
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 128Mi
```

```yaml
# helm/values/dev.yaml
emailWorker:
  enabled: true
  replicaCount: 1
  image:
    tag: "latest"
  resources:
    requests:
      cpu: 10m
      memory: 32Mi
    limits:
      cpu: 100m
      memory: 64Mi
```

---

## Helm template za worker Deployment

```yaml
# helm/templates/worker-deployment.yaml
{{- if .Values.emailWorker.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "project.fullname" . }}-email-worker
  namespace: {{ .Release.Namespace }}
spec:
  replicas: {{ .Values.emailWorker.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "project.fullname" . }}-email-worker
  template:
    metadata:
      labels:
        app: {{ include "project.fullname" . }}-email-worker
    spec:
      serviceAccountName: {{ .Values.serviceAccountName }}
      containers:
        - name: email-worker
          image: "{{ .Values.image.repository }}:{{ .Values.emailWorker.image.tag }}"
          command: ["/server", "worker", "email"]
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          {{- include "project.commonEnv" . | nindent 12 }}
          resources:
            {{- toYaml .Values.emailWorker.resources | nindent 12 }}
{{- end }}
```

---

## Ručno skaliranje

```bash
# Povećaj broj workera u gužvi (Black Friday, kampanje)
kubectl scale deployment email-worker --replicas=5 -n project-a-prod

# Provjeri status
kubectl rollout status deployment/email-worker -n project-a-prod

# Vrati na normalu
kubectl scale deployment email-worker --replicas=2 -n project-a-prod
```

---

## KEDA za auto-scaling po queue dubini (advanced)

KEDA (Kubernetes Event-Driven Autoscaling) automatski skalira broj worker podova
prema broju poruka koje čekaju u Redis Streams-u.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: email-worker-scaler
  namespace: project-a-prod
spec:
  scaleTargetRef:
    name: email-worker
  minReplicaCount: 1
  maxReplicaCount: 10
  cooldownPeriod: 60   # Čekaj 60s prije scale-down
  triggers:
    - type: redis-streams
      metadata:
        addressFromEnv: REDIS_URL
        stream: queue:email
        consumerGroup: email-workers
        lagCount: "50"           # Jedan worker per 50 pending poruka
        activationLagCount: "5"  # Ne skalira dok ima < 5 poruka
```

**Instalacija KEDA na EKS:**
```bash
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda --namespace keda --create-namespace
```

---

## Dijagnostika worker podova

```bash
# Provjeri koji workeri rade
kubectl get pods -n project-a-prod -l app=email-worker

# Logovi konkretnog workera
kubectl logs -n project-a-prod -l app=email-worker --tail=100

# Logovi u realnom vremenu
kubectl logs -f deployment/email-worker -n project-a-prod

# Provjeri Redis consumer group status
kubectl exec -it deployment/email-worker -n project-a-prod -- \
  redis-cli -u $REDIS_URL XINFO CONSUMERS queue:email email-workers
```
