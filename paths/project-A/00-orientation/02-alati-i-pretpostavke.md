# Alati i pretpostavke

## Šta ti treba instalirati

Instaliraj samo ovo dvoje. Sve ostalo se nikad ne instalira — pokreće se iz kontejner imagea kad zatreba.

> Claude Code CLI je pretpostavka — ako čitaš ovo kroz Claude, već je instaliran.

**Podman** (ili Docker)
Container runtime — srce svega. Biraš jedno od dva:

```bash
# Podman (preporučeno — daemonless, rootless, ne treba root)
brew install podman
podman machine init
podman machine start

# Docker Desktop (alternativa — GUI, lakši onboarding na macOS/Windows)
# https://www.docker.com/products/docker-desktop
```

Oba su API-kompatibilna. Makefile u projektu podržava oba — promijeniš jednu varijablu na vrhu i sve radi.

**kind** (Kubernetes IN Docker/Podman)
Jedini alat koji mora biti lokalni binarni fajl pored container runtime-a. Razlog: kind direktno poziva Podman/Docker daemon da bi kreirao cluster node kontejnere — ne može sam sebe pokrenuti iznutra.

Kubernetes koji kind kreira (API server, etcd, worker nodovi) — sve su to Podman/Docker kontejneri. Ali sam `kind` CLI mora biti lokalan.

```bash
# macOS
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind && mv ./kind /usr/local/bin/kind
```

---

## Šta se NIKAD ne instalira

Sve ostalo pokrećeš iz kontejner imagea. Makefile u projektu sadrži targete za svaki alat:

| Alat | Komanda | Instalacija |
|------|---------|-------------|
| kubectl | `make pods`, `make k-apply` | ❌ nije potrebna |
| helm | `make helm-install`, `make helm-lint` | ❌ nije potrebna |
| terraform | `make tf-plan`, `make tf-apply` | ❌ nije potrebna |
| aws CLI | `make aws-whoami` | ❌ nije potrebna |
| trivy | `make trivy-scan` | ❌ nije potrebna |
| tfsec | `make tf-security` | ❌ nije potrebna |
| hadolint | `make hadolint` | ❌ nije potrebna |
| mysql client | `make db-dump` | ❌ nije potrebna |
| k6 | `make perf-test` | ❌ nije potrebna |

Zašto? Jer svaki `make` target pokreće odgovarajući image sa pinovanom verzijom, izvršava komandu, i briše kontejner. Nema version hell-a, nema "radi na mom laptopu", nema onboarding problema.

---

**Nalozi**
- GitLab nalog (gitlab.com) — besplatan tier je dovoljan
- AWS nalog — koristiš Free Tier gdje možeš, ali EKS košta. Očekuj ~$5-15/dan dok cluster radi.

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

## Makefile — jedino mjesto za sve komande

Umjesto shell aliasa, projekat koristi jedan centralni `Makefile` koji raste zajedno s poglavljima. Prednost: radi u svakom shellu, ide u git, vidljiv svim članovima tima, i `make help` je instant dokumentacija.

```bash
# Prikaži sve dostupne komande sa objašnjenjima
make help
```

`make help` parsira `## komentar` na svakom targetu i ispisuje uređenu tabelu. Nema potrebe pamtiti komande — `make help` je uvijek tačna lista.

**Princip rasta:** Makefile počinje sa Docker targetima u oblasti 01. Svaka nova oblast dodaje svoje targete. Na kraju patha, `make help` prikazuje kompletan DevOps toolbox projekta.

**Prosleđivanje varijabli:** Targeti koji trebaju parametre koriste make varijable:
```bash
ENV=dev make infra-plan      # terraform plan za dev okruženje
FILE=deployment.yaml make k-apply  # kubectl apply specifičnog fajla
IMAGE=nginx:alpine make trivy-image  # trivy skeniranje specifičnog imagea
```

**AWS credentials:** Nikad u Makefile-u. Exportuj ih u terminalu, Makefile ih prenosi automatski:
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
make aws-whoami  # koristi exportovane varijable
```

## Kako koristiti Claude Code tokom ovog patha

Svaki modul ima "AI workflow" sekcije. Claude Code je CLI alat koji radi direktno u terminalu — ima pristup shellu, fajlovima i može izvršavati komande. Evo ključnih koncepata:

**CLAUDE.md — memorija projekta**

Na početku svakog radnog repoa kreiraj `CLAUDE.md`. Ovaj fajl Claude automatski učitava pri svakom pokretanju i daje mu kontekst o projektu:

```bash
# Inicijalizuj CLAUDE.md u korenu repoa
claude /init
```

Zatim edituj fajl i dodaj sekciju `## Project-A workflow` sa pravilima koja Claude treba da poštuje (plan→egzekucija→validacija petlja, DevOps checklist-e, itd.).

**`/plan` — plan pre izmena**

Pre svake izmene infrastrukture ili koda, kucaj `/plan` u Claude Code terminalu. Claude će predložiti plan i čekati tvoje odobrenje pre izvršavanja. Ovo je posebno bitno za Terraform (`terraform apply`) i Kubernetes deploy operacije.

```
# U Claude Code terminalu:
/plan
```

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

**Hooks — automatska validacija**

U `.claude/settings.json` možeš podesiti hooks koji se automatski izvršavaju pre ili posle određenih tool call-ova. Na primjer, hook koji pokreće `terraform validate` pre svakog `terraform apply`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "echo 'Provjeri plan pre apply!'"}]
      }
    ]
  }
}
```

**Kada si zapeo na labovima**

Labovi u ovom pathu su dizajnirani da možeš da ih prođeš sam. Ako zapneš više od 15 minuta, to je signal da nešto ne razumeš konceptualno — ne samo sintaksu. Pokreni `claude` u terminalu i pitaj:

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
