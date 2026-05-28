# 08 - Kubernetes Best Practices

## Principi koji se plaćaju na duge staze

Ovi principi izgledaju kao overhead na početku. U produkciji, njihovo odsustvo znači: neobjašnjivi outages, sigurnosni incidents, nemogućnost debuggiranja. Vrijedi ih usvojiti od prvog dana.

## 1. Uvijek postaviti resource requests i limits

```yaml
# OBAVEZNO — bez ovoga scheduler leti slijepo
resources:
  requests:
    cpu: "50m"
    memory: "64Mi"
  limits:
    cpu: "200m"
    memory: "128Mi"
```

Zašto: bez requests, Kubernetes ne zna koliko resursa Pod treba. Scheduler može staviti previše Podova na jedan node. Bez limits, loš Pod može "pojesti" sve resurse na node-u i srušiti ostale Podove.

## 2. Liveness i Readiness probes obavezno

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3

livenessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 30
  periodSeconds: 20
  failureThreshold: 3
```

**Readiness** — "Da li je ovaj Pod spreman primati saobraćaj?" Service ne šalje zahtjeve Podu dok readiness probe ne prođe. Ključno za zero-downtime rolling deploy.

**Liveness** — "Da li je ovaj Pod još živ?" Ako failuje, Kubernetes restartuje Pod. Hvatanje deadlock-ova i hung procesa.

Razlika je bitna: Pod koji sporo starta (dugi initialDelaySeconds) treba readiness provjeru, ne liveness — liveness restart bi ga neprestano ubijao.

## 3. Ne koristiti `latest` tag

```yaml
# LOŠE
image: nginx:latest

# DOBRO
image: registry.gitlab.com/firma/project-a:a3f9c21

# PRIHVATLJIVO za development
image: nginx:1.25-alpine
```

Razlog: `latest` je mutabilan. Sutra može biti drugačiji image. Kubernetes ne može znati da postoji nova verzija — ne restartuje Pod automatski. Rollback postaje nemoguć ("na šta da rollback-ujem?").

SHA tag je jedinstven i immutable. Uvijek znate tačno što deploujete.

## 4. Secrets nikad u git repou

```bash
# .gitignore — obavezno
*.key
*.crt
*.pem
secrets.yaml
*-secret.yaml
.env
```

Čak i ako obrišete fajl u sljedećem commitu, git historija ga čuva. Scaneri (GitGuardian, truffleHog) pronaći će ga.

Alternativa: Sealed Secrets ili External Secrets Operator (vidi 04-configmap-i-secrets.md).

## 5. Koristiti namespaces za izolaciju

```bash
# Svako okruženje u svom namespace-u
kubectl create namespace helloworld-dev
kubectl create namespace helloworld-staging
kubectl create namespace helloworld-prod
```

Prednosti: `kubectl get all -n helloworld-dev` vraća samo resurse tog okruženja. Accidentalni brisanje smanjeno (teže obrisati prod namespace od dev). Resource Quotas po namespace-u sprečavaju jedan tim da pojede sve resurse.

## 6. Labels i annotations — konvencija

Labels su selektori i filteri. Annotations su metapodaci za alate.

```yaml
metadata:
  labels:
    # Standardne Kubernetes preporučene labele
    app.kubernetes.io/name: hello-world
    app.kubernetes.io/version: "1.2.3"
    app.kubernetes.io/component: frontend
    app.kubernetes.io/part-of: project-a
    app.kubernetes.io/managed-by: helm
    # Vaše labele
    environment: production
    team: platform
  annotations:
    # Za tooling, ne za selektore
    deployment.kubernetes.io/revision: "5"
    kubectl.kubernetes.io/last-applied-configuration: ...
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
```

Standardne `app.kubernetes.io/*` labele omogućavaju toolima (Helm, ArgoCD, monitoring) da razumiju strukturu bez custom konfiguracije.

## 7. Pod Disruption Budget za visoku dostupnost

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: hello-world-pdb
  namespace: helloworld-prod
spec:
  minAvailable: 1      # uvijek mora biti min 1 Pod dostupan
  selector:
    matchLabels:
      app: hello-world
```

PDB govori Kubernetes-u: "Kada radiš voluntary disruption (node drain, node upgrade), ne smiješ uzeti više Podova nego što PDB dozvoljava." Bez PDB-a, node drain može ubiti sve replike odjednom.

Ovo je posebno važno za produkciju gdje radite node upgrades ili cluster upgrades.

## 8. Ograničiti privilegije kontejnera

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  containers:
    - name: nginx
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
          add:
            - NET_BIND_SERVICE  # potrebno za nginx na portu 80
```

Kontejner koji radi kao root = mogući escalation do host root-a u slučaju container escape exploit-a. `readOnlyRootFilesystem` sprečava pisanje na filesystem osim na eksplicitno montovane volumene.

Za nginx: trebate `NET_BIND_SERVICE` capability za binding na port 80, ili promijenite port na 8080 (port < 1024 zahtijeva privilegije).

## AI workflow: security review manifesta

Kada pišete Kubernetes manifeste, rutinski upit Claude-u:

```
Evo mog Kubernetes Deployment manifesta.
Napravi security review — šta bi promijenio/dodao za produkcijsku upotrebu?
Objasni zašto je svaka promjena važna.

[paste manifest]
```

Ili za debugging:

```
Pod je u CrashLoopBackOff stanju. Evo describe outputa i logova.
Šta je uzrok i kako popraviti?

[paste kubectl describe pod output]
[paste kubectl logs output]
```

Claude razumije Kubernetes YAML i može objasniti svaki security ili operational aspekt u kontekstu vašeg projekta. Koristite ga kao drugi par očiju pri code review-u manifesta.

## Checklist za svaki novi K8s manifest

Prije commita manifest-a, prođite kroz:

- [ ] Resource requests i limits postavljeni
- [ ] Readiness i liveness probes definisane
- [ ] Image tag je SHA ili specifična verzija (ne `latest`)
- [ ] Namespace eksplicitno naveden
- [ ] Labels sadrže `app`, `environment`, `version`
- [ ] Nema hardcoded Secrets (koristite Secret objekte)
- [ ] `securityContext` s `runAsNonRoot: true`
- [ ] PDB kreiran ako je to produkcijsko okruženje
