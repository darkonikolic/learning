# 04 — Environments i values override

## values.yaml kao default baza

`values.yaml` definiše najkonzervativnije, najjeftinije default vrijednosti.
Filozofija: default je "najmanji koji radi". Sve što zahtijeva više resursa
mora biti eksplicitno zahtjevano u env-specifičnom fajlu.

Ovo sprječava situaciju gdje dev okruženje greškom nasljeđuje prod resource limite.

```yaml
# values.yaml — baza, minimalna
replicaCount: 1

image:
  repository: registry.gitlab.com/firma/helloworld
  tag: latest
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi

ingress:
  enabled: false
  host: ""
  tls: false

hpa:
  enabled: false
```

## Per-environment override

Helm merge-uje values fajlove po redu kojim su navedeni.
Kasniji fajl prepisuje samo ono što definiše, ostatak ostaje iz ranijeg.

```bash
helm upgrade --install helloworld-prod ./helloworld \
  -f values.yaml \       ← baza
  -f values/prod.yaml    ← override
```

## Šta se razlikuje po okruženju

### replicaCount

```yaml
# values/dev.yaml
replicaCount: 1     # jedan pod je dovoljno za testiranje

# values/staging.yaml
replicaCount: 2     # testira HA ali bez cijene prod-a

# values/prod.yaml
replicaCount: 3     # minimum za zero-downtime rolling update
```

### resources

Dev ne treba production-grade resurse. Prod mora garantovati performance.

```yaml
# values/dev.yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 200m
    memory: 256Mi

# values/prod.yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### ingress.host

```yaml
# values/dev.yaml
ingress:
  enabled: true
  host: hello.dev.firma.com
  tls: false          # self-signed ili bez TLS na dev

# values/staging.yaml
ingress:
  enabled: true
  host: hello.staging.firma.com
  tls: true

# values/prod.yaml
ingress:
  enabled: true
  host: hello.firma.com
  tls: true
```

### image.tag

```yaml
# values/dev.yaml
image:
  tag: latest          # uvijek najnoviji build (CI pushuje latest na dev)
  pullPolicy: Always   # uvijek povuci, jer tag se ne mijenja ali image jest

# values/prod.yaml
image:
  tag: v1.4.2          # pinovan — znaš tačno šta je u produkciji
  pullPolicy: IfNotPresent
```

Produkciaj nikad ne koristi `latest`. `latest` tag ne garantuje reproduktivnost.
Ako cluster treba da pokrene novi pod (node failure, scaling), `latest` u tom trenutku
može biti potpuno drugačiji image nego što je bio pri originalnom deploymentu.

### HPA — samo staging i prod

```yaml
# values/staging.yaml
hpa:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70

# values/prod.yaml
hpa:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
```

Dev nema HPA — nepotrebna složenost za development workflow.

## Dynamic environments — review apps

Za svaki GitLab MR, CI kreira privremeno okruženje. Values se generišu dynamički
iz MR metapodataka.

```bash
# U GitLab CI, review job
REVIEW_HOST="hello-mr-${CI_MERGE_REQUEST_IID}.review.firma.com"

helm upgrade --install helloworld-mr-${CI_MERGE_REQUEST_IID} ./helloworld \
  -f values.yaml \
  --set image.tag=${CI_COMMIT_SHORT_SHA} \
  --set ingress.enabled=true \
  --set ingress.host=${REVIEW_HOST} \
  --set replicaCount=1 \
  --namespace helloworld-mr-${CI_MERGE_REQUEST_IID} \
  --create-namespace
```

`--set` na komandnoj liniji ima najveći prioritet — prepisuje sve values fajlove.
Koristi se za dinamički generisane vrijednosti (SHA, MR broj) koje ne možeš
unaprijed staviti u statički values fajl.

## Lokalni dev — values/local.yaml

Kind cluster nema LoadBalancer ni cloud-specific ingress kontroler.
Lokalne values rješavaju ovu razliku.

```yaml
# values/local.yaml
ingress:
  enabled: true
  host: hello.local
  annotations:
    kubernetes.io/ingress.class: nginx   # kind koristi nginx ingress
  tls: false

image:
  pullPolicy: Never    # koristi lokalno buildovan image, ne pull iz registry-ja
```

`pullPolicy: Never` je ključan detalj za lokalni dev sa kind-om.
Kind nema direktan pristup GitLab registry-ju bez konfiguracije.
Lokalno buildovan image se učitava u kind sa `kind load docker-image`.

## Veza sa project-A

Kompletna matrica okruženja u projektu:

| Release name | Values fajlovi | Namespace | Trigger |
|---|---|---|---|
| helloworld-local | values.yaml + local.yaml | helloworld-local | ručno |
| helloworld-dev | values.yaml + dev.yaml | helloworld-dev | merge na main |
| helloworld-staging | values.yaml + staging.yaml | helloworld-staging | tag v*.*.* |
| helloworld-prod | values.yaml + prod.yaml | helloworld-prod | manual approve |
| helloworld-mr-N | values.yaml + --set | helloworld-mr-N | otvaranje MR |
