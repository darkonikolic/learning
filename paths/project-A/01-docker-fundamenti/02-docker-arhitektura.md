# Docker arhitektura

## Tri komponente

Docker sistem se sastoji od tri dela koji komuniciraju međusobno:

```
┌──────────────────────────────────────────────────────────┐
│  Tvoj terminal                                           │
│                                                          │
│  $ docker build -t myapp .                               │
│  $ docker run myapp                                      │
│                                                          │
│  Docker CLI (client)                                     │
└────────────────────┬─────────────────────────────────────┘
                     │ REST API (Unix socket ili TCP)
                     │ /var/run/docker.sock
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Docker Daemon (dockerd)                                 │
│                                                          │
│  - Prima komande od CLI                                  │
│  - Gradi image-e                                         │
│  - Pokreće i zaustavlja kontejnere                       │
│  - Upravlja mrežama i volumima                           │
│  - Komunicira sa registry-jem                            │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS (docker pull/push)
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Registry                                                │
│                                                          │
│  Docker Hub: hub.docker.com (nginx:alpine)               │
│  GitLab CR:  registry.gitlab.com/firma/project-a         │
│  AWS ECR:    123456789.dkr.ecr.eu-west-1.amazonaws.com   │
└──────────────────────────────────────────────────────────┘
```

**Docker CLI** — alat kojeg ti koristiš. Ne radi ništa sam. Šalje instrukcije daemonu.

**Docker Daemon** — servis koji radi u pozadini na tvom laptopa (ili serveru). On zapravo gradi image-e i pokreće kontejnere. Komunicira sa kernel-om da postavi namespaces i cgroups.

**Registry** — skladište za Docker image-e. Docker Hub je javni default. GitLab Container Registry je privatni registry koji ćemo koristiti za project-A.

Ova razdvojenost znači da možeš imati Docker CLI na jednoj mašini koji komunicira sa Docker daemonom na drugoj. Na tome se zasniva Docker Context i daljinska administracija.

## Docker socket — kanal komunikacije, ne daemon

Česta zabuna: daemon i socket nisu ista stvar.

```
Docker daemon (dockerd)     → PROCES koji radi u pozadini, upravlja svim
Docker socket               → FAJL kroz koji CLI i daemon razgovaraju
/var/run/docker.sock
```

Analogija: daemon je recepcionar, socket je telefon na recepciji. Telefon nije recepcionar — samo kanal kroz koji ga zoveš.

Kada kucaš `docker run nginx`:

```
CLI otvori /var/run/docker.sock
    │
    ▼
Pošalje HTTP REST zahtjev: POST /containers/create
    │
    ▼
Daemon primi zahtjev → pokrene kontejner → vrati odgovor
```

Komunikacija je REST API over Unix socket — isti protokol kao HTTP, samo umjesto TCP porta koristi fajl na disku.

**Zašto je ovo važno u praksi:**

```yaml
# GitLab CI runner konfiguracija — montira socket u kontejner
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

Ovo znači: kontejner može slati komande Docker daemonu na hostu. Može pokretati nove kontejnere, brisati ih, čitati sve volume-e. Efektivno ima root pristup hostu kroz daemon.

Zato GitLab runner mora biti trusted — nije za javne fork projekte. Alternativa je Docker-in-Docker (`dind`) koji kreira izolirani daemon unutar kontejnera, bez pristupa host daemonu.

> **Podman arhitektura:** Podman nema centralnog daemona. Svaka `podman` komanda direktno komunicira sa container runtimeom (crun/runc) bez posrednika. Ovo je "daemonless" arhitektura — sigurnija jer nema root daemona koji sluša konekcije. Socket (`/run/user/$(id -u)/podman/podman.sock`) postoji samo ako ga eksplicitno pokrneš (`podman system service`). Za korištenje u ovom kursu: `podman build`, `podman run` itd. rade identično kao `docker` ekvivalenti.

## Image layeri — kako Docker skladišti fajlove

Docker image nije jedan monolitni fajl. To je stek read-only slojeva (layera).

Svaka instrukcija u Dockerfilu koja menja filesystem (`FROM`, `RUN`, `COPY`, `ADD`) kreira novi layer.

```
FROM nginx:alpine          → Layer 0: alpine linux base
                             Layer 1: nginx binarni fajlovi
