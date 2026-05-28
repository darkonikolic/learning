# 06 - LAB: Build i Push Image

## Cilj

Na kraju ovog lab-a imat ćete funkcionalan GitLab CI pipeline koji:
1. Gradi Docker image za nginx hello-world aplikaciju
2. Pokreće test (provjerava da nginx odgovara)
3. Push-uje image u GitLab Container Registry

## Preduslovi

- GitLab nalog (gitlab.com ili self-hosted)
- Kreirani projekat na GitLab-u (npr. `project-a`)
- Lokalno: git, Docker (za testiranje)

## Struktura projekta

```
project-a/
├── .gitlab-ci.yml
├── Dockerfile
├── nginx/
│   └── nginx.conf
└── html/
    └── index.html
```

## Korak 1: Kreirati aplikacijske fajlove

**html/index.html:**
```html
<!DOCTYPE html>
<html>
<head><title>Project A</title></head>
<body>
  <h1>Hello World</h1>
  <p>Build: CI_COMMIT_SHORT_SHA</p>
</body>
</html>
```

**nginx/nginx.conf:**
```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /health {
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
```

**Dockerfile:**
```dockerfile
FROM nginx:1.25-alpine

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY html/index.html /usr/share/nginx/html/index.html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1
```

## Korak 2: Kreirati .gitlab-ci.yml

```yaml
stages:
  - build
  - test
  - push

variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  IMAGE_BRANCH: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
  DOCKER_TLS_CERTDIR: "/certs"

default:
  image: docker:24
  services:
    - name: docker:24-dind
      alias: docker
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

build:
  stage: build
  script:
    - docker pull $IMAGE_BRANCH || true
    - |
      docker build \
        --cache-from $IMAGE_BRANCH \
        --tag $IMAGE_TAG \
        --tag $IMAGE_BRANCH \
        .
    - docker save $IMAGE_TAG | gzip > image.tar.gz
  artifacts:
    paths:
      - image.tar.gz
    expire_in: 1 hour
  rules:
    - if: $CI_COMMIT_BRANCH

test:
  stage: test
  needs:
    - build
  script:
    - docker load < image.tar.gz
    - docker run --rm -d --name hello-world-test -p 8080:80 $IMAGE_TAG
    - sleep 3
    - |
      RESPONSE=$(curl -sf http://localhost:8080/health)
      if [ "$RESPONSE" = "ok" ]; then
        echo "Health check passed"
      else
        echo "Health check failed: $RESPONSE"
        docker logs hello-world-test
        exit 1
      fi
    - curl -sf http://localhost:8080 | grep -q "Hello World" || (echo "HTML check failed" && exit 1)
    - echo "All tests passed"
    - docker stop hello-world-test
  rules:
    - if: $CI_COMMIT_BRANCH

push:
  stage: push
  needs:
    - test
  script:
    - docker load < image.tar.gz
    - docker push $IMAGE_TAG
    - docker push $IMAGE_BRANCH
    - |
      if [ "$CI_COMMIT_BRANCH" = "main" ]; then
        docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE:latest
        docker push $CI_REGISTRY_IMAGE:latest
        echo "Pushed as latest"
      fi
    - echo "IMAGE=$IMAGE_TAG" >> push.env
  artifacts:
    reports:
      dotenv: push.env
    expire_in: 1 week
  rules:
    - if: $CI_COMMIT_BRANCH
```

> **Podman u GitLab CI:**
> Docker-in-Docker (`docker:dind`) nije potreban s Podmanom. Koristi Podman socket pristup:
> ```yaml
> build:
>   image: quay.io/podman/stable
>   variables:
>     STORAGE_DRIVER: vfs
>   before_script:
>     - podman info
>   script:
>     - podman build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
>     - podman push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
> ```
> Prednost: ne treba `privileged: true` runner — Podman radi rootless.

## Korak 3: Push i provjera

```bash
git add .
git commit -m "Add CI pipeline with build, test, push"
git push origin main
```

Otvorite GitLab → vaš projekt → Build → Pipelines.

## Gdje vidite rezultate u GitLab UI

**Pipeline lista** (Build → Pipelines):
- Svaki red je jedan pipeline run
- Zelena kvačica = sve prošlo, crveni X = nešto failovalo
- Kliknite na SHA da vidite detalje

**Pipeline detalji**:
- Grafički prikaz stages i jobova
- Kliknite na job da vidite log

**Job log**:
- Sve što pipeline ispiše (stdout/stderr)
- Expandovati collapsed sekcije s plavim trouglovima
- Scroll do dna za rezultat (exit code)

**Container Registry** (Deploy → Container Registry):
- Lista imagesa s tagovima
- Svaki tag s datumom push-a i veličinom
- Možete ručno obrisati stare tagove

## Troubleshooting

**"Runner not found" ili "No runners available"**

Provjera: Settings → CI/CD → Runners. Ako nema shared runners, omogućite ih ili registrujte vlastiti runner.

Za gitlab.com: shared runners su uključeni po defaultu. Provjera: Project Settings → CI/CD → Runners → Shared runners for this project = enabled.

**"Permission denied" na Docker socket**

```
cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

Uzrok: Job pokušava koristiti socket binding ali runner nije konfigurisan za to. Rješenje: dodajte `services: [docker:24-dind]` i `DOCKER_TLS_CERTDIR: "/certs"`. Ne pokušavajte socket binding na shared runnerima.

**"denied: access forbidden" pri push-u**

```
denied: access forbidden
```

Uzrok: `CI_REGISTRY_USER` i `CI_REGISTRY_PASSWORD` nisu ispravni. Provjera: da li ste zaista koristili predefinisane varijable (ne hardcoded vrijednosti)?

Vrijedi i kada projekt ima Container Registry onemogućen: Settings → General → Visibility → Container Registry = enabled.

**Pipeline prolazi ali image nije u registry-ju**

Provjera: da li push stage ima `needs: [test]`? Bez `needs`, push može početi i završiti prije test stage-a u nekim race condition scenarijima. Eksplicitni `needs` garantuje redosled.

## AI workflow za troubleshooting

Kada pipeline fail-uje, kopirajte kompletan log (od početka do fail-a) i dajte Claude-u:

```
Moj GitLab CI pipeline fail-uje. Evo loga:

[paste cijeli log]

Šta je uzrok i kako popraviti?
```

Ili za learning:

```
Evo mog .gitlab-ci.yml. Radi, ali čini mi se neefikasno.
Gdje bi napravio izmjene za bolje performanse i sigurnost?

[paste .gitlab-ci.yml]
```

Claude razumije GitLab CI YAML sintaksu i može objasniti svaki aspekt u kontekstu vašeg projekta.
