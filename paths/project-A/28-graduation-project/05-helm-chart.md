# Helm Chart

## Struktura chart-a

```
helm/helloworld/
├── Chart.yaml
├── values.yaml          # defaults
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
└── values/
    ├── local.yaml
    ├── dev.yaml
    ├── staging.yaml
    └── prod.yaml
```

## Chart.yaml

```yaml
apiVersion: v2
name: helloworld
description: Hello World nginx aplikacija — project-A
type: application
version: 0.1.0
appVersion: "1.0.0"
```

`version` je verzija chart-a, `appVersion` je verzija aplikacije. Mijenjaj
`version` kad mijenjaš chart, `appVersion` kada puštaš novu verziju app-a.

## _helpers.tpl

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "helloworld.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "helloworld.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "helloworld.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "helloworld.selectorLabels" -}}
app.kubernetes.io/name: {{ include "helloworld.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

## templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "helloworld.name" . }}
  labels:
    {{- include "helloworld.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "helloworld.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "helloworld.selectorLabels" . | nindent 8 }}
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 101       # nginx user
        runAsGroup: 101
        fsGroup: 101
      containers:
        - name: nginx
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 80
              name: http
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: nginx-cache
              mountPath: /var/cache/nginx
            - name: nginx-run
              mountPath: /var/run
          livenessProbe:
            httpGet:
              path: /healthz
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
      volumes:
        - name: tmp
          emptyDir: {}
        - name: nginx-cache
          emptyDir: {}
        - name: nginx-run
          emptyDir: {}
```

`readOnlyRootFilesystem: true` + emptyDir volumeovi: nginx treba da piše u
`/tmp`, `/var/cache/nginx` i `/var/run`. Montujemo emptyDir (in-memory) na
ove putanje. Ostatak filesystema je read-only — exploit koji dobiše shell
ne može modifikovati binarne fajlove.

## templates/service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "helloworld.name" . }}
  labels:
    {{- include "helloworld.labels" . | nindent 4 }}
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "helloworld.selectorLabels" . | nindent 4 }}
```

## templates/ingress.yaml

```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "helloworld.name" . }}
  labels:
    {{- include "helloworld.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.tls }}
  tls:
    - hosts:
        - {{ .Values.ingress.host }}
      {{- if .Values.ingress.tlsSecretName }}
      secretName: {{ .Values.ingress.tlsSecretName }}
      {{- end }}
  {{- end }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "helloworld.name" . }}
                port:
                  name: http
{{- end }}
```

## templates/hpa.yaml

```yaml
{{- if .Values.hpa.enabled -}}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "helloworld.name" . }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "helloworld.name" . }}
  minReplicas: {{ .Values.hpa.minReplicas }}
  maxReplicas: {{ .Values.hpa.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.hpa.targetCPUUtilizationPercentage }}
{{- end }}
```

## values.yaml (defaults)

```yaml
replicaCount: 1

image:
  repository: registry.gitlab.com/tvoj-user/project-a
  tag: latest
  pullPolicy: Always

ingress:
  enabled: true
  host: app.local
  tls: false
  tlsSecretName: ""
  annotations: {}

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 200m
    memory: 128Mi

hpa:
  enabled: false
  minReplicas: 1
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70
```

## values/local.yaml

```yaml
image:
  pullPolicy: Never   # Koristi lokalni image, ne pull-aj

ingress:
  host: app.local
  annotations:
    kubernetes.io/ingress.class: nginx
```

## values/prod.yaml

```yaml
replicaCount: 3

image:
  pullPolicy: IfNotPresent

ingress:
  host: app.firma.com
  tls: true
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: "{{ .Values.acmCertArn }}"
    alb.ingress.kubernetes.io/ssl-redirect: "443"

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi

hpa:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Helm lint i test

```bash
# Provjeri sintaksu
helm lint ./helm/helloworld
helm lint ./helm/helloworld -f helm/helloworld/values/prod.yaml

# Provjeri generisan YAML
helm template helloworld ./helm/helloworld \
  -f helm/helloworld/values/local.yaml | \
  kubectl apply --dry-run=client -f -

# Provjeri sa kubesec
helm template helloworld ./helm/helloworld | \
  docker run --rm -i kubesec/kubesec:latest scan /dev/stdin
```

## AI prompt za security review

```
Evo Helm chart Deployment template-a:
[prijepi deployment.yaml]

Pregledaj sa sigurnosnog aspekta. Posebno:
1. Securitycontext — je li ispravno konfigurisan?
2. ReadOnlyRootFilesystem — šta nedostaje da ovo radi sa nginx?
3. Resource limits — jesu li razumni za statički nginx?
4. Da li capabilities drop ALL može uzrokovati probleme?
```
