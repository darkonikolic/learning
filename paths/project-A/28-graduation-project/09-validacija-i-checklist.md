# Validacija i Checklist

## Kako koristiti ovu listu

Prođi kroz svaku checklist tačku ručno — nemoj pretpostavljati da radi.
Svaka provjera treba biti aktivna (pokreni komandu, otvori URL, provjeri output).

Kada sve zeleno — projekt je završen.

## Lokalni environment (kind)

**Klaster:**
- [ ] `kind get clusters` prikazuje `project-a`
- [ ] `kubectl cluster-info --context kind-project-a` vraća URL bez errora
- [ ] `kubectl get nodes` prikazuje `control-plane` sa statusom `Ready`

**Ingress controller:**
- [ ] `kubectl get pods -n ingress-nginx` — controller pod je `Running`
- [ ] `curl -s http://localhost` vraća 404 (Ingress controller živ, ali nema route) ili nginx default page

**Aplikacija:**
- [ ] `kubectl get pods -n helloworld-local` — svi podovi `Running`, nema `CrashLoopBackOff`
- [ ] `kubectl get ingress -n helloworld-local` prikazuje host `app.local`
- [ ] `curl -H "Host: app.local" http://localhost/` vraća HTML sa "Hello World"
- [ ] `curl -H "Host: app.local" http://localhost/healthz` vraća `ok`
- [ ] Browser: `http://app.local` prikazuje "Hello World"
- [ ] Browser: `https://app.local` prikazuje "Hello World" (sa self-signed cert upozorenjem)

**Monitoring lokalno:**
- [ ] `kubectl get pods -n monitoring` — svi podovi `Running`
- [ ] `kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring` radi
- [ ] Grafana na `http://localhost:3000` dostupna (admin login radi)
- [ ] Grafana: nginx dashboard prikazuje metrike (requestovi, error rate)

**Helm:**
- [ ] `helm list -n helloworld-local` prikazuje `helloworld` release sa `STATUS: deployed`
- [ ] `helm history helloworld -n helloworld-local` prikazuje historiju release-a

## Dev environment (AWS EKS)

**Terraform infrastruktura:**
- [ ] `terraform state list` (u `envs/dev/`) prikazuje sve resurse (VPC, EKS, IAM, ...)
- [ ] `aws eks list-clusters --region eu-west-1` prikazuje `project-a-dev`
- [ ] `aws eks update-kubeconfig --name project-a-dev --region eu-west-1` ne daje error

**EKS klaster:**
- [ ] `kubectl get nodes` — svi nodovi `Ready`
- [ ] `kubectl get pods -n kube-system` — CoreDNS, kube-proxy running
- [ ] `kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller` — controller `Running`

**Aplikacija:**
- [ ] `kubectl get pods -n helloworld-dev` — svi podovi `Running`
- [ ] `kubectl get ingress -n helloworld-dev` — prikazuje ALB hostname
- [ ] `https://app.dev.firma.com` otvara u browseru sa validnim HTTPS (bez upozorenja)
- [ ] `curl https://app.dev.firma.com/healthz` vraća `ok`
- [ ] HTTP redirect radi: `curl -I http://app.dev.firma.com` vraća 301

**GitLab pipeline:**
- [ ] Pipeline na main branchu je zeleni (svi jobovi prošli)
- [ ] `docker-build` job: image dostupan u GitLab Container Registry
- [ ] `trivy-scan` job: nema HIGH/CRITICAL vulnerabilnosti (ili su acknowledged)
- [ ] `tf-plan-dev`: plan output vidljiv u MR komentarima
- [ ] `deploy-dev`: Helm release ažuriran sa novim image tagom

**Review app:**
- [ ] Kreiraj test MR (npr. promijeni `index.html`)
- [ ] `deploy-review` job kreirao namespace `mr-{N}` sa aplikacijom
- [ ] `https://mr-{N}.dev.firma.com` dostupan sa HTTPS
- [ ] Zatvaranjem MR: `destroy-review` job obrisao namespace i resurse

