# 14 — kubectl Referenca i Debug

Kompletna praktična kubectl referenca za svakodnevni rad i debugging produkcijskih problema na project-A clusteru.

---

## Context i cluster management

```bash
# Vidi sve dostupne contexte (clustere)
kubectl config get-contexts
# CURRENT   NAME                    CLUSTER                 AUTHINFO    NAMESPACE
# *         project-a-dev           kind-project-a-dev      kind-...    project-a-dev
#           project-a-prod-eks      project-a-prod.eks      eks-...     project-a-prod

# Promijeni context
kubectl config use-context project-a-prod-eks

# Postavi default namespace za context (da ne moraš -n svaki put)
kubectl config set-context --current --namespace=project-a-prod

# Kratki prikaz trenutnog contexta
kubectl config current-context

# Merge kubeconfig (lokalni kind + EKS)
export KUBECONFIG=~/.kube/config:~/.kube/eks-config
kubectl config view --merge --flatten > ~/.kube/merged-config
```

**Preporučeni alati za context switching:**
```bash
# kubectx i kubens — brže od kubectl config
kubectx project-a-prod-eks     # promijeni cluster
kubens project-a-prod          # promijeni namespace

# Ili aliasi
alias k='kubectl'
alias kp='kubectl -n project-a-prod'
alias kd='kubectl -n project-a-dev'
alias kprod='kubectl config use-context project-a-prod-eks'
alias kdev='kubectl config use-context kind-project-a-dev'
```

---

## Svakodnevne komande

### Pregled resursa

```bash
# Podovi s IP adresama i node-ovima
kubectl get pods -n project-a-prod -o wide

# Live update (watch)
kubectl get pods -n project-a-prod --watch
kubectl get pods -n project-a-prod -w    # kraće

# Sve vrste resursa odjednom
kubectl get all -n project-a-prod

# Eventi sortirani po vremenu (kritično za debugging)
kubectl get events -n project-a-prod --sort-by='.lastTimestamp'
kubectl get events -n project-a-prod --sort-by='.lastTimestamp' | tail -20

# Resursi u svim namespace-ovima
kubectl get pods --all-namespaces
kubectl get pods -A    # kraće

# Prikaz labela
kubectl get pods -n project-a-prod --show-labels
kubectl get pods -n project-a-prod -l app=go-service    # filtriraj po labelu
```

### Detaljni opisi

```bash
# Opis poda — sadrži Events sekciju, ključnu za debugging
kubectl describe pod go-service-7f9d-xk8p2 -n project-a-prod

# Opis node-a — prikazuje resurse, pode, taintove
kubectl describe node ip-10-0-3-45.eu-west-1.compute.internal

# Opis servisa — sadrži Endpoints, selector
kubectl describe svc go-service -n project-a-prod

# Opis deploymenta — conditions, rollout status
kubectl describe deployment go-service -n project-a-prod
```

### Logovi

```bash
# Logovi poda (svi kontejneri ako ih je samo jedan)
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod

# Prethodni (crashnuti) pod
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod --previous
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod -p    # kraće

# Specifičan kontejner (multi-container pod, ili init container)
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod -c go-service
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod -c wait-for-mysql

# Follow (streaming)
kubectl logs -f go-service-7f9d-xk8p2 -n project-a-prod
kubectl logs -f deployment/go-service -n project-a-prod    # follow Deployment (aktivan pod)

# Svi podovi određenog labela
kubectl logs -l app=go-service -n project-a-prod --all-containers

# Zadnjih N linija
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod --tail=100

# Logovi od određenog vremena
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod --since=1h
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod --since-time="2026-05-27T10:00:00Z"
```

### Exec — ulazak u kontejner

