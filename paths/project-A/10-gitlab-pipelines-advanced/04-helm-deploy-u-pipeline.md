# 04 — Helm deploy u pipeline-u

## Teorija

Helm deploy u CI/CD znači: svaki deployment je **reproducibilan, auditovan i rollbackabilan**.
`helm upgrade --install` je idempotentna operacija — možeš je pokrenuti 10 puta sa istim
rezultatom. To je idealno za pipeline.

---

## Zašto Helm kao Docker image u pipeline-u

`image: alpine/helm:3.14` — koristimo Helm unutar Docker kontejnera u CI.

Prednosti:
- Ista verzija Helm-a na svakom runneru, uvijek
- Nema instalacije na runner mašini
- Lako mijenjati verziju: samo promijeni tag
- Konzistentno sa pravilom projekta: sve kao Docker kontejner

---

## Kubeconfig u CI

Da bi Helm mogao komunicirati s K8s clusterom, treba mu `kubeconfig`.

Kubeconfig **ne ide u repo**. Ide kao GitLab CI/CD Variable, tipa File, base64 enkodiran.

```yaml
# Encode lokalno:
cat ~/.kube/config | base64 -w 0

# Postavi u GitLab:
# Settings → CI/CD → Variables
# Key: KUBE_CONFIG_DEV
# Type: Variable (ili File)
# Value: <base64 string>
# Protect: yes
# Mask: yes (ako File type ne podržava mask, koristi Variable type)
```

U job skripti:

```yaml
before_script:
  - mkdir -p ~/.kube
  - echo $KUBE_CONFIG_DEV | base64 -d > ~/.kube/config
  - chmod 600 ~/.kube/config
```

---

## Deploy pattern za project-A

```yaml
deploy:dev:
  stage: deploy
  image: alpine/helm:3.14
  environment:
    name: dev
    url: https://app.dev.firma.com
  before_script:
    - mkdir -p ~/.kube
    - echo $KUBE_CONFIG_DEV | base64 -d > ~/.kube/config
  script:
    - >
      helm upgrade --install helloworld ./helm/helloworld
      --namespace helloworld-dev
      --create-namespace
      -f helm/helloworld/values/dev.yaml
      --set image.tag=$CI_COMMIT_SHORT_SHA
      --wait
      --timeout 5m
      --atomic
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

Objašnjenje svake opcije:

- `upgrade --install` — ako release postoji, upgrade; ako ne, install. Idempotentno.
- `--namespace helloworld-dev` — svaki environment ima vlastiti namespace.
- `--create-namespace` — kreira namespace ako ne postoji.
- `-f values/dev.yaml` — environment-specifične vrijednosti (replicas, resources, ingress host).
- `--set image.tag=$CI_COMMIT_SHORT_SHA` — točna verzija image-a za ovaj commit.
- `--wait` — čeka da svi Podovi budu Ready prije nego job završi.
- `--timeout 5m` — max 5 minuta čekanja. Ako nije Ready za 5 min, job faila.
- `--atomic` — ako deployment faila (timeout, crash), automatski rollback na prethodnu verziju.

`--atomic` je ključan za production safety: nikad ne ostavljaš broken deployment.

---

## `--wait` i `--timeout`: zašto su neophodni

Bez `--wait`, Helm job završi čim K8s prihvati manifeste — ali Pod možda još nije startao.

Sa `--wait`, Helm čeka da su svi Podovi, Deploymenti i Stateful seti u `Ready` stanju.
Ako job završi uspješno, znamo da aplikacija **stvarno radi**, ne samo da su manifesti prihvaćeni.

`--timeout 5m` sprečava da job visi beskonačno ako postoji problem (pogrešan image tag,
nedovoljan CPU/memory, imagePullBackOff). Nakon 5 minuta, job faila s greškom.

---

## Rollback u pipeline-u

Opcija 1 — automatski (preporučeno): `--atomic` u helm deploy jobu.

Opcija 2 — manuelni rollback job:

```yaml
rollback:dev:
  stage: deploy
  image: alpine/helm:3.14
  when: manual
  before_script:
    - echo $KUBE_CONFIG_DEV | base64 -d > ~/.kube/config
  script:
    - helm rollback helloworld --namespace helloworld-dev
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

Opcija 3 — re-run deploy job iz starijeg pipeline-a (pogledaj `01-pipeline-strategija.md`).

---

## Smoke test posle deploya

Deploy job koji završi uspješno ne garantuje da **aplikacija odgovara na HTTP zahtjeve**.
Smoke test to provjerava:

```yaml
verify:dev:
  stage: verify
  image: curlimages/curl:latest
  script:
    - sleep 10  # daj LoadBalanceru da ažurira
    - curl -f --max-time 30 https://app.dev.firma.com/
    - curl -f --max-time 30 https://app.dev.firma.com/health
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

`-f` flag: curl vraća non-zero exit code ako HTTP response nije 2xx ili 3xx.
Ako zdravstveni check faila, pipeline faila i tim prima notifikaciju.

---

## Values fajlovi po environmentu

```
helm/helloworld/
  Chart.yaml
  values.yaml          # defaultne vrijednosti
  values/
    dev.yaml           # dev overrides
    staging.yaml       # staging overrides
    prod.yaml          # prod overrides
```

`values/dev.yaml` primjer:
```yaml
replicaCount: 1
ingress:
  host: app.dev.firma.com
resources:
  requests:
    cpu: 100m
    memory: 64Mi
```

`values/prod.yaml` primjer:
```yaml
replicaCount: 3
ingress:
  host: app.firma.com
resources:
  requests:
    cpu: 500m
    memory: 256Mi
```

Ista Helm chart, različite konfiguracije po environmentu.

---

## Veza sa project-A

Svaki push na `main` pokreće `deploy:dev` i `deploy:staging` jobove.
Oba koriste isti Helm chart iz `./helm/helloworld/`, ali različite values fajlove.
`--set image.tag=$CI_COMMIT_SHORT_SHA` garantuje da je deployovan točno onaj image
koji je buildan u istom pipeline-u — ne neki stariji, ne `latest`.
