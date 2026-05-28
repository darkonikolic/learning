# 01 — Arhitektura i odluke

## Zašto ovaj stack postoji

Ovo nije stack koji se bira bez razloga. Svaki servis pokriva konkretan problem koji drugi servis ne može riješiti jednako dobro. Mješavina tehnologija ima cijenu — distribuirani sistem uvodi network failure, eventual consistency i operativnu kompleksnost. Taj tradeoff se prihvata svjesno.

---

## PHP kao proxy sloj

PHP servis sjedi između nginx-a i Go servisa. Nije ovdje jer je "legacy" — ovdje je jer rješava tri problema koje ne bi trebalo gurnuti u Go:

**Session handling**: PHP ima zreliji ekosistem za session management uz Redis. `php-redis` extenzija, `session.gc_maxlifetime`, session fixation zaštita — sve je izgrađeno i testirano godinama. Reimplementirati to u Go je moguće, ali nema razloga.

**Legacy compatibility**: Ako projekat ima historiju, PHP dio može apsorbovati stari kod koji nije vrijedan refaktoringa. Go servis ostaje čist.

**Rate limiting centralizovano**: Slim middleware može interceptovati sve /api/ pozive prije nego stignu do Go servisa. Rate limit logika je u jednom mjestu, ne duplicirana u svakom endpointu.

Što PHP NIJE: PHP nije business logic. Ne radi kalkulacije, ne procesira domenske entitete, ne komunicira direktno sa MySQL-om za podatke. To je Go-ov posao.

---

## Go za business logic

Go je izabran zbog tri konkretne karakteristike:

**Type safety na runtime-u**: Kompilacija hvata greške koje PHP otkriva tek u produkciji. Za domenski kritičan kod (finansijske kalkulacije, stanje korisničkih account-a) to nije luxuz.

**Performance i memory footprint**: Go servis troši 20-50MB RAM-a pod opterećenjem. Ekvivalentni PHP FPM pool za isti broj concurrent zahtjeva treba 200-500MB. Na K8s-u to direktno utiče na troškove.

**Goroutines za async processing**: Kada endpoint mora napraviti 3 database querija koji nisu međuzavisni, Go ih radi paralelno bez callback pakla. `sync.WaitGroup` ili `errgroup` — 10 linija koda, stvarno paralelno izvršavanje.

Go servis komunicira sa MySQL-om direktno i sa Redis-om direktno. PHP ga poziva samo putem HTTP.

---

## Vue.js SPA pattern

Vue.js je decoupled od svakog backenda. Build artefakt je statički HTML/CSS/JS koji ne zna ništa o PHP-u ili Go-u. Sva komunikacija ide kroz `/api/` prefix koji nginx proksira na PHP servis.

Ovo omogućava:
- Frontend tim radi nezavisno, može koristiti mock API
- Build pipeline je čist Node.js, bez PHP ili Go zavisnosti
- CDN serviranje statičnih asseta bez promjena (hashed filenames)

SPA routing zahtijeva nginx `try_files` konfiguraciju — svaki URL koji ne postoji kao fajl mora vratiti `index.html`. Ovo je jedina nginx-specifična stvar koju Vue.js zahtijeva.

---

## MySQL master/replica

Jedan MySQL server je single point of failure i bottleneck za read-heavy aplikacije. Master/replica daje:

**Write isolation**: Svi `INSERT/UPDATE/DELETE` idu na master. Aplikacija eksplicitno bira konekciju — ne "automatski" routing koji može iznenaditi.

**Read scaling**: `SELECT` queriji za reporting, listing, pretragu — idu na repliku. Master je slobodan za write operacije.

**Replication lag awareness**: Ovo je kritičan tradeoff koji se mora razumjeti. Replikacija je asinhrana. Nakon `INSERT` na masteru, podatak možda nije dostupan na replici narednih 10-100ms. Aplikacijski kod mora ovo znati:

```go
// Nakon write operacije, read mora ići na master, NE repliku
func (s *UserService) CreateUser(ctx context.Context, user User) error {
    err := s.masterDB.CreateUser(ctx, user)
    if err != nil {
        return err
    }
    // Ovo mora ići na master ili čekati replikaciju
    return s.sendWelcomeEmail(ctx, user, s.masterDB)
}
```

Pattern za rješavanje replication lag-a: "read-your-own-writes" — korisnik koji je upravo napravio izmjenu dobija response sa master podataka narednih N sekundi (session flag ili version-based routing).

---

## Redis — session storage, ne JWT

Ovo je svjesna arhitekturalna odluka koja se mora objasniti.

**Zašto ne JWT stateless**: JWT stateless token ne može biti invalidiran prije expiry-ja. Ako korisnik odjavi nalog, ili admin forcefully logout-a korisnika, JWT token ostaje validan do isteka. Za aplikacije koje imaju "logout all sessions" ili security revocation zahtjev, JWT stateless je pogrešan izbor.

Redis session storage omogućava:
- Trenutni logout (brisanje session key-a iz Redis-a)
- "Logout all devices" (brisanje svih session key-ova za korisnika)
- Session inspection (admin može vidjeti aktivne session-e)
- TTL automatski handles expiry

**Cache invalidation strategija**: Redis se koristi i za application cache. Strategija je "cache-aside" (lazy loading):

```
1. App traži podatak iz Redis-a
2. Cache miss → upit na MySQL repliku → spremi u Redis sa TTL
3. Cache hit → vrati direktno
4. Na write operaciji → explicitno invalidirati cache key
```

Ne koristiti "write-through" (pisati u Redis i MySQL istovremeno) — previše kompleksnosti za ovaj nivo, i write operacije su generalno rjeđe od read-a.

---

## Service communication: zašto HTTP/JSON, ne gRPC

gRPC je izvrstan protokol. Za ovaj stack je overkill iz konkretnih razloga:

- **Tooling overhead**: gRPC zahtijeva protobuf definicije, code generation, versioning contract. HTTP/JSON radi sa `curl` i browser devtools-ima.
- **PHP gRPC klijent**: `grpc` PHP ekstenzija je komplikovanija za setup od standardnog HTTP klijenta.
- **Latency**: Interna mreža (Docker/K8s) ima latency ispod 1ms. gRPC prednost nad HTTP/JSON dolazi do izražaja na WAN-u ili pri ekstremno visokom throughput-u.

Communication matrix:

```
nginx (80/443) → PHP FPM (9000, FastCGI/TCP)
nginx (80/443) → Vue.js static files (u nginx image-u, direktno)
PHP service    → Go service (8080, HTTP/JSON)
PHP service    → Redis (6379, Redis protocol)
Go service     → MySQL master (3306, MySQL protocol)
Go service     → MySQL replica (3307, MySQL protocol)
Go service     → Redis (6379, Redis protocol)
```

---

## Kada ovaj stack ima smisla

Ovaj stack je opravdan kada:

1. Tim je podijeljen po tehnologiji (PHP devovi, Go devovi, frontend devovi rade nezavisno)
2. Read/write ratio je visok (>80% read) — read scaling je kritičan
3. Session revocation je funkcionalni zahtjev
4. Business logic ima performance zahtjeve koji PHP ne može ispuniti (CPU-bound operacije)
5. Aplikacija će rasti — horizontalno skaliranje po servisu ima smisla

**Kada ovo nije dobra ideja**: Startup sa jednim developerom, interna alat aplikacija, proof of concept. Monolith (Laravel ili Go monolith) je brži za razvoj i lakši za debugovanje. Distribuirani sistem uvodi network debugging, distributed tracing potrebu, kompleksnost deployments-a. Cijena mora biti opravdana.