RUN apk add curl           → Layer 2: curl paket
COPY index.html /usr/...   → Layer 3: tvoj fajl
```

Svaki layer je identificiran SHA256 hashom svog sadržaja. Ako dva image-a dele isti layer (isti hash), taj layer se čuva samo jednom na disku.

**Union filesystem (OverlayFS)** je mehanizam koji spaja ove layere u jedinstven pogled na filesystem. Kada kontejner pokreneš, Docker doda jedan read-write layer na vrhu. Sve što kontejner piše ide u taj layer, originalni layeri ostaju nepromijenjeni.

```
┌─────────────────────────────────────┐
│  Container layer (read-write)       │  ← samo dok kontejner živi
├─────────────────────────────────────┤
│  Layer 3: tvoj index.html           │  ← COPY u Dockerfilu
├─────────────────────────────────────┤
│  Layer 2: curl                      │  ← RUN apk add curl
├─────────────────────────────────────┤
│  Layer 1: nginx binaries            │  ← deo nginx:alpine image-a
├─────────────────────────────────────┤
│  Layer 0: alpine linux              │  ← deo nginx:alpine image-a
└─────────────────────────────────────┘
```

**Copy-on-write** — ako kontejner treba da promeni fajl iz read-only layera (npr. edituje nginx.conf iz Layer 1), Docker kopira taj fajl u container layer i tamo ga menja. Originalni layer ostaje nedirnut. Druga kopija kontejnera i dalje vidi original.

Praktična posledica: možeš pokrenuti 100 kontejnera od istog image-a i oni dijele sve read-only layere. Jedina razlika je mali container layer per kontejner.

## Container lifecycle

Kontejner prolazi kroz ova stanja:

```
         docker create
              │
              ▼
         ┌─────────┐
         │ CREATED │  postoji, nije pokrenuto
         └────┬────┘
              │ docker start
              ▼
         ┌─────────┐
    ┌───▶│ RUNNING │◀───┐
    │    └────┬────┘    │
    │         │         │ docker start
    │   docker pause    │
    │         │         │
    │    ┌────▼────┐    │
    │    │ PAUSED  │    │
    │    └────┬────┘    │
    │         │         │
    │   docker unpause  │
    │         │         │
    │    docker stop    │
    │         │         │
    │    ┌────▼────┐    │
    └────│ STOPPED │────┘
         └────┬────┘
              │ docker rm
              ▼
           (gone)
```

> **Podman:** Sve komande iz dijagrama rade identično — zamijeni `docker` sa `podman`: `podman create`, `podman start`, `podman pause`, `podman unpause`, `podman stop`, `podman rm`.

`docker run` = `docker create` + `docker start` u jednoj komandi.

> **Podman:** `podman run` = `podman create` + `podman start`

Ono što ovo znači za nas: RUNNING kontejner = RUNNING proces unutar kontejnera. Kada nginx proces unutar kontejnera pukne ili se zaustavi, kontejner prelazi u STOPPED. Kubernetes to detektuje i restartuje pod. Monitoring mora pratiti ovo stanje.

## Tok kroz ceo sistem

Vizualizacija kompletnog toka koji ćemo proći u project-A:

```
1. DOCKER BUILD
   Dockerfile → Docker daemon → gradi layere → lokalni image
   
   $ docker build -t helloworld:local .

2. DOCKER TAG
   Dodaj registry prefiks image-u
   
   $ docker tag helloworld:local \
     registry.gitlab.com/firma/project-a:abc123

3. DOCKER PUSH
   Lokalni image → GitLab Container Registry
   
   $ docker push registry.gitlab.com/firma/project-a:abc123

4. DOCKER PULL (na EKS nodeu, K8s to radi automatski)
   GitLab Registry → EKS node → lokalni image na nodu
   
   kubelet automatski: docker pull registry.gitlab.com/...

5. DOCKER RUN (K8s pokreće kontejner iz image-a)
   image → running container = running nginx process
```

> **Podman:**
> ```bash
> podman build -t helloworld:local .
> podman tag helloworld:local registry.gitlab.com/firma/project-a:abc123
> podman push registry.gitlab.com/firma/project-a:abc123
> podman pull registry.gitlab.com/...
> podman run helloworld:local
> ```

Ovaj tok se automatizuje u GitLab CI/CD pipeline-u. Svaki `git push` pokreće sve ove korake bez ručne intervencije.

## Zašto to razumeti

Kada pipeline fail-uje sa "manifest unknown" na docker pull koraku, znaš: image nije pushnut u registry, ili push/pull credentials nisu ispravni. Kada kontejner pada u CrashLoopBackOff, znaš: proces unutar kontejnera se gasi — gledaj logove, ne K8s konfiguraciju.

Arhitektura objašnjava gde tražiti problem.
