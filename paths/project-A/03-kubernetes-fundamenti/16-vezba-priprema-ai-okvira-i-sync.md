# 16 — Vežba: priprema AI-okvira i sync (Kubernetes)

Pripremaš AI-okvir za K8s manifeste, pa validiraš deployment na lokalni kind klaster kroz schema validaciju i server-side dry-run.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Odlučujemo da li je potreban K8s-specifičan artefakt u okviru (glob-rule za manifeste), pa K8s manifeste iz prethodnih labova provodimo kroz kubeconform i `kubectl apply --dry-run=server`, i verifikujemo da deployment proradi na kind klasteru.

**Pretpostavke za potvrdu:**
- Postoje K8s manifesti u `k8s/` direktorijumu (iz prethodnih labova oblasti 03)
- `kubectl` je konfigurisan na lokalni kind klaster
- Postoji `CLAUDE.md` u korenu radnog repoa sa `## Project-A workflow` sekcijom

**Van opsega:**
- Ne podešavamo produkcijski klaster — samo lokalni kind
- Ne radimo Helm deployment (to je oblast 04)

**Prompt za diskusiju:**
```
Radim Kubernetes oblast u project-A. Imam K8s manifeste u k8s/
direktorijumu koje treba da proverim. Kontekst je u CLAUDE.md (sekcija ## Project-A workflow). Da li mi treba poseban K8s artefakt (rule za manifeste),
ili je pokriveno? Predloži kao kandidat sa evidencijom i confidence,
bez automatskog kreiranja.
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** K8s manifesti prolaze kubeconform schema validaciju i `kubectl apply --dry-run=server`, deployment proradi i pod je Running.

**Fajlovi koji se diraju:**
- `k8s/*.yaml` (manifesti)
 (ako je odluka „dodaj")

**Fajlovi koji se NE diraju:**
- `Dockerfile` — obrađen u oblasti 01
- `.gitlab-ci.yml` — obrađen u oblasti 02
- Helm chart-ovi — tema oblasti 04

**AI okvir za ovu oblast:**

Dodaj sekciju `## Kubernetes manifest checklist` u `CLAUDE.md`, ili napravi `.claude/rules/k8s-manifest-checks.md`

Sadržaj pravila:
```
- Svaki kontejner ima resources.requests i resources.limits.
- liveness i readiness probe definisani za svaki kontejner.
- Image tag pinovan — ne :latest.
- securityContext: runAsNonRoot: true gde je moguće.
```

Anti-sprawl: K8s se ponavlja kroz module 03, 13 i 22 — minimalan dodatak je opravdan. Ako je pokriveno postojećim pravilima, zapiši odluku i preskoči kreiranje.

**Acceptance criteria:**
- [ ] Odluka o artefaktu doneta i zapisana u `.claude/memory/decisions.md` ili `CLAUDE.md`
- [ ] `kubeconform -strict k8s/` — nula grešaka
- [ ] `kubectl apply --dry-run=server -f k8s/` — prolazi bez grešaka
- [ ] `kubectl rollout status deployment/<ime>` — status `successfully rolled out`
- [ ] Svi kontejneri u manifestima imaju `resources` i probe definisane
- [ ] Sync zapisan u `.claude/memory/decisions.md` ili `CLAUDE.md ## Decision log`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Donosim odluku o k8s-manifest-checks artefaktu
- Pokrećem kubeconform schema validaciju
- Pokrećem kubectl apply --dry-run=server
- Apliciram manifeste i proveravam rollout status

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Schema validacija (offline):

```bash
docker run --rm -v "$PWD":/w ghcr.io/yannh/kubeconform:latest -strict /w/k8s/
```

Server-side dry-run (validira protiv API-ja):

```bash
kubectl apply --dry-run=server -f k8s/
```

Apliciraj manifeste i provjeri rollout:

```bash
kubectl apply -f k8s/
kubectl rollout status deployment/<ime-deployementa>
```

Provjeri da je pod running i servis dostupan:

```bash
kubectl get pods
kubectl get svc
```

Ako `kubectl apply --dry-run=server` prijavi grešku:

```
kubectl apply --dry-run=server daje:
[greška]
Evo manifesta:
[sadržaj]
Šta je pogrešno i koji je minimalan ispravan oblik?
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- kubeconform -strict bez grešaka
- kubectl apply --dry-run=server prolazi
- kubectl rollout status: successfully rolled out
- svi kontejneri imaju resources i probe

Evo outputa:
[ovde lepiš kubeconform output, dry-run output, rollout status output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `docker run --rm -v "$PWD":/w ghcr.io/yannh/kubeconform:latest -strict /w/k8s/` | Nema izlaza (kubeconform ne ispisuje ništa kada su svi manifesti validni) |
| 2 | Pokreni `kubectl apply --dry-run=server -f k8s/` | Shell ispisuje `configured` ili `created` za svaki resurs, bez `Error` linije |
| 3 | Pokreni `kubectl rollout status deployment/<ime>` | Shell ispisuje `deployment "<ime>" successfully rolled out` |
| 4 | Pokreni `kubectl get pods` i provjeri status kolonu | Svi pod-ovi imaju status `Running` i `READY` kolona pokazuje `1/1` |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Kubernetes sync (oblast 03)
- Urađeno: k8s-manifest-checks rule dodat / ili: odlučeno bez dodatka jer ...
- Naučeno: kubeconform + kubectl dry-run kao K8s validacija; resource limits i probe kao obavezni
- Šta bi promenio:
```