```bash
# Interaktivna shell sesija
kubectl exec -it go-service-7f9d-xk8p2 -n project-a-prod -- sh
kubectl exec -it go-service-7f9d-xk8p2 -n project-a-prod -- bash    # ako postoji bash

# Specifičan kontejner u multi-container podu
kubectl exec -it go-service-7f9d-xk8p2 -n project-a-prod -c go-service -- sh

# Jednolinijska komanda bez TTY
kubectl exec go-service-7f9d-xk8p2 -n project-a-prod -- env | grep DB_
kubectl exec go-service-7f9d-xk8p2 -n project-a-prod -- cat /app/config.yaml
kubectl exec go-service-7f9d-xk8p2 -- wget -qO- http://mysql:3306
```

### Port forwarding

```bash
# Forward lokalnog porta na servis
kubectl port-forward svc/go-service 8080:8080 -n project-a-prod
# Sada http://localhost:8080 → go-service u clusteru

# Forward na specifičan pod (za debugging jednog poda)
kubectl port-forward pod/mysql-0 3306:3306 -n project-a-prod
# Sada mysql klijent na localhost:3306 → MySQL pod direktno

# Port forward u backgroundu
kubectl port-forward svc/go-service 8080:8080 -n project-a-prod &
# Zaustavi: kill %1 ili fg + Ctrl+C

# Koristi za:
# - Direktni pristup Prometheus UI: kubectl port-forward svc/prometheus 9090 -n monitoring
# - Grafana: kubectl port-forward svc/grafana 3000 -n monitoring
# - MySQL direktno: kubectl port-forward pod/mysql-0 3306 -n project-a-prod
```

### Rollout management

```bash
# Status deploya (čeka da završi)
kubectl rollout status deployment/go-service -n project-a-prod

# Historija revizija
kubectl rollout history deployment/go-service -n project-a-prod
kubectl rollout history deployment/go-service -n project-a-prod --revision=3   # detalji revizije

# Rollback na prethodnu reviziju
kubectl rollout undo deployment/go-service -n project-a-prod

# Rollback na specifičnu reviziju
kubectl rollout undo deployment/go-service -n project-a-prod --to-revision=2

# Rolling restart (novi podovi s novim Secrets/ConfigMaps)
kubectl rollout restart deployment/go-service -n project-a-prod

# Pauziraj/nastavi rollout (za staged deploy)
kubectl rollout pause deployment/go-service -n project-a-prod
kubectl rollout resume deployment/go-service -n project-a-prod
```

### Apply i dry-run

```bash
# Uvijek provjeri prije apply-a
kubectl apply -f deployment.yaml --dry-run=client
kubectl apply -f deployment.yaml --dry-run=server    # validira i na serveru (strože)

# Prikaži razliku od trenutnog stanja u clusteru
kubectl diff -f deployment.yaml

# Apply s output-om što se promijenilo
kubectl apply -f deployment.yaml --output=yaml

# Forsirani brisanje (pažljivo!)
kubectl delete pod go-service-7f9d-xk8p2 -n project-a-prod    # graceful, 30s timeout
kubectl delete pod go-service-7f9d-xk8p2 -n project-a-prod --force --grace-period=0   # odmah

# Scale
kubectl scale deployment/go-service -n project-a-prod --replicas=5
kubectl scale deployment/go-service -n project-a-prod --replicas=0   # gasi sve pode
```

---

## Debugging po scenariju

### Scenario 1 — Pod se ne pokrenuo / u lošem stanju

```bash
# Korak 1: Vidi status
kubectl get pods -n project-a-prod
# STATUS kolona:
# Pending           → scheduler ne može naći node (resursi, taint, affinity)
# Init:0/2          → čeka init kontejnere
# Init:Error        → init container pao
# Init:CrashLoopBackOff → init container pada i restartuje
# ContainerCreating → image se povlači ili volume se montiraj
# ImagePullBackOff  → ne može povući Docker image
# ErrImagePull      → greška pri pull-u (registry, kredencijali)
# CrashLoopBackOff  → kontejner crashuje i restartuje
# OOMKilled         → ubijen zbog prekoračenja memory limit-a
# Completed         → Job pod završen uspješno
# Error             → exit code != 0
# Terminating       → u procesu brisanja (stuck = finalizer problem)

# Korak 2: Events sekcija (najvažnija za dijagnozu)
kubectl describe pod go-service-7f9d-xk8p2 -n project-a-prod
# Sekcija Events na kraju opisa — prikazuje uzrok problema

# Korak 3: Logovi (ako je kontejner uopće startao)
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod
kubectl logs go-service-7f9d-xk8p2 -n project-a-prod --previous   # crashnuti
```

