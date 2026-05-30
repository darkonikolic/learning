# 07 — Vežba: priprema AI-okvira i sync (Helm)

Pripremaš AI-okvir za Helm chart-ove, pa validiraš `helloworld` chart iz ove oblasti kroz `helm lint` i template rendering po okruženjima.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Odlučujemo da li je potreban Helm-specifičan artefakt u okviru (dopuna k8s-manifest-checks ili zaseban rule za chart templates), pa `helloworld` chart provodimo kroz `helm lint` i `helm template` i verifikujemo da se renderuje ispravno za dev i prod okruženja.

**Pretpostavke za potvrdu:**
- Postoji `helloworld/` Helm chart sa `values/dev.yaml` i `values/prod.yaml` (iz prethodnih labova oblasti 04)
- `helm` CLI je instalisan
- Postoji `CLAUDE.md` u korenu radnog repoa sa `## Project-A workflow` sekcijom

**Van opsega:**
- Ne deployujemo na produkciju — samo lokalna validacija
- Ne menjamo K8s manifeste direktno — sve ide kroz Helm template

**Prompt za diskusiju:**
```
Radim Helm oblast u project-A. Imam helloworld chart sa values/dev.yaml
i values/prod.yaml. Kontekst je u CLAUDE.md (sekcija ## Project-A workflow i
## Kubernetes manifest checklist). Da li da proširim k8s-manifest-checks sekciju
na Helm templates, ili da dodam zaseban .claude/rules/ fajl? Predloži kao kandidat
sa evidencijom i confidence, bez automatskog kreiranja.
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** `helloworld` chart prolazi `helm lint` i `helm template` renderuje validne manifeste za dev i prod, bez hardkodovanih vrednosti u template-ima.

**Fajlovi koji se diraju:**
- `helloworld/templates/*.yaml`
- `helloworld/values/dev.yaml`
- `helloworld/values/prod.yaml`
- `helloworld/_helpers.tpl`
- `CLAUDE.md` ili `.claude/rules/helm-chart-checks.md` (ako je odluka „dodaj")

**Fajlovi koji se NE diraju:**
- `k8s/` direktni manifesti — obrađeni u oblasti 03
- Aplikacijski kod

**AI okvir za ovu oblast:**

Dodaj sekciju `## Helm chart checklist` u `CLAUDE.md`, ili napravi `.claude/rules/helm-chart-checks.md`

Sadržaj pravila:
```
- Vrednosti dolaze iz values/<env>.yaml — ne hardkodovane u template.
- Svaki resurs koristi {{ include "...labels" . }} iz _helpers.tpl.
- resources i probe parametrizovani po okruženju (različite vrednosti u dev vs prod).
```

Anti-sprawl: Helm se ponavlja kroz module 04, 13 i 22 — minimalan dodatak je opravdan. Ako `k8s-manifest-checks` već pokriva potrebu, dopuni ga umesto kreiranja novog fajla.

**Acceptance criteria:**
- [ ] Odluka o artefaktu doneta i zapisana u `.claude/memory/decisions.md` ili `CLAUDE.md`
- [ ] `helm lint helloworld -f helloworld/values/dev.yaml` — nula grešaka
- [ ] `helm template helloworld -f helloworld/values/prod.yaml` — renderuje bez grešaka
- [ ] `helm template ... | grep "image:"` prikazuje pinovan tag (ne `:latest`)
- [ ] `grep -r "hardcoded\|localhost\|password" helloworld/templates/` — nema plaintext vrednosti
- [ ] Sync zapisan u `.claude/memory/decisions.md` ili `CLAUDE.md ## Decision log`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Donosim odluku o Helm artefaktu (dopuna ili novi rule)
- Pokrećem helm lint za dev okruženje
- Pokrećem helm template za prod okruženje
- Proveravam image tag i odsustvo hardkodovanih vrednosti

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Lint chart-a za dev okruženje:

```bash
helm lint helloworld -f helloworld/values/dev.yaml
```

Template rendering za prod okruženje (bez deploymenta):

```bash
helm template helloworld -f helloworld/values/prod.yaml
```

Template rendering i server-side dry-run zajedno:

```bash
helm template helloworld -f helloworld/values/prod.yaml | kubectl apply --dry-run=server -f -
```

Provjeri da je image tag pinovan u rendered output-u:

```bash
helm template helloworld -f helloworld/values/dev.yaml | grep "image:"
```

Ako lint prijavi grešku:

```
helm lint prijavljuje:
[greška]
Evo template-a i values:
[sadržaj]
Koja vrednost nedostaje i kako da je parametrizujem po okruženju?
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- helm lint bez grešaka za dev okruženje
- helm template za prod renderuje bez grešaka
- image tag je pinovan (ne :latest)
- nema hardkodovanih vrednosti u templates

Evo outputa:
[ovde lepiš helm lint output, helm template output, grep image output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `helm lint helloworld -f helloworld/values/dev.yaml` | Shell ispisuje `1 chart(s) linted, 0 chart(s) failed` |
| 2 | Pokreni `helm template helloworld -f helloworld/values/prod.yaml \| grep "image:"` | Izlaz prikazuje image sa pinovanim tagom (npr. `nginx:1.25.3-alpine`), ne `:latest` |
| 3 | Pokreni `helm template helloworld -f helloworld/values/prod.yaml \| kubectl apply --dry-run=server -f -` | Shell ispisuje `configured` ili `created` za svaki resurs, bez `Error` linije |
| 4 | Otvori `helloworld/templates/deployment.yaml` i pretraži sadržaj | Nema hardkodovanih IP adresa, lozinki niti environment-specifičnih vrednosti — sve referencira `{{ .Values.* }}` |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Helm sync (oblast 04)
- Urađeno: helm-chart-checks rule dodat / ili: k8s-manifest-checks dopunjen za Helm
- Naučeno: helm lint + helm template kao Helm validacija; values po okruženju kao obavezan obrazac
- Šta bi promenio:
```
