# 03 — Templates i values

## Go template sintaksa

Helm koristi Go template engine. Svaki fajl u `templates/` prolazi kroz ovaj engine
i producira Kubernetes YAML manifest.

Osnovna sintaksa:

```
{{ .Values.image.tag }}        ← umetni vrijednost iz values
{{- .Values.image.tag }}       ← umetni, ukloni whitespace prije
{{ .Values.image.tag -}}       ← umetni, ukloni whitespace poslije
{{- .Values.image.tag -}}      ← umetni, ukloni whitespace sa oba kraja
```

`-` uz `{{` i `}}` je bitan za kontrolu praznina u generisanom YAML-u.
Bez njega možeš dobiti neželjene prazne redove.

## Tri glavna scope-a

`.Values` — sve iz values.yaml i override fajlova:

```yaml
{{ .Values.replicaCount }}
{{ .Values.image.repository }}
{{ .Values.image.tag }}
{{ .Values.ingress.host }}
```

`.Release` — informacije o konkretnoj instalaciji:

```yaml
{{ .Release.Name }}         # npr. "helloworld-dev"
{{ .Release.Namespace }}    # npr. "helloworld-dev"
{{ .Release.Service }}      # uvijek "Helm"
{{ .Release.IsUpgrade }}    # bool
```

`.Chart` — podaci iz Chart.yaml:

```yaml
{{ .Chart.Name }}        # "helloworld"
{{ .Chart.Version }}     # "0.3.1"
{{ .Chart.AppVersion }}  # "1.2.0"
```

## _helpers.tpl i include funkcija

Named templates iz `_helpers.tpl` se pozivaju sa `include`:

```yaml
metadata:
  name: {{ include "helloworld.fullname" . }}
  labels:
    {{- include "helloworld.labels" . | nindent 4 }}
```

`include` vraća string. `nindent 4` dodaje newline i indent od 4 razmaka.
Zašto `nindent` a ne `indent`: `nindent` dodaje newline na početku,
što je potrebno jer labele idu u novi red.

## Conditionals

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
...
{{- end }}
```

Kompleksni conditional:

```yaml
{{- if and .Values.ingress.enabled .Values.ingress.tls }}
  tls:
    - hosts:
        - {{ .Values.ingress.host }}
      secretName: {{ include "helloworld.fullname" . }}-tls
{{- end }}
```

## Loops

Za environment varijable iz values:

```yaml
# values.yaml
env:
  - name: APP_ENV
    value: production
  - name: LOG_LEVEL
    value: info
```

```yaml
# deployment.yaml template
{{- if .Values.env }}
env:
  {{- range .Values.env }}
  - name: {{ .name }}
    value: {{ .value | quote }}
  {{- end }}
{{- end }}
```

`quote` je Helm funkcija koja omota vrijednost u navodne znakove —
važno za stringove koji izgledaju kao brojevi ili booleani.

## toYaml i nindent za složene strukture

Resources blok je dobar primjer gdje `toYaml` sjaji:

```yaml
# values.yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

```yaml
# deployment.yaml template
resources:
  {{- toYaml .Values.resources | nindent 10 }}
```

`toYaml` konvertuje Go map strukturu nazad u YAML string.
`nindent 10` dodaje newline i 10 razmaka indentacije.
Bez toga bi resources blok bio jedan red bez indentacije.

## Kompletan deployment.yaml za hello-world

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "helloworld.fullname" . }}
  namespace: {{ .Release.Namespace }}
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
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          {{- if .Values.env }}
          env:
            {{- range .Values.env }}
            - name: {{ .name }}
              value: {{ .value | quote }}
            {{- end }}
          {{- end }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 3
            periodSeconds: 5
```

Svaki varijabilan dio je template izraz. Šta ostaje isto za sva okruženja:
port 80, probe paths, probe timing. Šta se mijenja: replicas, image tag,
resources, env vars.

## Veza sa project-A

Kada GitLab CI pokrene deploy stage, komanda je:

```bash
helm upgrade --install helloworld-${ENV} ./helm/helloworld \
  -f ./helm/helloworld/values.yaml \
  -f ./helm/helloworld/values/${ENV}.yaml \
  --set image.tag=${CI_COMMIT_SHORT_SHA} \
  --namespace helloworld-${ENV}
```

`--set image.tag` overriduje vrijednost iz values fajla — CI uvijek zna
tačan SHA commita koji gradi. Eksplicitniji od oslanjanja na `latest`.