**Dijagnoza po STATUS-u:**

```bash
# ImagePullBackOff
kubectl describe pod xxx | grep -A10 "Events:"
# Error: rpc error: code = Unknown desc = failed to pull and unpack image
# → Provjeri: image tag postoji? Ispravni imagePullSecrets?
kubectl get secret gitlab-registry-credentials -n project-a-prod   # postoji?

# CrashLoopBackOff
kubectl logs xxx --previous   # logovi zadnjeg crasha
kubectl describe pod xxx | grep "Exit Code"   # Exit Code: 1, 137, 2...
# 137 = OOMKill, 1 = aplikacijska greška, 2 = misuse of shell

# Pending — scheduler problem
kubectl describe pod xxx | grep -A20 "Events:"
# "0/3 nodes are available: 3 Insufficient memory"  → povećaj node ili smanji requests
# "0/3 nodes are available: 3 node(s) had taint"    → dodaj toleration
# "0/3 nodes are available: 3 node(s) didn't match pod anti-affinity"  → nema node-ova koji zadovoljavaju

# Terminating (stuck)
kubectl get pod xxx -o jsonpath='{.metadata.finalizers}'   # postoji li finalizer?
kubectl patch pod xxx -p '{"metadata":{"finalizers":[]}}' --type=merge   # ukloni finalizer (oprezno!)
```

### Scenario 2 — Pod radi ali servis ne odgovara

```bash
# Korak 1: Postoje li endpointovi?
kubectl get endpoints go-service -n project-a-prod
# Ako je ENDPOINTS = <none> → servis nema targetova

# Korak 2: Selector vs Label provjera
kubectl get svc go-service -n project-a-prod -o jsonpath='{.spec.selector}'
# {"app":"go-service"}
kubectl get pods -n project-a-prod --show-labels | grep go-service
# Labele moraju matchovati

# Korak 3: Direktni test iz drugog poda
kubectl exec -it nginx-xxx -n project-a-prod -- curl http://go-service:8080/health
# Ili iz debug poda
kubectl run debug --image=curlimages/curl -it --rm -n project-a-prod -- sh

# Korak 4: NetworkPolicy blokira?
kubectl get networkpolicies -n project-a-prod
kubectl describe networkpolicy go-service-netpol -n project-a-prod

# Korak 5: DNS rezolucija radi?
kubectl exec -it nginx-xxx -n project-a-prod -- nslookup go-service
# Ako DNS ne radi:
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### Scenario 3 — Skaliranje ne radi / HPA ne reagira

```bash
# HPA status i conditions
kubectl describe hpa go-service-hpa -n project-a-prod
# Prikazuje:
# - Current/Desired replicas
# - Current metrics (CPU, custom)
# - Conditions (AbleToScale, ScalingActive)

# Realne CPU/memory vrijednosti
kubectl top pods -n project-a-prod
kubectl top pods -n project-a-prod --sort-by=cpu

# Node kapacitet
kubectl top nodes
kubectl describe node ip-10-0-3-45.eu-west-1.compute.internal | grep -A10 "Allocated"

# Je li metrics-server dostupan?
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top pods -n kube-system    # metrics-server pod mora biti Running

# ResourceQuota blokira scale?
kubectl describe resourcequota -n project-a-prod
# Used vs Hard — ako je Used == Hard za pods, HPA ne može kreirati više
```

### Scenario 4 — Secret ili ConfigMap nije dostupan u podu

```bash
# Postoji li Secret?
kubectl get secret db-credentials -n project-a-prod

