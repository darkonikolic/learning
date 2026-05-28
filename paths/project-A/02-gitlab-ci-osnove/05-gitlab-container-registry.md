# 05 - GitLab Container Registry

## Šta je i zašto je ugrađen

GitLab Container Registry je Docker registry koji dolazi besplatno sa svakim GitLab projektom. Na `registry.gitlab.com/namespace/project` možete čuvati Docker imagee bez podešavanja eksternog servisa.

Zašto je to vrijedno:

- **Nema eksternog dependency-ja** — ne trebate DockerHub nalog, AWS ECR konfiguraciju, ili zasebni Harbor server za početak
- **Automatska autentikacija u CI** — GitLab injektuje credentials direktno u pipeline jobove
- **Iste permisije kao i repozitorij** — ko ima pristup projektu, ima pristup i registry-ju
- **Besplatan za privatne projekte** (do određene kvote na GitLab.com)

Za project-A: svi imagesi idu na `registry.gitlab.com/vas-namespace/project-a`. Nema konfiguracije.

## Predefinisane CI/CD varijable

GitLab automatski ubacu ove varijable u svaki pipeline job:

```bash
CI_REGISTRY=registry.gitlab.com
CI_REGISTRY_IMAGE=registry.gitlab.com/vas-namespace/project-a
CI_REGISTRY_USER=gitlab-ci-token
CI_REGISTRY_PASSWORD=<automatski token važeći za taj pipeline>
```

Koristite ih direktno u pipeline-u — nikad ne hardcode-ujte registry URL ili credentials:

```yaml
before_script:
  - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
```

`CI_REGISTRY_PASSWORD` je kratkovječan token specifičan za svaki pipeline run. Ovo znači da ako neko ukrade log iz jednog pipeline-a, token je već istekao.

## Strategija tagovanja

Tag je human-readable oznaka za image. Dobra strategija tagovanja pravi razliku između debugging-a u 3 ujutro i mirnog spavanja.

**Commit SHA** — uvijek jedinstven, direktno mapira na git commit:
```
registry.gitlab.com/firma/project-a:a3f9c21
```

**Branch name** — posljednji build s tog brancha:
```
registry.gitlab.com/firma/project-a:main
registry.gitlab.com/firma/project-a:feature-novi-header
```

**latest** — konvencija za "najnoviji stable build". Opasno ako se ne pazi — ne znate koji commit je u `latest` bez inspekcije.

**Semantic versioning** — za release deploymente:
```
registry.gitlab.com/firma/project-a:1.2.3
registry.gitlab.com/firma/project-a:1.2
registry.gitlab.com/firma/project-a:1
```

Preporuka za project-A pipeline:

```yaml
variables:
  IMAGE_SHA: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  IMAGE_BRANCH: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
  IMAGE_LATEST: $CI_REGISTRY_IMAGE:latest

script:
  - docker build -t $IMAGE_SHA -t $IMAGE_BRANCH .
  - docker push $IMAGE_SHA
  - docker push $IMAGE_BRANCH
  # latest samo s main brancha
  - |
    if [ "$CI_COMMIT_BRANCH" = "main" ]; then
      docker tag $IMAGE_SHA $IMAGE_LATEST
      docker push $IMAGE_LATEST
    fi
```

Kubernetes deploymenti uvijek koriste SHA tag (`a3f9c21`) — nikad `latest` ili branch ime. Razlog: SHA je immutable (uvijek isti image), dok `latest` može biti drugačiji image sjutra.

## Image cleanup policies

Bez cleanup-a, registry se puni. Svaki push kreira novi image. Za aktivan projekat s 10 pusheva dnevno na 5 brancha — to je 50 imagesa dnevno.

GitLab ima ugrađen cleanup policy: Settings → Packages and registries → Container Registry.

Tipična konfiguracija:
- Obriši tagove koji matchaju `feature-*` starije od 14 dana
- Obriši tagove koji matchaju `mr-*` starije od 7 dana
- Zadrži uvijek: `main`, `latest`, `v*` (semantic version tagovi)
- Zadrži posljednjih N tagova po imenu

Za project-A: feature branch imagesi se brišu nakon 14 dana, MR imagesi nakon mergea. `main` i verzionisani imagesi ostaju trajno.

Možete i ručno pokrenuti cleanup: Project → Packages & Registries → Container Registry → "Clean up tags".

## Lokalno povlačenje imagea

Da povučete image s GitLab registry-ja lokalno:

```bash
# Prijavite se (jednom)
docker login registry.gitlab.com

# Povucite image
docker pull registry.gitlab.com/vas-namespace/project-a:main

# Pokrenite lokalno
docker run --rm -p 8080:80 registry.gitlab.com/vas-namespace/project-a:main
```

> **Podman:** `podman login registry.gitlab.com`
> **Podman:** `podman pull registry.gitlab.com/vas-namespace/project-a:main`
> **Podman:** `podman run --rm -p 8080:80 registry.gitlab.com/vas-namespace/project-a:main`

Za personal access token (za lokalni rad, ne pipeline):
```bash
docker login registry.gitlab.com -u vas-gitlab-username -p glpat-xxxxxxxxxxxx
```

> **Podman:** `podman login registry.gitlab.com -u vas-gitlab-username -p glpat-xxxxxxxxxxxx`

Generišite PAT u GitLab: Profile → Access Tokens → read_registry scope.

## Veza sa project-A

Svaki merge na `main` branch aktivira pipeline koji:

1. Gradi novi image s nginx + `index.html`
2. Taguje ga s commit SHA i `main`
3. Push-uje u `registry.gitlab.com/firma/project-a`

Kubernetes deployment na staging-u koristi taj SHA tag da bi uvijek imao reproducibilan deployment — znate tačno koji HTML je u produkciji i možete reproduce-ovati bilo koji prethodni deployment.

Monitoring (Prometheus + Grafana) u kasnijim modulima — njihovi imagesi idu na isti registry ali u poseban direktorij: `registry.gitlab.com/firma/project-a/monitoring/prometheus:...`.
