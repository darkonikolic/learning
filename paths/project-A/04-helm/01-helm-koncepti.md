# 01 — Helm koncepti

## Problem bez Helm-a

Imaš nginx app koja se deploya na tri okruženja: dev, staging, prod.
Svako okruženje treba `Deployment`, `Service`, `Ingress`, `HorizontalPodAutoscaler`.

Bez Helm-a završiš sa:

```
k8s/
├── dev/
│   ├── deployment.yaml     ← skoro isti kao staging/prod
│   ├── service.yaml        ← identičan
│   ├── ingress.yaml        ← samo host se razlikuje
│   └── hpa.yaml
├── staging/
│   ├── deployment.yaml     ← copy-paste, promijenjen replicaCount
│   ├── service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
└── prod/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    └── hpa.yaml
```

12 fajlova od kojih je 80% identično. Promjena image taga znači editovanje na tri mjesta.
Griješka je garantovana. Ovo ne skalira.

## Helm = package manager za Kubernetes

Helm rješava ovaj problem isto kao što npm rješava problem JavaScript biblioteka.

Umjesto 12 YAML fajlova, imaš:
- jedne **template** fajlove sa varijabilnim dijelovima
- odvojene **values** fajlove po okruženju koji samo definišu šta se razlikuje

Deployment.yaml postaje template:

```yaml
replicas: {{ .Values.replicaCount }}
image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
```

A razlike živee u `values/dev.yaml`:

```yaml
replicaCount: 1
image:
  tag: latest
```

i `values/prod.yaml`:

```yaml
replicaCount: 3
image:
  tag: v1.4.2
```

## Tri ključna pojma

**Chart** — paket sa svim template fajlovima i default values. To je "recept".
Analogija: Docker image. Definicija aplikacije, nije pokrenuta instanca.

**Release** — konkretna instalacija chart-a u Kubernetes cluster.
Analogija: Docker container pokrenut iz image-a.
Jedan chart može imati više releases: `helloworld-dev`, `helloworld-staging`, `helloworld-prod`.

**Repository** — mjesto gdje se chart-ovi čuvaju i distribuišu.
Može biti HTTP server (klasično) ili OCI registry (moderno — GitLab, GHCR).

## Helm vs Kustomize

Oba alata rješavaju problem copy-paste YAML-a, ali na različit način.

| | Helm | Kustomize |
|---|---|---|
| Pristup | Template engine (Go templates) | Patch/overlay sistem |
| Logika | If/else, loops, funkcije | Nema — samo deklarativni patches |
| Kriva učenja | Strmija | Blaža |
| Kubectl integracija | Zasebni alat | `kubectl apply -k` |
| Registry distribucija | Da (OCI charts) | Ne direktno |

**Zašto Helm za project-A:** trebamo logiku u templates (HPA samo za staging/prod,
različiti resource limits, conditionals za ingress). Kustomize bi tu bio kompliciraniji.
Kustomize je bolji izbor kad imaš postojeće upstream YAML-ove koje ne želiš mijenjati.

## Helm 3 vs Helm 2

Helm 2 je imao komponentu zvanu **Tiller** — server-side daemon koji je živio u clusteru
i izvršavao promjene. Problem: Tiller je imao cluster-admin privilegije, što je
bio ozbiljan sigurnosni rizik.

Helm 3 (2019) je uklonio Tiller. Helm client direktno komunicira sa Kubernetes API-jem
koristeći tvoje kubeconfig credentials. Rezultat: mnogo jednostavnija instalacija,
bolji sigurnosni model.

Ako naiđeš na staru dokumentaciju koja pominje `helm init` ili Tiller — to je Helm 2,
preskoči je.

## Veza sa project-A

```
jedan chart:  helloworld/
tri releases: helloworld-dev     (namespace: helloworld-dev)
              helloworld-staging (namespace: helloworld-staging)
              helloworld-prod    (namespace: helloworld-prod)
N releases:   helloworld-mr-123  (dynamic review env per GitLab MR)
```

Isti chart, različite values. Promjena u template odmah vrijedi za sva okruženja.
Nova verzija app-e znači samo promjena `image.tag` vrijednosti — na jednom mjestu.