# Sadržaj Secret-a (bez otkrivanja vrijednosti)
kubectl get secret db-credentials -n project-a-prod -o jsonpath='{.data}' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for k, v in d.items():
    decoded = base64.b64decode(v).decode('utf-8')
    print(f'{k}: {decoded[:4]}*** (len={len(decoded)})')
"

# Dekodiranje specifičnog ključa
kubectl get secret db-credentials -n project-a-prod -o jsonpath='{.data.host}' | base64 -d

# Vidi li pod varijable?
kubectl exec -it go-service-xxx -n project-a-prod -- env | grep DB_
kubectl exec -it go-service-xxx -n project-a-prod -- env | grep -v PASSWORD   # bez lozinki

# Provjeri je li volume montiran
kubectl exec -it nginx-xxx -n project-a-prod -- ls -la /etc/nginx/conf.d/
kubectl exec -it nginx-xxx -n project-a-prod -- cat /etc/nginx/conf.d/default.conf

# ExternalSecret status
kubectl describe externalsecret db-credentials -n project-a-prod
kubectl get externalsecret -n project-a-prod   # Status kolona: SecretSynced / Error
```

### Scenario 5 — Node problem / visoka upotreba

```bash
# Koji podovi rade na problematičnom node-u?
kubectl get pods -n project-a-prod -o wide | grep ip-10-0-3-45

# Svi podovi na node-u (sve namespace-ove)
kubectl get pods --all-namespaces -o wide | grep ip-10-0-3-45

# Node conditions (Ready, MemoryPressure, DiskPressure)
kubectl describe node ip-10-0-3-45.eu-west-1.compute.internal | grep -A10 Conditions

# Cordon (spriječi nove pode na node-u)
kubectl cordon ip-10-0-3-45.eu-west-1.compute.internal

# Drain (premjesti sve pode s node-a)
kubectl drain ip-10-0-3-45.eu-west-1.compute.internal --ignore-daemonsets --delete-emptydir-data

# Uncordon (vrati node u rotaciju)
kubectl uncordon ip-10-0-3-45.eu-west-1.compute.internal
```

---

## kubectl explain — dokumentacija bez googlea

```bash
# Dokument za bilo koji K8s field
kubectl explain deployment.spec.strategy
kubectl explain deployment.spec.strategy.rollingUpdate

kubectl explain pod.spec.containers.resources
kubectl explain pod.spec.containers.resources.requests

kubectl explain networkpolicy.spec.ingress
kubectl explain networkpolicy.spec.egress

kubectl explain statefulset.spec.volumeClaimTemplates

# --recursive za pregled cijele strukture
kubectl explain deployment.spec --recursive | head -50
```

**Prednost pred Google-om**: uvijek tačno za verziju Kubernetes-a koji radi u clusteru, ne za random verziju dokumentacije.

---

## JSONPath — precizni upiti

```bash
# Koji image-i se koriste u svim podovima?
kubectl get pods -n project-a-prod -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u

# Pod IP-ovi s imenima
kubectl get pods -n project-a-prod -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.podIP}{"\n"}{end}'

# Node na kojima podovi rade
kubectl get pods -n project-a-prod -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\n"}{end}'

# Resource requests za sve kontejnere
kubectl get pods -n project-a-prod -o custom-columns='
  NAME:.metadata.name,
  CPU_REQ:.spec.containers[0].resources.requests.cpu,
  MEM_REQ:.spec.containers[0].resources.requests.memory,
  CPU_LIM:.spec.containers[0].resources.limits.cpu,
  MEM_LIM:.spec.containers[0].resources.limits.memory'

# Restartovi — podovi s više od 5 restartova
kubectl get pods -n project-a-prod -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}' | awk '$2 > 5'

