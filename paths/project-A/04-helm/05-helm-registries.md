# 05 — Helm registries

## Dva pristupa distribuciji chart-ova

**Klasični HTTP Helm repo** — stariji pristup. Chart se pakuje u `.tgz` arhivu,
generiše se `index.yaml` fajl, i servira sa HTTP servera.
Problem: zahtijeva zasebnu infrastrukturu ili GitHub Pages za hosting.

**OCI registry** — moderni pristup (Helm 3.8+, 2022). Chart se pushuje
kao OCI artifact u isti registry koji čuva i Docker image-ove.
GitLab Container Registry podržava OCI artifact od 2022.

Za project-A koristimo OCI — manje infrastrukture, jedan registry za sve.

## OCI vs HTTP repo

| | OCI Registry | HTTP Helm Repo |
|---|---|---|
| Hosting | Container registry (GitLab, GHCR) | HTTP server, S3, GitHub Pages |
| Auth | Isti kao za Docker images | Zasebna konfiguracija |
| Versioning | Immutable tags | Mutable index.yaml |
| Namespace | `oci://` prefix | `https://` URL |
| Helm podrška | Helm 3.8+ | Sve verzije |

## Push chart u GitLab Container Registry

Pakovati chart u `.tgz`:

```bash
helm package ./helloworld
# kreira: helloworld-0.1.0.tgz
```

Autentikovati se:

```bash
helm registry login registry.gitlab.com \
  --username $CI_REGISTRY_USER \
  --password $CI_REGISTRY_PASSWORD
```

Push na OCI registry:

```bash
helm push helloworld-0.1.0.tgz \
  oci://registry.gitlab.com/firma/helloworld/charts
```

Chart je sada dostupan na:
`oci://registry.gitlab.com/firma/helloworld/charts/helloworld:0.1.0`

## Pull i deploy sa OCI registry

```bash
helm upgrade --install helloworld-dev \
  oci://registry.gitlab.com/firma/helloworld/charts/helloworld \
  --version 0.1.0 \
  -f values/dev.yaml \
  --namespace helloworld-dev \
  --create-namespace
```

`--version` je obavezan za OCI charts — Helm ne može "pronaći" latest verziju
automatski kao kod HTTP repo-a. Uvijek moraš biti eksplicitan.

Pregled dostupnih verzija:

```bash
helm show chart oci://registry.gitlab.com/firma/helloworld/charts/helloworld \
  --version 0.1.0
```

## Versioning chart-a u CI/CD

U project-A, chart verzija se automatski bumpa u CI-u.
Postoje dva pristupa:

**Pristup 1: Chart verzija = Git tag aplikacije**

```yaml
# .gitlab-ci.yml
package-helm:
  script:
    - |
      # Postavi appVersion na trenutni Git tag
      sed -i "s/^appVersion:.*/appVersion: \"${CI_COMMIT_TAG}\"/" helm/helloworld/Chart.yaml
      # Bump chart patch version
      CHART_VERSION=$(grep '^version:' helm/helloworld/Chart.yaml | awk '{print $2}')
      helm package helm/helloworld --version ${CHART_VERSION}
      helm push helloworld-*.tgz oci://registry.gitlab.com/firma/helloworld/charts
```

**Pristup 2: Chart verzija = Git SHA (immutable, po build-u)**

```bash
CHART_VERSION="0.0.0-${CI_COMMIT_SHORT_SHA}"
helm package ./helm/helloworld --version ${CHART_VERSION}
helm push helloworld-*.tgz oci://registry.gitlab.com/firma/helloworld/charts
```

Ovaj pristup daje unique verziju za svaki build. Dobar za traceability ali
generiše mnogo verzija. Dodaj cleanup job koji briše stare verzije.

## Kada koristiti lokalni chart vs registry chart

**Lokalni chart** (`./helm/helloworld`) — tokom razvoja chart-a.
CI/CD pipeline koji radi iz istog repozitorijuma.

```bash
helm upgrade --install helloworld-dev ./helm/helloworld -f values/dev.yaml
```

**Registry chart** — za deployment iz zasebnog pipeline-a, ili kad više
projekata koristi isti chart.

```bash
helm upgrade --install helloworld-dev \
  oci://registry.gitlab.com/firma/helloworld/charts/helloworld \
  --version 0.1.0
```

Za project-A na početku: lokalni chart u CI pipeline-u.
Kad projekt sazri: push na registry i deploy s referencom na verziju.

## Veza sa project-A

GitLab CI deploy job struktura:

```yaml
deploy:dev:
  stage: deploy
  image: alpine/helm:3.14
  script:
    - helm registry login registry.gitlab.com
        --username $CI_REGISTRY_USER
        --password $CI_REGISTRY_PASSWORD
    - helm upgrade --install helloworld-dev ./helm/helloworld
        -f helm/helloworld/values.yaml
        -f helm/helloworld/values/dev.yaml
        --set image.tag=$CI_COMMIT_SHORT_SHA
        --namespace helloworld-dev
        --create-namespace
        --wait
        --timeout 5m
  environment:
    name: dev
    url: https://hello.dev.firma.com
```

`--wait` čeka da svi Pods postanu Ready prije nego job završi.
`--timeout 5m` — ako za 5 minuta Pods nisu Ready, job failuje.
Bez ova dva flaga, CI bi rekao "deploy uspješan" čak i ako Pods crashaju.
