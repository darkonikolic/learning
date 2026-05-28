# 02 - .gitlab-ci.yml Anatomija

## Srce pipeline-a

`.gitlab-ci.yml` je jedini fajl koji opisuje cijeli pipeline. Živi u **korijenu repoa**, verzionisan je u gitu zajedno s kodom. To nije slučajno — ako izmijenite aplikaciju i pipeline u istom commitu, oboje se mijenjaju atomično. Nema situacije gdje je novi kod deploovan starim pipeline-om.

GitLab čita ovaj fajl na svakom triggeru i konstruiše DAG (directed acyclic graph) jobova za izvršavanje.

## Top-level ključevi

```yaml
# Redosled stages — sekvencijalno
stages:
  - build
  - test
  - deploy

# Varijable dostupne svim jobovima
variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  DOCKER_DRIVER: overlay2

# Podrazumijevane postavke koje nasljeđuju svi jobovi
default:
  image: docker:24
  tags:
    - docker

# Uvoz vanjskih fajlova (modularizacija velikih pipeline-a)
include:
  - local: '.gitlab/ci/deploy.yml'
  - template: 'Security/SAST.gitlab-ci.yml'
```

`stages` definišu redosled. Ako ne navedete `stages`, svi jobovi idu u podrazumijevani stage `test`.

`variables` su environment varijable dostupne u svim jobovima. Možete ih override-ovati na nivou joba.

`default` postavlja vrijednosti koje svi jobovi nasljeđuju ako ne definišu vlastite. Korisno za `image`, `before_script`, `tags`.

`include` omogućava razbijanje velikog `.gitlab-ci.yml` na više fajlova. Za project-A ćemo početi s jednim fajlom.

## Job definicija

Job je osnovna jedinica. Mora biti unutar nekog stage-a.

```yaml
build-image:
  stage: build              # kojoj fazi pripada
  image: docker:24          # Docker image za ovaj job
  services:
    - docker:24-dind        # Docker-in-Docker daemon
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  artifacts:
    reports:
      dotenv: build.env     # preda varijable sljedećem jobu
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: always
    - when: never
```

`image` — Docker image koji runner pokreće kao kontejner za ovaj job. Sve komande iz `script` izvršavaju se unutar tog kontejnera.

`services` — dodatni kontejneri koji rade pored glavnog. Docker-in-Docker zahtijeva `docker:dind` service da bi `docker` komanda radila unutar joba.

`before_script` — komande koje se izvršavaju prije `script`. Tipično: prijava u registry, instalacija alata.

`script` — lista komandi koje job izvršava. Ako bilo koja komanda vrati non-zero exit code, job **fail-uje** i pipeline se zaustavlja.

`artifacts` — fajlovi koje job sačuva i preda dalje (sledećim jobovima ili za preuzimanje iz UI).

## rules vs only/except

Stari način kontrole kada se job izvršava:

```yaml
# STARI PRISTUP — izbjegavati
deploy:
  only:
    - main
  except:
    - tags
```

Novi pristup s `rules`:

```yaml
# MODERNI PRISTUP — koristiti uvijek
deploy:
  rules:
    - if: $CI_COMMIT_BRANCH == "main" && $CI_PIPELINE_SOURCE == "push"
      when: always
    - if: $CI_MERGE_REQUEST_ID
      when: manual
    - when: never
```

`rules` je moćniji jer:
- Podržava složene logičke izraze (`&&`, `||`)
- Može mijenjati varijable po uvjetu (`variables:` unutar rule-a)
- Može mijenjati `when` (always, manual, never, delayed)
- Evaluira se odozgo prema dolje, prva koja se podudara — primjenjuje se

`only/except` je deprecated. Ne koristite ga u novim pipeline-ima.

## Praktičan primer: minimalni pipeline za hello-world

```yaml
stages:
  - build
  - test

variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

default:
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

build-image:
  stage: build
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  rules:
    - if: $CI_COMMIT_BRANCH

test-image:
  stage: test
  script:
    - docker run --rm -d --name test-app -p 8080:80 $IMAGE_TAG
    - sleep 2
    - curl -f http://localhost:8080 || (docker logs test-app && exit 1)
    - docker stop test-app
  rules:
    - if: $CI_COMMIT_BRANCH
```

Ovaj pipeline radi dvije stvari: gradi image i provjerava da li nginx odgovara na HTTP zahtjev. Svega 30-ak linija, ali opisuje kompletan CI ciklus.

## Kako AI pomaže

Kada radite sa GitLab CI, jedan od najefikasnijih načina učenja je analiza cijelih fajlova uz pomoć Claude-a.

Primjeri upita koji dobro rade:

- "Evo mog `.gitlab-ci.yml`. Objasni mi šta radi svaki dio i zašto je strukturiran ovako."
- "Zašto ovaj job fail-uje? Evo loga: [paste loga]"
- "Refaktoriši ovaj pipeline da koristi `rules` umjesto `only/except`"
- "Dodaj stage za security scanning koji se pokreće samo na main branchu"

Strategija: počnite s minimalnim pipeline-om koji radi, pa postepeno dodajte kompleksnost. Claude može objasniti svaku izmjenu u kontekstu vašeg projekta.