# Svi image-i koji nisu "latest" (production hygiene)
kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | grep -v ':latest' | sort -u
```

---

## Upravljanje certifikatima (cert-manager)

```bash
# Stanje certifikata
kubectl get certificates -n project-a-prod
kubectl describe certificate project-a-tls -n project-a-prod

# CertificateRequest status
kubectl get certificaterequests -n project-a-prod

# Challenge status (ACME validacija)
kubectl get challenges -n project-a-prod

# Forsiraj obnovu certifikata
kubectl annotate certificate project-a-tls -n project-a-prod cert-manager.io/issue-temporary-certificate="true"
# ILI:
kubectl delete secret project-a-tls-cert -n project-a-prod   # cert-manager automatski rekreira
```

---

## Helm debugging

```bash
# Prikaz svih Helm releasa
helm list -n project-a-prod
helm list -A    # svi namespace-ovi

# Status releasea
helm status go-service -n project-a-prod

# Historija revizija
helm history go-service -n project-a-prod

# Rollback na prethodnu verziju
helm rollback go-service -n project-a-prod
helm rollback go-service 3 -n project-a-prod    # specifična revizija

# Rendiraj template bez deployment-a (debugging)
helm template go-service ./charts/go-service -f values-prod.yaml

# Dry-run deploy
helm upgrade go-service ./charts/go-service -f values-prod.yaml -n project-a-prod --dry-run

# Vidi što je upravo deployano (computed values)
helm get values go-service -n project-a-prod
helm get manifest go-service -n project-a-prod   # svi K8s objekti
```

---

## Korisni kubectl plugini (krew)

```bash
# Instalacija krew
kubectl krew install neat        # čistiji YAML output (bez managed fields)
kubectl krew install tree        # hijerarhijski prikaz resursa
kubectl krew install ctx         # brži context switch (= kubectx)
kubectl krew install ns          # brži namespace switch (= kubens)
kubectl krew install resource-capacity   # kapacitet node-ova pregledno

# Primjeri korištenja
kubectl neat get pod go-service-xxx -n project-a-prod    # čistiji YAML
kubectl tree deployment go-service -n project-a-prod     # ReplicaSet → Pod hijerarhija
kubectl resource-capacity --sort cpu.limit               # node kapacitet sortirano
```

---

## Brze dijagnostike — cheat sheet

```bash
# Restart deployment
kubectl rollout restart deployment/go-service -n project-a-prod

# Brzi health check svih podova
kubectl get pods -n project-a-prod | grep -v Running | grep -v Completed

# Podovi koji se puno restaruju
kubectl get pods -n project-a-prod | awk 'NR>1 && $4 > 5 {print $0}'

# Logovi svih podova jedne aplikacije odjednom
kubectl logs -l app=go-service -n project-a-prod --prefix=true --tail=50

# Je li deployment zaustavljen (u progress)?
kubectl rollout status deployment/go-service -n project-a-prod --timeout=5m

# Provjeri sve resource quote u namespace-u
kubectl describe resourcequota -n project-a-prod

# Forsiraj brisanje stuck namespace-a
kubectl get namespace project-a-old -o json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); d['spec']['finalizers']=[]; print(json.dumps(d))" | \
  kubectl replace --raw /api/v1/namespaces/project-a-old/finalize -f -
```

---

## Sigurnosna provjera prije produkcijskog deploy-a

```bash
# 1. Dry-run
kubectl apply -f ./k8s/ --dry-run=server -n project-a-prod

# 2. Diff
kubectl diff -f ./k8s/ -n project-a-prod

# 3. Provjeri PDB
kubectl get pdb -n project-a-prod

# 4. Provjeri HPA
kubectl get hpa -n project-a-prod

# 5. Trenutni rollout
kubectl rollout status deployment/go-service -n project-a-prod

# 6. Provjeri evente odmah nakon deploy-a
kubectl get events -n project-a-prod --sort-by='.lastTimestamp' | tail -20

# 7. Logovi odmah nakon deploy-a
kubectl logs -f -l app=go-service -n project-a-prod --since=2m
```
