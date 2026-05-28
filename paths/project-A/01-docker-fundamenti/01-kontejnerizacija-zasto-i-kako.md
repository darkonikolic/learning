# Kontejnerizacija — zašto i kako

## Problem koji je postojao pre Dockera

2013. godina. Developer napiše Python web app. Radi savršeno na laptopa. Pošalje kolegi. Ne radi. "Radi na mom računaru" postaje vic koji nije smiješan.

Zašto se to dešava? Aplikacija zavisi od:
- Verzije Python interpretera (3.9 vs 3.11 — breaking changes)
- Instaliranih Python paketa i njihovih verzija
- Sistemskih biblioteka (libssl, libpq...)
- Environment varijabli
- Operativnog sistema (Ubuntu 20.04 vs macOS 14)
- Fajl sistema i putanja

Svaki od ovih faktora može uzrokovati da aplikacija radi na jednoj mašini a ne na drugoj. Klasična rešenja su bila:

**Dokumentacija** — "Instaliraj Python 3.9, onda pip install -r requirements.txt, onda..." Ručno, error-prone, zastarijeva.

**Virtuelne mašine** — pakovana cela OS. Radi ali je teška: 2-10 GB po VM, minutes to boot, ogromna potrošnja resursa.

## VM vs kontejner

```
Virtuelna mašina                    Kontejner
┌─────────────────────┐             ┌─────────────────────┐
│  App A              │             │  App A              │
├─────────────────────┤             ├─────────────────────┤
│  Guest OS (Ubuntu)  │             │  Libs, bins, config │
│  (2GB+)             │             │  (MB-niveau)        │
├─────────────────────┤             ├─────────────────────┤
│  Hypervisor         │             │  Container Runtime  │
│  (VMware/KVM/HyperV)│             │  (Docker/containerd)│
├─────────────────────┤             ├─────────────────────┤
│  Host OS            │             │  Host OS            │
├─────────────────────┤             ├─────────────────────┤
│  Hardware           │             │  Hardware           │
└─────────────────────┘             └─────────────────────┘
```

Kontejner ne simulira hardware. Ne pokreće sopstveni kernel. Deli kernel sa host OS-om.

Umesto toga, koristi dve Linux kernel funkcionalnosti:

**namespaces** — izolacija. Svaki kontejner vidi sopstveni filesystem, mrežu, procese, korisnike. Ne zna za ostale kontejnere (osim ako im dozvoliš komunikaciju).

**cgroups** (control groups) — ograničenje resursa. Ovom kontejneru možeš reći: ne smeš koristiti više od 256MB RAM-a i 0.5 CPU core-a.

Rezultat:

| | VM | Kontejner |
|---|---|---|
| Veličina | GB | MB |
| Boot time | minute | sekunde (millisekunde) |
| Izolacija | kompletan OS | namespace/cgroups |
| Pokretljivost | teška | trivijalna |
| Overhead | visok | minimalan |

## OCI standard

Open Container Initiative definiše šta je container image i kako se pokreće. To znači da image napravljen sa Docker build-om može pokrenuti containerd, podman, cri-o, ili bilo koji OCI-kompatibilan runtime.

Zbog toga: image koji napravimo i gurnemo u GitLab registry, Kubernetes može pokrenuti bez obzira koji container runtime koristi u pozadini.

Praktično za nas: `docker build` → GitLab Registry → EKS (containerd). Kompatibilnost je garantovana standardom.

## Šta kontejner zapravo jeste

Kontejner nije magija. To je Linux proces (ili više procesa) koji:

1. Vidi sopstveni "root filesystem" koji je zapravo slaganje read-only slojeva (image layers) + jedan read-write sloj na vrhu
2. Ima sopstveni network namespace (vlastita IP adresa, vlastiti port space)
3. Ima ograničene resurse (ako postaviš limits)
4. Ako ga ubiješ, read-write sloj (sve što je pisano tokom rada) nestaje

Ova poslednja stavka je kritična: **kontejneri su ephemeral**. Ono što piše na disk unutar kontejnera — nestaje kada kontejner nestane. Zato postoje volumes (modul 05).

## Zašto kontejnerizujemo nginx u project-A

nginx je web server koji servira naš `index.html`. Mogli bismo instalirati nginx direktno na server. Zašto ne?

Jer jednom kad nginx živí u kontejneru:

```
docker run -p 8080:80 registry.gitlab.com/firma/project-a:sha-abc123
```

Ova jedna komanda radi identično na:
- Laptopa u development-u
- kind clusteru lokalno
- AWS EKS dev okruženju
- AWS EKS produkciji

Nema "nginx konfiguracija je drugačija u produkciji". Nema "verzija nginx-a na serveru je starija". Image koji je prošao testove je tačno isti image koji ide u prod. To je vrednost kontejnerizacije u jednoj rečenici.

Pored toga, kada treba skalirati, K8s pokreće 10 identičnih kopija istog image-a. Kada treba da unapredimo nginx, promenimo `FROM nginx:1.25.3-alpine` u Dockerfilu, pokrenemo pipeline, dobijemo novi image.

## Šta dolazi sledeće

Razumeš zašto kontejnerizujemo. Sledeće je kako: arhitektura Docker sistema koji to omogućava.
