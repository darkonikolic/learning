# 02 — Environments i deployments

## Teorija

GitLab Environment je **logična destinacija** na koju deployuješ: dev, staging, prod,
review/MR-42. Nije server — to je koncept koji GitLab koristi za praćenje deployova,
kontrolu pristupa i vizualni pregled stanja sistema.

---

## Zašto environments eksplicitno definisati

Bez `environment:` keyword-a u jobu, GitLab ne zna da je job deployment. Sa njim:

- Job je vidljiv u Environments panelu
- MR prikazuje link na live URL review appa
- GitLab prati deployment historiju (ko, kada, što)
- Možeš zaštititi environment (required approvals)
- Možeš definisati varijable specifične samo za taj environment

---

## Kako radi: environment keyword

```yaml
deploy:dev:
  stage: deploy
  environment:
    name: dev
    url: https://app.dev.firma.com
  script:
    - helm upgrade --install helloworld ./helm/helloworld ...
```

`name` mora biti jedinstven. Za dynamic envs koristi varijable:

```yaml
review:deploy:
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
    on_stop: review:stop
```

`$CI_MERGE_REQUEST_IID` je broj MR-a (42, 43...). Svaki MR dobija svoj environment.

---

## Deployment tracking

GitLab bilježi za svaki deployment:

- Koji commit je deployovan (`$CI_COMMIT_SHA`)
- Ko je pokrenuo job (GitLab user)
- Kada je deployment bio
- Koji pipeline je pokrenuo deployment
- Status: running / success / failed / canceled

Ovo je audit trail bez ikakve dodatne konfiguracije.

---

## Protected environments

Production environment treba da zahteva **manual approval** prije nego deployment krene.

GitLab UI → Settings → CI/CD → Protected Environments:

- `prod` environment → dodaj required approvers (npr. team lead)
- Deployment job se pauzira, šalje notifikaciju approveru
- Approver klikne "Approve and run" ili "Reject"

```yaml
deploy:prod:
  stage: deploy
  when: manual
  environment:
    name: prod
    url: https://app.firma.com
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
```

`when: manual` je GitLab-ova strana — job ne krene automatski.
Protected environment je dodatni sloj — čak i ručni trigger mora biti approveovan.

---

## Environment variables scoped po environmentu

GitLab CI/CD Variables mogu biti scope-ovane:

```
Settings → CI/CD → Variables

KUBE_CONFIG   →  Environment scope: dev      →  base64 kubeconfig za dev cluster
KUBE_CONFIG   →  Environment scope: prod     →  base64 kubeconfig za prod cluster
```

Isti naziv varijable, različita vrijednost per environment. Pipeline automatski
dobija ispravnu varijablu za environment u koji deploya.

---

## Stop environment: on_stop za dynamic envs

Dynamic review envs moraju biti obrisani kad se MR zatvori (merge ili close).

```yaml
review:deploy:
  stage: deploy
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
    on_stop: review:stop
  rules:
    - if: $CI_MERGE_REQUEST_IID

review:stop:
  stage: destroy
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    action: stop
  when: manual
  variables:
    GIT_STRATEGY: none
  script:
    - helm uninstall helloworld-mr-$CI_MERGE_REQUEST_IID -n helloworld-mr-$CI_MERGE_REQUEST_IID || true
    - # terraform destroy za Route53 record
  rules:
    - if: $CI_MERGE_REQUEST_IID
      when: manual
```

`action: stop` govori GitLab-u: ovaj job briše environment.
`GIT_STRATEGY: none` — ne trebamo checkout repoa za destroy.
`|| true` — ako namespace već nije tu, job ne smije failovati.

---

## Praktičan primjer: svi environments za project-A

```yaml
deploy:dev:
  environment:
    name: dev
    url: https://app.dev.firma.com

deploy:staging:
  environment:
    name: staging
    url: https://app.staging.firma.com

deploy:prod:
  environment:
    name: prod
    url: https://app.firma.com

review:deploy:
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
    on_stop: review:stop
```

---

## Veza sa project-A

Svaki deploy Helm chart-a za project-A ide u named environment.
Kad mergeuješ MR s feature za novi naslov na stranici:

1. `review:stop` se automatski okine → namespace obrisan → Route53 record uklonjen
2. `deploy:dev` se pokrene → nova verzija na dev
3. U GitLab UI Environments vidiš: dev = commit `a3f9b12`, staging = commit `d1c8e44`

Razlika između verzija na različitim environmentima je odmah vidljiva.
