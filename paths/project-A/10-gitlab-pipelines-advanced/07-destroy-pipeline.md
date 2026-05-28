# 07 — Destroy pipeline

## Teorija

Destroy pipeline je **prva klasa citizen** u DevOps projektu. Infrastruktura koja se
ne može uredno obrisati je infrastruktura koja košta novac i stvara sigurnosne rizike
tokom vikenda. Destroy mora biti testiran, dokumentovan i što jednostavniji za pokretanje.

---

## Zašto destroy mora biti u pipeline-u

Lokalni `terraform destroy` ima iste probleme kao i lokalni `terraform apply`:
nije auditovan, zavisi od lokalnog statea, credentials moraju biti na laptopu.

Destroy kroz pipeline:
- Auditovan: vidiš ko je pokrenuo i kada
- Siguran: koristi iste OIDC credentials kao apply
- Redoslijed: pipeline osigurava da se Helm briše prije Terraforma
- Zaštićen: destroy za prod zahteva approval

---

## Manuelni destroy job u pipeline-u

```yaml
destroy:dev:
  stage: destroy
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  when: manual
  environment:
    name: dev
    action: stop
  before_script:
    - echo $KUBE_CONFIG_DEV | base64 -d > ~/.kube/config
  script:
    - # Korak 1: Helm uninstall
    - helm uninstall helloworld --namespace helloworld-dev || true
    - kubectl delete namespace helloworld-dev || true
    - # Korak 2: Terraform destroy
    - cd terraform/environments/dev
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
    - terraform destroy -auto-approve
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

Redoslijed je bitan: **Helm briše K8s resurse**, zatim **Terraform briše infrastrukturu**.
Ako obrneš redoslijed, Terraform pokuša obrisati EKS node group dok su Pods aktivni —
može hangati ili failovati.

---

## Zaštita: destroy za prod zahteva approval

Produkcija ne smije biti obrisana bez eksplicitnog approval-a:

1. GitLab UI → Settings → CI/CD → Protected Environments
2. Dodaj `prod` kao protected environment
3. Postavi required approvers (senior engineer ili team lead)

```yaml
destroy:prod:
  stage: destroy
  when: manual
  environment:
    name: prod
    action: stop
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
      when: manual
```

Čak i sa `when: manual`, protected environment zahteva drugi korak odobrenja.
Dvostruka zaštita: niko ne može slučajno obrisati prod.

---

## Scheduled destroy za dev

Razvojni clusteri ne trebaju raditi 24/7. Svaki petak navečer: destroy.
Svaki ponedjeljak ujutro: pipeline kreira sve iznova (`terraform apply`).

```yaml
destroy:scheduled:dev:
  stage: destroy
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - helm uninstall helloworld --namespace helloworld-dev || true
    - cd terraform/environments/dev
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
    - terraform destroy -auto-approve
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        DESTROY_TARGET: dev
```

GitLab Schedules (Settings → CI/CD → Schedules):
```
Cron: 0 23 * * 5    →  Svaki petak u 23:00
Branch: main
Variables: DESTROY_TARGET=dev
```

Za dynamic review envs, scheduled destroy svake večeri u 23:00:

```yaml
destroy:scheduled:review-apps:
  stage: destroy
  script:
    - |
      # Pronađi sve namespaceove koji počinju s helloworld-mr-
      for ns in $(kubectl get namespaces -o name | grep helloworld-mr-); do
        helm uninstall helloworld-$(echo $ns | cut -d/ -f2) -n $(echo $ns | cut -d/ -f2) || true
        kubectl delete $ns || true
      done
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        DESTROY_TARGET: review-apps
```

---

## "Nuclear" destroy: cijeli cluster

Poseban, maksimalno zaštićen job za brisanje EKS clustera i sve infrastrukture:

```yaml
destroy:nuclear:
  stage: destroy
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  when: manual
  allow_failure: false
  environment:
    name: nuclear
    action: stop
  script:
    - echo "PAŽNJA: Brisanje kompletne infrastrukture za $TARGET_ENV!"
    - cd terraform/environments/$TARGET_ENV
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
    - terraform destroy -auto-approve -target=module.eks
    - terraform destroy -auto-approve  # ostatak infrastrukture
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

`nuclear` environment u GitLab je protected sa striktnim approverima.
Ovo je "break glass" procedura — koristi se za čišćenje projekta ili sandbox reseta.

---

## Praktičan `destroy:dev` job YAML (finalna verzija)

```yaml
destroy:dev:
  stage: destroy
  image: alpine:3.19
  when: manual
  environment:
    name: dev
    action: stop
  before_script:
    - apk add --no-cache curl bash
    - curl -LO https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl
    - chmod +x kubectl && mv kubectl /usr/local/bin/
    - mkdir -p ~/.kube
    - echo "$KUBE_CONFIG_DEV" | base64 -d > ~/.kube/config
  script:
    - echo "=== Korak 1: Helm uninstall ==="
    - helm uninstall helloworld --namespace helloworld-dev --wait || true
    - kubectl delete namespace helloworld-dev --wait=true || true
    - echo "=== Korak 2: Terraform destroy ==="
    - docker run --rm
        -e AWS_ROLE_ARN=$DEV_AWS_ROLE_ARN
        -v $(pwd)/terraform:/terraform
        hashicorp/terraform:1.7 -chdir=/terraform/environments/dev
        destroy -auto-approve
    - echo "=== Destroy kompletiran ==="
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

---

## Veza sa project-A

Tokom učenja, destroy je tvoj prijatelj — kreira i briši infrastrukturu slobodno.
EKS cluster košta čak i kad nema workloada (node instancee su tu).
Scheduled destroy + scheduled create (ponedjeljak ujutro) štedi 60-70% troškova
za dev environment koji se koristi samo radnim danima.

Napravi naviku: svaki put kad završiš lab sesiju → pokreni `destroy:dev` job.
