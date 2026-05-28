# Alati i pretpostavke

## Šta ti treba instalirati

Instaliraj samo ovo četvoro. Sve ostalo radi kroz Docker.

**Docker Desktop**
Srce svega. Na macOS i Windows dolazi sa Docker Engine, Docker Compose, i GUI za upravljanje kontejnerima. Na Linux instaliraj Docker Engine + Docker Compose plugin.
→ https://www.docker.com/products/docker-desktop

**kind** (Kubernetes IN Docker)
Lokalni Kubernetes koji radi unutar Docker kontejnera. Nema VM, nema cloud troška.
```bash
# macOS
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind && mv ./kind /usr/local/bin/kind
```

**VS Code**
Editor. Sa ekstenzijama: Docker, Kubernetes, GitLab Workflow, YAML.

**Nalozi**
- GitLab nalog (gitlab.com) — besplatan tier je dovoljan
- AWS nalog — koristiš Free Tier gde možeš, ali EKS košta. Očekuj ~$5-15/dan dok cluster radi.

## Znanje koje se pretpostavlja

Ovaj path nije za početnike u programiranju. Pretpostavljamo:

- Znaš šta je terminal i ne plašiš ga se
- Razumeš osnove Linux komandi: `ls`, `cd`, `cat`, `grep`, `curl`
- Znaš šta je git i koristiš ga svakodnevno (`clone`, `push`, `pull`, `branch`, `merge`)
- Razumeš šta je HTTP — request, response, status kodovi (200, 404, 500)
- Čitao si YAML i nisi se onesvijestio

Ne trebaš znati K8s, Terraform, Helm, ili CI/CD. To se uči ovde.

## Docker kao alat za pokretanje alata

Ovo je jedan od ključnih principa patha. Nikad ne instaliraš terraform, kubectl, helm, aws, ili trivy direktno na laptop. Zašto?

Jer version hell postoji. Projekt A radi sa Terraform 1.6, projekt B zahteva 1.9. Instaliraj Docker, pokreni pravu verziju za svaki projekt.

Jer onboarding postaje trivijalan. Novi kolega klonira repo, pokreće `docker run`, radi.

Jer CI pipeline koristi iste Docker image-e. Lokalno i u pipeline-u je identično.

**Terraform**
```bash
# Umesto instalacije terraform CLI:
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7.5 \
  init

docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7.5 \
  plan
```
> **Podman:** `podman run --rm -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7.5 init` (i `plan` — zamijeni zadnji argument)

`--rm` znači: obriši kontejner kad završi. `-v $(pwd):/workspace` montira trenutni folder u kontejner. `-w /workspace` postavlja working directory unutar kontejnera.

**kubectl**
```bash
docker run --rm \
  -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 \
  get pods --all-namespaces
```
> **Podman:** `podman run --rm -v ~/.kube:/root/.kube bitnami/kubectl:1.29 get pods --all-namespaces`

`~/.kube` folder sadrži kubeconfig — credentials za K8s cluster. Montiramo ga u kontejner da kubectl zna kom clusteru da se spoji.

**helm**
```bash
docker run --rm \
  -v $(pwd):/charts \
  -v ~/.kube:/root/.kube \
  -w /charts \
  alpine/helm:3.14 \
  install myapp ./mychart
```
> **Podman:** `podman run --rm -v $(pwd):/charts -v ~/.kube:/root/.kube -w /charts alpine/helm:3.14 install myapp ./mychart`

**Trivy** (security scanner)
```bash
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest \
  image nginx:alpine
```
> **Podman:** `podman run --rm -v /run/user/$(id -u)/podman/podman.sock:/var/run/docker.sock aquasec/trivy:latest image nginx:alpine`

`/var/run/docker.sock` je Unix socket kroz koji Trivy komunicira sa lokalnim Docker daemonom da pristupi image-ovima.

## Shell aliasi koji ti štede vreme

Stavi ovo u `~/.zshrc` ili `~/.bashrc`:

```bash
alias tf='docker run --rm -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7.5'
alias k='docker run --rm -v ~/.kube:/root/.kube bitnami/kubectl:1.29'
alias helm='docker run --rm -v $(pwd):/charts -v ~/.kube:/root/.kube -w /charts alpine/helm:3.14'
```
> **Podman:** `alias tf='podman run --rm -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7.5'` (i analogno za `k` i `helm`)

Posle ovoga: `tf plan`, `k get pods`, `helm install` rade isto kao lokalne instalacije.

## Kako koristiti AI tokom ovog patha

Svaki modul ima "AI workflow" sekcije. Ali evo opštih principa:

**Daj kontekst, ne samo pitanje**

Loše: "Kako da deploajujem na K8s?"

Dobro:
```
Radim na projektu koji deployuje nginx na AWS EKS.
Koristim Helm chart. Imam ovaj error:

Error: INSTALLATION FAILED: cannot re-use a name that is still in use

Komanda: helm install myapp ./charts/myapp -n dev
Šta znači ovaj error i kako da ga rešim?
```

**Copy-paste ceo error, ne samo poruku**

Terminalni output ima kontekst pre i posle poruke o grešci koji Claude treba. Selektuj sve od komande do kraja output-a.

**Traži objašnjenje, ne samo rešenje**

```
Predlažeš da dodam --atomic flag. Objasni šta taj flag radi
i koji su trade-offs pre nego što ga primenimo.
```

**Verifikuj pre primene na produkciji**

```
Evo terraform plan output-a. Šta će se promeniti?
Ima li nešto što bi moglo uticati na produkcijsko okruženje?
[paste plan output]
```

**Kada si zapeo na labovima**

Labovi u ovom pathu su dizajnirani da možeš da ih prođeš sam. Ako zapneš više od 15 minuta, to je signal da nešto ne razumeš konceptualno — ne samo sintaksu. Idi na Claude:

```
Radim lab 01-docker-fundamenti/08-lab. Na ovom koraku:
[opis koraka]
Dobijam:
[error]
Moj Dockerfile izgleda ovako:
[kod]
Objasni šta se dešava.
```

## Priprema okruženja

Pre nego što kreneš sa modulom 01:

```bash
# Provjeri da Docker radi
docker run --rm hello-world

# Provjeri verziju
docker --version
docker compose version

# Provjeri kind
kind version

# Kloniraj ili napravi folder za projekat
mkdir -p ~/projects/project-a
cd ~/projects/project-a
git init
```
> **Podman:** `podman run --rm hello-world`

Ako `docker run hello-world` ne radi, ne nastavljaj dok to ne popravljiš. Sve što dolazi posle zavisi od Dockera.
