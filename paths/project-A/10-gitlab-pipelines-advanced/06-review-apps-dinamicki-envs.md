# 06 — Review Apps i dinamički environments

## Teorija

Review App je **automatski deployment svakog MR-a na vlastiti URL**.
Tester, PM ili tech lead može vidjeti feature u akciji, ne u opisu teksta MR-a —
nego klikne link i vidi živu aplikaciju. Merge decision se donosi na osnovu stvarnog
ponašanja, ne procjene.

---

## Zašto review apps mijenjaju workflow

Bez review apps:
1. Developer mergea MR
2. Deploya na dev
3. Tester testira na dev-u (koji može imati još 3 druge neterminirane features)
4. Bug nađen — novi MR, čekanje, ...

Sa review apps:
1. MR je otvoren → review app je odmah tu, na svom URL-u, izolovano
2. Tester testira bez buke od ostalih features
3. PM vidi šta se mijenja vizualno, ne čitajući kod
4. Merge se radi kad svi zadovoljni
5. Review app se automatski briše

---

## Kako radi: review:deploy job

```yaml
review:deploy:
  stage: deploy
  image: alpine/helm:3.14
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
    on_stop: review:stop
    auto_stop_in: 3 days
  before_script:
    - echo $KUBE_CONFIG_DEV | base64 -d > ~/.kube/config
  script:
    - >
      helm upgrade --install helloworld-mr-$CI_MERGE_REQUEST_IID
      ./helm/helloworld
      --namespace helloworld-mr-$CI_MERGE_REQUEST_IID
      --create-namespace
      -f helm/helloworld/values/dev.yaml
      --set image.tag=$CI_COMMIT_SHORT_SHA
      --set ingress.host=mr-$CI_MERGE_REQUEST_IID.dev.firma.com
      --wait --timeout 5m --atomic
  rules:
    - if: $CI_MERGE_REQUEST_IID
```

Ključne tačke:
- `environment: name: review/$CI_MERGE_REQUEST_IID` — svaki MR ima vlastiti named environment
- `url:` — GitLab prikazuje klikabilni link direktno u MR panelu
- `on_stop: review:stop` — koja job briše environment kad se MR zatvori
- `auto_stop_in: 3 days` — automatski stop ako se zaboravi otvoreni MR
- `--set ingress.host=...` — override host za ovaj specifični MR
- `--namespace helloworld-mr-$CI_MERGE_REQUEST_IID` — potpuna izolacija od ostalih MR-ova

---

## Dynamic URL: kako radi routing

Za `mr-42.dev.firma.com` da radi, potreban je wildcard DNS record:

```
*.dev.firma.com  →  CNAME  →  <EKS ALB hostname>
```

Kubernetes Ingress s wildcard će matchati sve subdomene. Ili Terraform kreira
individual CNAME za svaki MR (čistiji, ali sporiji):

```hcl
resource "aws_route53_record" "review_app" {
  zone_id = var.hosted_zone_id
  name    = "mr-${var.mr_iid}.dev.firma.com"
  type    = "CNAME"
  ttl     = 60
  records = [var.alb_hostname]
}
```

Wildcard opcija je brža za review apps — DNS record postoji permanentno,
Ingress pravilo odlučuje koji namespace/service servira koji hostname.

---

## review:stop job — cleanup

```yaml
review:stop:
  stage: destroy
  image: alpine/helm:3.14
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    action: stop
  when: manual
  variables:
    GIT_STRATEGY: none
  before_script:
    - echo $KUBE_CONFIG_DEV | base64 -d > ~/.kube/config
  script:
    - helm uninstall helloworld-mr-$CI_MERGE_REQUEST_IID
        --namespace helloworld-mr-$CI_MERGE_REQUEST_IID || true
    - kubectl delete namespace helloworld-mr-$CI_MERGE_REQUEST_IID || true
  rules:
    - if: $CI_MERGE_REQUEST_IID
      when: manual
```

`action: stop` — govori GitLab-u da ovaj job terminira environment.
`when: manual` — job se može pokrenuti manuelno ILI automatski kad se MR zatvori (GitLab to radi).
`GIT_STRATEGY: none` — ne trebamo kod za destroy, samo kubectl/helm.
`|| true` — tolerišemo slučaj kada namespace/release već nisu tu.

---

## Šta kreira review env: detaljan flow

Kad se push na feature branch koji ima otvoreni MR:

1. **build job** — gradi Docker image, pushuje u registry sa tagom `$CI_COMMIT_SHORT_SHA`
2. **review:deploy job** (paralelno s testovima ili nakon, ovisno o konfiguraciji):
   - Helm deploy u novi namespace `helloworld-mr-42`
   - Ingress s hostom `mr-42.dev.firma.com`
3. GitLab prikazuje u MR panelu: `View app →` link na `https://mr-42.dev.firma.com`
4. Tester klikne, vidi feature

Opciono (za kompleksnije setupove): Terraform job kreira Route53 CNAME record za ovaj MR.

---

## Šta briše review env (on_stop flow)

Kad se MR mergea ili zatvori:

1. GitLab automatski okida job naveden u `on_stop:` (koji je `review:stop`)
2. `helm uninstall` — uklanja sve K8s resurse u namespaceu
3. `kubectl delete namespace` — čisti namespace
4. (Opciono) Terraform destroy za Route53 record
5. GitLab Environment status: "Stopped"

`auto_stop_in: 3 days` — ako MR ostane otvorena 3 dana bez aktivnosti, GitLab stopira
environment automatski (čak i ako review:stop nije manuelno pokrenut).

---

## Veza sa project-A

Za project-A, review apps su idealne za demonstraciju pipeline sposobnosti:

1. Napravi MR koji mijenja naslov u `index.html` iz "Hello World" u "Zdravo Svijete"
2. Pipeline automatski builda i deploya na `mr-5.dev.firma.com`
3. Vidiš promjenu bez da ijedan od ostalih environment-a ima tu promjenu
4. Merge → review app se briše → dev i staging dobijaju novu verziju automatski

Ovo je dokaz da pipeline radi end-to-end.