**Terraform destroy test (kritično!):**
- [ ] `terraform destroy -var-file=dev.tfvars` (u `envs/dev/`) završava bez errora
- [ ] `aws eks list-clusters` više ne prikazuje `project-a-dev`
- [ ] AWS konzola: VPC obrisan, ALB obrisan, NAT gateway obrisan
- [ ] Re-kreiranje sa `terraform apply` radi čisto

## Staging environment (AWS EKS)

Staging je identičan dev-u ali sa staging domenama i strožijim resource limits.

- [ ] Sve dev checklistovi prolaze i za staging
- [ ] `https://app.staging.firma.com` dostupan
- [ ] Deploy na staging zahtjeva manual trigger (nije automatski)
- [ ] Terraform state za staging je odvojen od dev (`envs/staging/terraform.tfstate`)

## Produkcija (AWS EKS)

**Terraform:**
- [ ] `prevent_destroy = true` je postavljeno na kritičnim resursima (EKS, VPC, S3)
- [ ] `terraform plan` na prod ne prikazuje neočekivane promjene

**Aplikacija:**
- [ ] `https://app.firma.com` otvara sa validnim ACM sertifikatom
- [ ] `kubectl get hpa -n helloworld-prod` prikazuje HPA sa `minReplicas: 3`
- [ ] `kubectl get pods -n helloworld-prod` — 3 poda `Running`
- [ ] Image tag je specifična verzija (npr. `abc1234`), ne `latest`

**Deploy workflow:**
- [ ] `deploy-prod` job zahtjeva manual approval (protected environment)
- [ ] Deploy prošao: `helm history helloworld -n helloworld-prod` pokazuje novu verziju
- [ ] Rollback radi: `helm rollback helloworld 1 -n helloworld-prod` vraća prethodnu verziju

**Monitoring:**
- [ ] `https://monitoring.firma.com` otvara Grafana
- [ ] AlertManager konfigurisan sa Slack webhook-om
- [ ] Postoji alert koji bi okidao na pod crash — testiraj ga:
  ```bash
  kubectl delete pod -l app.kubernetes.io/name=helloworld -n helloworld-prod --force
  # Alert treba stići na Slack unutar 5 minuta
  ```

## Čest razlog za neuspjeh

Ako checklist ne prolazi, ovaj redosljed debugging koraka rješava 90% problema:

1. **Pod ne startuje** → `kubectl describe pod <ime>` i `kubectl logs <ime>`
2. **Ingress ne radi** → `kubectl describe ingress` i `kubectl get events`
3. **HTTPS ne radi** → provjeri ACM cert status u AWS konzoli, provjeri ALB listener
4. **Pipeline failuje** → kopiraj cijeli failed job log u Claude
5. **Terraform failuje** → provjeri AWS permisije, provjeri je li state konzistentan

## Šta dalje

Projekat je kompletan. Sljedeći logični koraci za napredovanje:

**Multi-service arhitektura**: Dodaj backend API servis, konfiguraci service-to-service
komunikaciju unutar klastera. Uvedi Kubernetes NetworkPolicy za izolaciju.

**GitOps sa ArgoCD**: Umjesto `helm upgrade` u pipeline-u, ArgoCD
kontinuirano sinkronizuje Helm chart iz repo-a na klaster. Pipeline samo
pushuje promjenu u Git, ArgoCD detectuje i deploya.

**Cost optimizacija sa Karpenter**: Zamijeni managed node group sa Karpenter
node provisioner-om — kreira nodove tačno po potrebi, bira najjeftiniji instance tip.

**Service mesh sa Istio**: Mutual TLS između servisa, napredni traffic
management, observability sa Jaeger distributed tracing.

**AI workflow za maintain**: Kada dobiješ novi Kubernetes CVE alert ili
AWS deprecation notice, koristiš isti AI workflow iz modula 10:
"Evo tfsec output-a za moju infrastrukturu, šta je prioritetno za fix?"
