# Volumes i networking

## Zašto volumes postoje

Kontejneri su ephemeral — kada nestanu, njihov filesystem nestaje s njima. Ovo je feature, ne bug. Ali ponekad ti treba perzistencija ili deljenje fajlova između hosta i kontejnera.

Tri scenarija:

1. **Development** — menjaš `index.html` na hostu i hoćeš da nginx unutar kontejnera odmah vidi promenu bez rebuild-a image-a
2. **Logovi** — nginx piše logove na disk; hoćeš ih čitati sa hosta ili slati u log agregator
3. **Baze podataka** — PostgreSQL čuva podatke na disku; restart kontejnera ne sme obrisati bazu

## Tri tipa volumes

**Bind mount** — montiraj konkretan folder/fajl sa hosta u kontejner

```bash
docker run -v $(pwd)/app:/usr/share/nginx/html nginx:alpine
#              ↑ host putanja    ↑ putanja u kontejneru
```

> **Podman:** `podman run -v $(pwd)/app:/usr/share/nginx/html nginx:alpine`

Kontejner direktno vidi host filesystem na toj putanji. Promeni fajl na hostu → kontejner odmah vidi promenu. Ovo je osnov live reload u development-u.

Nedostaci: putanja je apsolutna, ne prenosiva između mašina. Kontejner može pisati u host filesystem (sigurnosni rizik ako nije pažljivo postavljen).

**Named volume** — Docker upravlja storage-om, ti znaš samo ime

```bash
docker volume create mydata
docker run -v mydata:/var/lib/mysql mysql:8
```

> **Podman:** `podman volume create mydata` / `podman run -v mydata:/var/lib/mysql mysql:8`

Docker čuva podatke u `/var/lib/docker/volumes/mydata/`. Ti ne znaš niti te briga gde je. Volumepreživljava brisanje kontejnera. Koristiš za podatke koji moraju preživeti restart.

**tmpfs** — u memoriji, ne na disku

```bash
docker run --tmpfs /tmp nginx:alpine
```

> **Podman:** `podman run --tmpfs /tmp nginx:alpine`

Korisno za privremene fajlove, secrets koje ne smeš pisati na disk, ili keševe koji trebaju biti brzi ali ne perzistentni.

## Volumes u development vs produkciji

```
Development (bind mount):
├── brz feedback loop (promeni fajl, odmah vidiš)
├── source code je na hostu, edituje VS Code
└── nema rebuild image-a za svaku promenu

Produkcija (image sadrži sve):
├── image je immutable artifact
├── isti image u dev, staging, prod
└── ne možeš "ručno promeniti fajl na serveru"
```

Ovo razgraničenje je važno. Bind mount u produkciji znači da server filesystem određuje šta aplikacija radi — a ne image koji je prošao testove i pipeline. To je anti-pattern.

## Networking — kako kontejneri komuniciraju

Svaki Docker kontejner po default-u dobija sopstvenu IP adresu unutar Docker network-a.

**Bridge network** (default) — Docker kreira virtualni switch. Kontejneri na istoj bridge mreži mogu međusobno komunicirati. Ne vide host network direktno.

```bash
# Dva kontejnera na default bridge mreži
docker run -d --name nginx1 nginx:alpine
docker run -d --name nginx2 nginx:alpine

# nginx2 može pingati nginx1 ALI po IP adresi, ne po imenu
# Ovo je problem
```

> **Podman:** `podman run -d --name nginx1 nginx:alpine` / `podman run -d --name nginx2 nginx:alpine`

**Custom bridge network** — kreira se ručno, ali ima DNS resolution

```bash
docker network create mynet

docker run -d --name nginx1 --network mynet nginx:alpine
docker run -d --name nginx2 --network mynet nginx:alpine

# Sada nginx2 može se spojiti na nginx1 po imenu!
# http://nginx1/ radi unutar mynet mreže
```

> **Podman:** `podman network create mynet` / `podman run -d --name nginx1 --network mynet nginx:alpine` / `podman run -d --name nginx2 --network mynet nginx:alpine`

Ovo je kako Docker Compose setups rade: kreira custom network, stavlja sve servise na nju, i servisi se referenciraju po nazivu.

**Host network** — kontejner direktno deli network namespace sa hostom

```bash
docker run --network host nginx:alpine
# nginx sluša na host 0.0.0.0:80, bez port mapiranja
```

> **Podman:** `podman run --network host nginx:alpine`

Korisno za performance-critical scenarije, ali gubi izolaciju. Na macOS ne radi (Docker Desktop ima Linux VM u sredini).

**None** — bez mreže

```bash
docker run --network none myapp
# Kontejner nema mrežni pristup
```

> **Podman:** `podman run --network none myapp`

## Container-to-container komunikacija po imenu

Ovo je pattern koji ćeš koristiti stalno:

```yaml
# docker-compose.yml
services:
  frontend:
    image: nginx:alpine
    # može se spojiti na backend po imenu "backend"
  
  backend:
    image: myapp:latest
    # sluša na portu 3000
```

Unutar `frontend` kontejnera: `http://backend:3000` radi. Docker Compose automatski kreira custom network i registruje DNS za sve servise.

Isti princip važi u Kubernetes (modul 03): Services se referenciraju po imenu unutar namespace-a.

## Praktičan primer za project-A

nginx sa bind mount za development (live reload):

```bash
docker run --rm \
  -p 8080:80 \
  -v $(pwd)/app/index.html:/usr/share/nginx/html/index.html:ro \
  nginx:1.25.3-alpine
```

> **Podman:** `podman run --rm -p 8080:80 -v $(pwd)/app/index.html:/usr/share/nginx/html/index.html:ro nginx:1.25.3-alpine`

`:ro` = read-only mount. Kontejner može čitati fajl ali ne može ga pisati. Dobra navika — kontejnerima daješ minimalne potrebne dozvole.

Sada: promeni `app/index.html` na hostu, refresh browser na `http://localhost:8080` — vidiš promenu odmah, bez restart kontejnera.

Za development workflow sa Docker Compose (modul 06) ovo postaje još elegantnije.

## AI workflow

Kada dobiješ permission error na volume mount:

```
Pokrenuo sam:
docker run -v $(pwd)/data:/data myapp

Dobijam:
Permission denied: /data/file.txt

Host folder permissions: drwxr-xr-x darko darko
Kontejner korisnik: appuser (UID 1001)

Objasni zašto se dešava i kako da rešim bez chmod 777.
```
