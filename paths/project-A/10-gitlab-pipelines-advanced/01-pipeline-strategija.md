# 01 — Pipeline strategija

## Teorija

Pipeline strategija odgovara na pitanje: **koji kod, kada, i kako se testira i deploya?**

Dvije dominantne strategije su GitFlow i trunk-based development. Izbor strategije direktno
određuje strukturu `.gitlab-ci.yml` i kompleksnost pipeline-a.

---

## Zašto trunk-based za project-A

**GitFlow** ima `develop`, `release/*`, `hotfix/*`, `feature/*` brancheve. Rezultat:
dugi živuci branchevi, česti merge konflikti, kompleksni pipeline koji mora znati
"u kojoj fazi smo". Za male timove to je overhead bez benefita.

**Trunk-based development** znači: svi rade na kratkim `feature/*` branchevima,
mergeuju u `main` često (bar svaki dan), a release je tag. `main` je uvijek deployable.

Za project-A (jedan nginx koji servira `index.html`) — trunk-based je jedini razuman izbor.
Nema smisla imati `develop` branch kad imaš jednu aplikaciju i cilj je naučiti pipeline.

---

## Branch strategija — šta koji branch pokreće

```
feature/*  →  build + test + dynamic env (review app)
main       →  build + test + deploy dev (auto) + staging (auto)
tag v*.*.*  →  deploy prod (manual approval)
```

Ovo nije slučajno. Iza svakog pravila stoji razlog:

- `feature/*` dobija **review app** jer tester mora vidjeti promjenu prije merga —
  ne tek kad stigne na dev.
- `main` deploya **dev i staging automatski** jer je `main` uvijek stabilna —
  ako je prošao review, prošao je test, prošao je CI, deploy je logičan slijed.
- `tag` za **prod je manual** jer prod deployment je svjesna odluka, ne nuspojava push-a.

---

## Kako radi: pipeline as code

`.gitlab-ci.yml` je **u repou**. To znači:

- Verzioniran: svaki commit mijenja pipeline zajedno sa kodom.
- Reviewovan: promjena pipeline-a prolazi kroz isti MR process kao i kod.
- Reproducibilan: znaš točno koji pipeline je radio za koji commit.

Alternativa (pipeline konfigurisan u GitLab UI) je anti-pattern — nije verzioniran,
ne znaš ko je mijenjao, ne možeš lako rollbackati.

---

## Praktičan primjer: rules blok

```yaml
workflow:
  rules:
    - if: $CI_COMMIT_BRANCH =~ /^feature\//
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/

build:
  stage: build
  rules:
    - if: $CI_COMMIT_BRANCH =~ /^feature\//
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/

deploy:prod:
  stage: deploy
  when: manual
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
```

---

## Environments u GitLab UI

GitLab UI → Operate → Environments prikazuje:

- Koji environments postoje (dev, staging, prod, review/MR-42...)
- Kada je zadnji deploy bio
- Ko je deployovao
- Link na live URL aplikacije

Ovo je vidljivo svakom članu tima bez ulaska u CI logove.

---

## Rollback: re-trigger starijeg pipeline joba

Rollback u GitLab-u nije posebna komanda — to je **re-run deploy joba iz starijeg pipeline-a**.

CI/CD → Pipelines → nađi stari pipeline → klikni na deploy job → "Run again"

Helm `--set image.tag=$CI_COMMIT_SHORT_SHA` osigurava da ponovo deployuješ točno onu
verziju Docker image-a koja je bila u tom commitu. Zato je `CI_COMMIT_SHORT_SHA` ključan
parametar — ne koristiti `latest` tag.

---

## Veza sa project-A

Za project-A primjenujemo tačno ovu strategiju:

1. Radiš na `feature/dodaj-kontakt-stranicu`
2. Push → pipeline builda Docker image, deploya review app na `mr-42.dev.firma.com`
3. Tester klikne link iz MR-a, provjeri
4. Merge u `main` → auto deploy na dev, zatim staging
5. `git tag v1.2.0 && git push --tags` → manual approve → prod deploy
