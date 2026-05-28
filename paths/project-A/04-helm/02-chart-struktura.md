# 02 — Chart struktura

## Anatomija chart direktorijuma

```
helloworld/
├── Chart.yaml            ← metadata o chart-u
├── values.yaml           ← default values (base)
├── values/
│   ├── local.yaml        ← kind cluster (lokalni dev)
│   ├── dev.yaml          ← AWS dev override
│   ├── staging.yaml      ← AWS staging override
│   └── prod.yaml         ← AWS prod override
└── templates/
    ├── _helpers.tpl      ← reusable template fragments (ne generišu YAML)
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    └── hpa.yaml
```

Helm procitaje `values.yaml` kao bazu. Kada deployas sa `-f values/prod.yaml`,
prod.yaml vrijednosti prepisuju (override) samo ono što je u njemu definirano.
Ostatak dolazi iz base `values.yaml`.

## Chart.yaml

Obavezan fajl. Metadata o chart-u.

```yaml
apiVersion: v2
name: helloworld
description: Nginx hello world app za project-A
type: application
version: 0.3.1        # verzija chart-a (Helm packaging)
appVersion: "1.2.0"   # verzija aplikacije (informativno)
```

Razlika između `version` i `appVersion`:
- `version` — verzija samog chart-a (mijenja se kad mijenjas templates ili values strukturu)
- `appVersion` — verzija aplikacije koja se deploya (image tag). Informativno polje,
  Helm ga ne koristi za logiku.

U project-A, `version` se bumpa u CI-u pri svakoj promjeni chart-a.
`appVersion` prati Git tag aplikacije.

## values.yaml — default baza

```yaml
replicaCount: 1

image:
  repository: registry.gitlab.com/firma/helloworld
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  host: ""
  tls: false

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi

hpa:
  enabled: false
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 70

env: []
```

Default vrijednosti su namjerno minimalne — najmanji resursi, bez ingress-a, bez HPA.
Svako okruženje koje treba više, eksplicitno to definiše u svom values fajlu.

## Per-environment values fajlovi

`values/dev.yaml` — samo šta se razlikuje od baze:

```yaml
ingress:
  enabled: true
  host: hello.dev.firma.com

resources:
  limits:
    cpu: 200m
    memory: 256Mi
```

`values/prod.yaml`:

```yaml
replicaCount: 3

ingress:
  enabled: true
  host: hello.firma.com
  tls: true

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

hpa:
  enabled: true
  minReplicas: 3
  maxReplicas: 10

image:
  pullPolicy: Always
```

Prod fajl je eksplicitan i oprezlijiji. Dev je minimalan.

## _helpers.tpl — reusable template fragments

Fajl čije ime počinje sa `_` Helm ne renderuje kao Kubernetes manifest.
Koristi se za definisanje named templates koji se pozivaju iz ostalih fajlova.

```
{{/*
Generise ime za sve resurse ovog chart-a.
Koristi .Release.Name da bi vise releases mogli coexistirati.
*/}}
{{- define "helloworld.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Zajednicke labele koje idu na sve resurse.
*/}}
{{- define "helloworld.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labele za Deployment i Service matching.
*/}}
{{- define "helloworld.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

Zašto je `helloworld.fullname` koji uključuje `.Release.Name` važan:
Kada deployas isti chart dva puta u isti namespace (npr. dva MR review env-a),
svaki release dobija único ime resursa. Bez toga bi resources kolidirale.

## Veza sa project-A

Chart direktorijum živi u Git repozitorijumu uz kod aplikacije:

```
project-A/
├── src/                     ← nginx config i index.html
├── Dockerfile
├── .gitlab-ci.yml
└── helm/
    └── helloworld/          ← chart
        ├── Chart.yaml
        ├── values.yaml
        ├── values/
        └── templates/
```

Sve u jednom repozitorijumu. CI/CD pipeline ima pristup i kodu i chart-u.
