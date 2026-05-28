# Lab 02 — Workflow disciplina: GET /tasks endpoint

## Cilj
Na kraju ovog laba imaš implementiran GET /tasks endpoint uz primijenjenu /plan → execute disciplinu, koristio/la si /compact svjesno, i možeš objasniti zašto svaki prompt koji si napisao/la jest ili nije bio dovoljno konkretan.

## Preduvjeti
- Lab 01 završen: `task-api` projekat postoji, `go build ./...` prolazi
- POST /tasks endpoint radi i vraća 201
- CLAUDE.md postoji u `task-api/` direktorijumu
- `.claude/settings.json` postoji s allow/deny pravilima

## Kontekst
Lab 01 ti je dao strukturu projekta i POST endpoint. Sada koristiš disciplinirani workflow: pišeš CLAUDE.md kao prvi kontekst sesije, koristiš /plan before execution, i svjesno upravljaš kontekstom s /compact. Cilj nije samo napraviti GET endpoint — cilj je naučiti KAKO raditi, ne samo ŠTA.

## Koraci

### Korak 1 — Pripremi se PRIJE otvaranja Claude sesije

Ovo je thinking mode — radi sam/sama, bez Claude-a.

U `task-api/` napravi fajl `docs/plans/02-get-tasks-context.md`:

```bash
mkdir -p docs/plans
```

Sadržaj (popuni sve `[fill in]` dijelove):

```markdown
## Cilj
Implementirati GET /tasks endpoint koji vraća sve taskove iz in-memory store-a.

## Problem koji rješavamo
API korisnici ne mogu dohvatiti taskove nakon što ih kreiraju — POST /tasks postoji,
ali GET /tasks ne postoji, pa je API nepotpun.

## Relevant files
- tasks/handler.go — dodati GetTasks handler ovdje
- tasks/store.go — dodati List() metodu ovdje
- main.go — registrovati rutu ovdje

## Acceptance criteria (NAPIŠI OVE SAM/SAMA)
- [ ] GET /tasks s praznim store-om vraća 200 i tijelo []
- [ ] GET /tasks nakon 2 POST-a vraća niz dužine 2
- [ ] Taskovi u odgovoru su u redoslijedu kreiranja (prvi kreiran = index 0)
- [ ] Svaki task u odgovoru ima: id, title, completed, created_at
- [ ] Response Content-Type je application/json

## Out of scope
- Paginacija
- Filtriranje ili sortiranje
- Autentikacija
```

**Uradi ovo:**
Popuni fajl i provjeri: da li su tvoji acceptance criteria konkretni? Možeš li verificirati svaki s `curl` komandom? Ako ne — prepiši.

---

### Korak 2 — Otvori sesiju s CLAUDE.md kao prvim kontekstom

Navigiraj u `task-api/` i pokreni Claude Code:

```bash
claude
```

Kada se otvori sesija, ODMAH pošalji:

```
I'm starting a new session. Please read CLAUDE.md to understand the project context.

Also read docs/plans/02-get-tasks-context.md for the context of this task.

Confirm: what are the constraints for this project, and what is the goal of this session?
```

**Očekivani output:**
Claude odgovara navodeći constraints iz CLAUDE.md (no external packages, JSON errors, itd.) i goal iz context fajla. Ako ne može pročitati fajlove — provjeri da si u pravom direktorijumu.

Ovo je važno: **nikad ne počinjaš implementaciju bez da Claude potvrdi da razumije kontekst.**

---

### Korak 3 — Koristi /plan za planiranje GET /tasks

Sada kada je Claude upoznat s projektom, pokreni plan mode:

```
/plan Implement GET /tasks endpoint — no implementation yet.
Read: tasks/handler.go, tasks/store.go, main.go
Goal: implement based on docs/plans/02-get-tasks-context.md
Constraints: stdlib only, no external packages
Files to modify: tasks/handler.go, tasks/store.go, main.go
```

**Očekivani output:**
Claude predlaže plan u plan modu — nabrajanje koraka bez pisanja koda. Plan treba sadržavati redoslijed: (1) store.List() metoda, (2) GetTasks handler, (3) registracija rute u main.go.

**Provjeri plan:**
- Je li redoslijed ispravan? Store MORA biti implementiran PRIJE handlera.
- Da li plan pominje external packages? Ne smije.
- Da li svaki korak ima specifičan fajl? Ako piše "update store" bez fajla — zatraži reviziju.

Ako plan nije ispravan, pošalji:

```
Revise the plan:
- Step 1 must name the specific file: tasks/store.go
- Store List() must come before handler implementation
- No external packages in any step
```

---

### Korak 4 — Izvrši implementaciju bounded messageom

Nakon što si odobrio/la plan, izvrši implementaciju:

```
Execute the GET /tasks plan.
Files to modify: tasks/handler.go, tasks/store.go, main.go
Do not add any behavior not in the plan.
After implementation, run: go build ./...
```

