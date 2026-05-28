# 06 — LAB: Napravi Helm chart

## Cilj

Kreirati funkcionalan Helm chart za hello-world nginx app,
deployati ga na lokalni kind cluster i verifikovati.

## Preduslovi

- kind cluster pokrenut (modul 03)
- kubectl konfigurisan za kind
- Helm instaliran ili dostupan kao Docker kontejner

## Helm kao Docker kontejner

Ako ne želiš instalirati Helm direktno:

```bash
alias helm='docker run --rm -it \
  -v $(pwd):/workspace \
  -v ~/.kube:/root/.kube \
  -w /workspace \
  alpine/helm:3.14'
```

Sada `helm` komande rade iz tekuceg direktorijuma.

## Korak 1: Generiši polazni chart

```bash
helm create helloworld
```

Ovo kreira kompletnu strukturu sa primjer templates. Pregledaj sta je kreirano:

```bash
ls -la helloworld/
ls -la helloworld/templates/
```

## Korak 2: Očisti suvišno

`helm create` generiše generic app sa puno primjera. Obrisi ono sto ne trebamo:

```bash
# Obrisi sve iz templates osim baznih
rm helloworld/templates/tests/
rm helloworld/templates/serviceaccount.yaml
rm helloworld/templates/hpa.yaml   # napravicemo vlastiti

# Obrisi primjer notes fajl
rm helloworld/templates/NOTES.txt
```

## Korak 3: Uredite Chart.yaml

```yaml
apiVersion: v2
name: helloworld
description: Nginx hello world app
type: application
version: 0.1.0
appVersion: "1.0.0"
```

## Korak 4: Zamijeni values.yaml

Zamijenite sadrzaj `values.yaml` minimalnim default-ima:

```yaml
replicaCount: 1

image:
  repository: nginx
  tag: alpine
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  host: hello.local

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

## Korak 5: Kreiraj values/local.yaml

```bash
mkdir helloworld/values
```

Sadrzaj `helloworld/values/local.yaml`:

```yaml
ingress:
  enabled: true
  host: hello.local
  annotations:
    kubernetes.io/ingress.class: nginx

image:
  pullPolicy: Never
```

## Korak 6: Provjeri generisani YAML bez deployvanja

```bash
helm template helloworld-local ./helloworld -f helloworld/values/local.yaml
```

Ovo ispisuje kompletan Kubernetes YAML koji bi bio primijenjen.
Provjeri da su vrijednosti ispravne.

Ako hoces vidjeti samo jedan template:

```bash
helm template helloworld-local ./helloworld \
  -f helloworld/values/local.yaml \
  -s templates/deployment.yaml
```

## Korak 7: Dry-run provjera

```bash
helm install helloworld-local ./helloworld \
  -f helloworld/values/local.yaml \
  --namespace helloworld-local \
  --create-namespace \
  --dry-run
```

`--dry-run` komunicira sa Kubernetes API-jem i validira YAML,
ali ne kreira resurse. Bolje od `helm template` za provjeru API kompatibilnosti.

## Korak 8: Deploy na kind cluster

Ucitaj image u kind ako koristis lokalni build (ne nginx:alpine):

```bash
kind load docker-image nginx:alpine
```

Deploy:

```bash
helm upgrade --install helloworld-local ./helloworld \
  -f helloworld/values/local.yaml \
  --namespace helloworld-local \
  --create-namespace \
  --wait
```

## Korak 9: Verifikacija

Provjeri Helm release:

```bash
helm list -n helloworld-local
helm status helloworld-local -n helloworld-local
```

Provjeri Kubernetes resurse:

```bash
kubectl get all -n helloworld-local
kubectl get ingress -n helloworld-local
```

Provjeri da pod radi:

```bash
kubectl port-forward -n helloworld-local svc/helloworld-local-helloworld 8080:80
# U drugom terminalu:
curl http://localhost:8080
```

## Korak 10: Kreiraj values za dev, staging, prod

`helloworld/values/dev.yaml`:

```yaml
replicaCount: 1
ingress:
  enabled: true
  host: hello.dev.firma.com
```

`helloworld/values/staging.yaml`:

```yaml
replicaCount: 2
ingress:
  enabled: true
  host: hello.staging.firma.com
resources:
  limits:
    cpu: 300m
    memory: 256Mi
```

`helloworld/values/prod.yaml`:

```yaml
replicaCount: 3
image:
  tag: v1.0.0
  pullPolicy: Always
ingress:
  enabled: true
  host: hello.firma.com
  tls: true
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

## Korak 11: Simuliraj upgrade

Promijeni `replicaCount` u `values/local.yaml` na 2 i upgraduj:

```bash
helm upgrade helloworld-local ./helloworld \
  -f helloworld/values/local.yaml \
  --namespace helloworld-local
```

Provjeri historiju release-a:

```bash
helm history helloworld-local -n helloworld-local
```

Rollback na prethodnu verziju:

```bash
helm rollback helloworld-local 1 -n helloworld-local
```

## Korak 12: Cleanup

```bash
helm uninstall helloworld-local -n helloworld-local
kubectl delete namespace helloworld-local
```

## AI workflow

Imas `Chart.yaml` i `deployment.yaml`. Daj ih Claude-u:

```
Evo mog Helm chart-a:
[Chart.yaml sadrzaj]
[deployment.yaml sadrzaj]

Molim te:
1. Provjeri da li ima gresaka u template sintaksi
2. Predlozi outputs koji bi bili korisni za CI/CD pipeline
3. Koji lifecycle hooks bi imali smisla za ovu aplikaciju?
```

Kada dobijes gresku iz `helm template` ili `helm install --dry-run`:

```
Dobio sam ovu gresku iz helm template:
[greska]

Evo relevantnog template fajla:
[sadrzaj]

Sta uzrokuje gresku i kako da je ispravim?
```