**Očekivani output:**
Claude implementira List() metodu u store.go, GetTasks handler u handler.go, registrira rutu u main.go, i pokreće `go build ./...`. Build treba proći.

Pazi na scope creep — ako Claude doda nešto što nije u planu (npr. filtriranje, paginaciju), odmah zaustavi:

```
Stop. You've gone beyond the plan. Revert the filtering addition — it's not in scope.
```

---

### Korak 5 — Svjesno upravljanje kontekstom s /compact

Provjeri koliko je kontekst popunjen:

```
/context
```

Zabilježi postotak. Sada napravi nekoliko dodatnih upita (npr. postavi pitanja o kodu), pa opet provjeri.

Kad kontekst pređe 50%, pokreni compact **ali samo nakon što si zapisao/la plan na disk**:

```
/compact
```

Nakon compact, odmah provjeri da Claude još uvijek pamti projekt:

```
What are the project constraints? What endpoint did we just implement?
```

**Očekivani output:**
Claude treba moći odgovoriti na oba pitanja jer su odgovori u CLAUDE.md koji preživljava compact. Ako ne može — CLAUDE.md nije učitan ispravno ili je premali.

---

### Korak 6 — Prompt repair vježba

Ovo je namjerna vježba: napiši loš prompt, pa ga ispravi.

**Iteracija 1 — loš prompt:**

```
add endpoint
```

Pogledaj šta Claude radi s ovim. (Nemoj odobriti nikakve izmjene.)

**Iteracija 2 — bolji prompt:**

```
add GET /tasks endpoint that returns all tasks
```

Usporedi s prethodnim. Bolji, ali i dalje neprecizno.

**Iteracija 3 — konkretan prompt:**

```
Implement GET /tasks handler in tasks/handler.go.
The handler must:
- Call store.List() to get all tasks
- Return 200 with JSON array of all tasks
- Return [] (not null) when no tasks exist
- Set Content-Type: application/json
Do not modify main.go or store.go in this step.
Run go build ./... after implementation.
```

**Uradi ovo:**
Pokreni treći prompt. Provjeri da li je implementacija ispravna. Odgovori sebi: zašto je treći prompt bio najefikasniji?

---

### Korak 7 — Verifikacija endpointa

Pokreni server:

```bash
go run main.go
```

U drugom terminalu, verificiraj acceptance criteria iz tvog context fajla:

```bash
# Criterion 1: prazan store vraca []
curl -s http://localhost:8080/tasks
# Ocekivano: []

# Criterion 2: status 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/tasks
# Ocekivano: 200

# Criterion 3: duzina niza nakon 2 POST-a
curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"alpha"}'

curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"beta"}'

curl -s http://localhost:8080/tasks | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))"
# Ocekivano: 2

# Criterion 4: redoslijed kreiranja (alpha mora biti na index 0)
curl -s http://localhost:8080/tasks | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['title'])"
# Ocekivano: alpha

# Criterion 5: Content-Type header
curl -sI http://localhost:8080/tasks | grep -i content-type
# Ocekivano: application/json
```

Za svaki FAIL: vrati se u Claude sesiju s konkretnim opisom greške (template iz teorije):

```
Flaw: GET /tasks returns null instead of []
Location: tasks/store.go, List() method
Expected: return make([]Task, 0) not nil slice — nil serializes to null in JSON
```

---

### Korak 8 — Commituj

```bash
git add tasks/handler.go tasks/store.go main.go docs/plans/
git commit -m "feat: implement GET /tasks endpoint with in-memory list"
```

## Verifikacija

- [ ] `curl -s http://localhost:8080/tasks` vraća `[]` kad nema taskova (ne `null`, ne `404`)
- [ ] `curl -s http://localhost:8080/tasks` vraća niz dužine 2 nakon dva POST-a
- [ ] Taskovi su u redoslijedu kreiranja (stariji task je na index 0)
- [ ] Svaki task ima: id, title, completed, created_at polja
- [ ] Koristio/la si `/compact` barem jednom i Claude je nastavio rad
- [ ] Možeš objasniti zašto je treći prompt iz Koraka 6 bio najefikasniji

## Šta si naučio

- **Session opener disciplina**: sesija počinje s CLAUDE.md kao prvim kontekstom — to je persistentna memorija projekta, ne chat history
- **/plan mode** sprečava Claude da piše kod bez odobrenog plana — koristiš ga kad promjena dodiruje više fajlova
- **/compact** sažima chat history ali ne uništava CLAUDE.md — informacije koje su samo u chatu se gube, informacije u fajlovima preživljavaju
- **Bounded execution message** sadrži specifične fajlove, granice scopea i verification instrukciju — vague prompts produciraju vague rezultate
- **Prompt iteracija**: tri iteracije istog zahtjeva pokazuju koliko specifičnost utječe na kvalitet outputa — vague prompt daje vague implementaciju
