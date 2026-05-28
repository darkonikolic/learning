# Lab 15 — Checkpoint i kompresija konteksta

## Cilj
Na kraju ovog laba imaš checkpoint packet za crawler Phase 1 koji sadrži sve što je potrebno za nastavak rada, demonstriraš da nova sesija može nastaviti samo s checkpointom, i prošao/la si compression validation test.

## Preduvjeti
- Lab 14 završen: crawler Phase 1 implementirana
- `docs/specs/crawler-phase1-fetch-parse.md` postoji s ACs
- `cmd/crawler/fetcher/fetcher.go` postoji

## Kontekst
Dugi radni dani produciravaju duge sesije. Duge sesije pune se s L4 operativnim kontekstom (error logovi, test output) koji potiskuje L2 SPEC kontekst. Checkpoint packet je tvoj alat za "reset" — pišeš ga PRIJE /compact, i u novoj sesiji učitavaš samo checkpoint umjesto cijele historije.

## Koraci

### Korak 1 — Simuliraj dugu sesiju s 10+ operacija

Otvori Claude sesiju i simuliraj rad na crawler kodu:

```bash
claude
```

Pošalji ove promte jedan po jedan (simuliraj realni rad):

**Operacija 1:**
```
Read cmd/crawler/fetcher/fetcher.go and explain the current implementation.
```

**Operacija 2:**
```
Read docs/specs/crawler-phase1-fetch-parse.md and list all acceptance criteria.
```

**Operacija 3:**
```
Run: go test ./cmd/crawler/fetcher/... -v
```

**Operacija 4:**
```
What would happen if the jsonplaceholder API returns a 500 error?
```

**Operacija 5:**
```
Read cmd/crawler/inserter/inserter.go
```

**Operacija 6:**
```
What is the difference between Phase 1 and Phase 2 in the crawler?
```

**Operacija 7:**
```
Run: go build ./...
```

**Operacija 8:**
```
Read docs/crawler/dependency-graph.md
```

**Operacija 9:**
```
What acceptance criteria in Phase 1 SPEC are currently not covered by tests?
```

**Operacija 10:**
```
Run: curl -s https://jsonplaceholder.typicode.com/todos | head -c 500
```

Provjeri context fill:

```
/context
```

Zabilježi postotak (treba biti 30-60% popunjeno).

---

### Korak 2 — Napiši checkpoint packet PRIJE /compact

KLJUČNO: napiši checkpoint PRIJE nego pokreneš /compact. Checkpoint je tvoj insurance policy.

```
Before I run /compact, help me write a checkpoint packet for the current state.

I need to capture (in docs/checkpoints/crawler-phase1.md):
1. Verified state: which ACs from docs/specs/crawler-phase1-fetch-parse.md are passing
2. Open decisions made this session: any technical choices made
3. Next action: the specific next thing to do (one concrete step)
4. File paths that matter: all relevant files with their purpose
5. Protected verbatim items: exact AC text, exact field names, exact error messages

Format per 15-context-compression/01-compression-and-checkpoints.md checkpoint format.
Write to docs/checkpoints/crawler-phase1.md.
```

Provjeri checkpoint:

```bash
cat docs/checkpoints/crawler-phase1.md
```

**Provjeri da checkpoint sadrži:**
- Svaki AC s PASS/FAIL statusom
- Exact field names iz Todo struct-a
- Exact error messages
- File paths (apsolutni ili repo-relativni)
- Next action (jedna konkretna stvar, ne lista)

---

### Korak 3 — Pokreni /compact

Sada pokreni compact:

```
/compact
```

**Nakon compact:**

```
/context
```

Zabilježi novi postotak — treba biti manji od prethodnog.

---

### Korak 4 — Compression validation test

Odmah nakon /compact, provjeri da kritične informacije nisu izgubljene:

**Pitanje 1:**
```
What does AC-02 from docs/specs/crawler-phase1-fetch-parse.md require exactly — 
give me the exact status code and response validation requirement.
```

Ako Claude odgovori s parafrazom ("validates the response") umjesto egzaktnog teksta → kompresija je uništila AC. Reloaduj SPEC.

**Pitanje 2:**
```
What are the exact field names in the Todo struct from cmd/crawler/fetcher/fetcher.go?
```

Ako Claude pogriješi field names → context je pokvaren. Reloaduj fajl.

**Pitanje 3:**
```
What is the next concrete action based on the current state of crawler Phase 1?
```

Ako Claude ne može odgovoriti bez da "izmišlja" → checkpoint nije bio dovoljan.

**Ako bilo koji odgovor je paraphrase:**

```
Load docs/checkpoints/crawler-phase1.md — this is the ground truth for current state.
Now answer the previous question again using the checkpoint as context.
```

---

### Korak 5 — Zatvori sesiju i otvori novu

Zatvori Claude sesiju:

- Pritisni `Ctrl+C` ili ukucaj `/exit`

Otvori NOVU sesiju:

```bash
claude
```

U novoj sesiji, pošalji SAMO checkpoint (bez dugog setup prompta):

```
I'm resuming work on the task-api crawler.

Load my checkpoint: docs/checkpoints/crawler-phase1.md

Based ONLY on the checkpoint (do not read other files yet):
1. What phase are we on?
2. Which ACs are passing?
3. What is the next action?
```

**Očekivani output:**
Nova sesija treba moći odgovoriti na sva 3 pitanja koristeći samo checkpoint fajl.

---

### Korak 6 — Checkpoint validation test u novoj sesiji

U novoj sesiji, pokreni 3 validation pitanja:

**Validation 1:**
```
Based on docs/checkpoints/crawler-phase1.md, 
what would cause a test to fail for AC-04 (insertion order)?
Cite the exact criterion text.
```

**Validation 2:**
```
Based on docs/checkpoints/crawler-phase1.md,
what files need to be read before implementing the next action?
```

**Validation 3:**
```
Based on docs/checkpoints/crawler-phase1.md,
what are the open decisions that were made during the previous session?
```

**Provjeri:**
- Da li nova sesija može odgovoriti na sva 3 pitanja?
- Da li citira egzaktan tekst umjesto parafraze?
- Da li zna koji je sljedeći korak?

Ako da — checkpoint je validan.

---

### Korak 7 — Identificiraj šta je checkpoint spasio

Napiši kratku refleksiju u `docs/checkpoints/crawler-phase1-reflections.md`:

```
Create docs/checkpoints/crawler-phase1-reflections.md with:

1. Context level analysis:
   What was in the session at the time of /compact?
   - L1 (Goal): [da li je bio definisan?]
   - L2 (SPEC): [koja SPEC sekcija je bila u context-u?]
   - L3 (Implementation): [koji fajlovi su bili pročitani?]
   - L4 (Operational): [koji error logovi/test output je bio u context-u?]

2. What the checkpoint preserved vs what would have been lost:
   - Preserved by checkpoint: [lista]
   - Would have been lost without checkpoint: [lista]

3. What made this checkpoint effective:
   - [3-4 bullet points]
```

---

### Korak 8 — Commituj checkpoint artefakte

```bash
mkdir -p docs/checkpoints
git add docs/checkpoints/
git commit -m "docs: crawler phase1 checkpoint packet — context compression artifact"
```

## Verifikacija

- [ ] `docs/checkpoints/crawler-phase1.md` postoji s popunjenim svim sekcijama
- [ ] Checkpoint sadrži exact AC text (ne paraphraze)
- [ ] Checkpoint sadrži exact field names iz Todo struct-a
- [ ] Checkpoint sadrži next action kao jednu konkretnu instrukciju
- [ ] Nova sesija može odgovoriti na sva 3 validation pitanja koristeći samo checkpoint
- [ ] `/compact` je pokrenut i context postotak je smanjen
- [ ] `docs/checkpoints/crawler-phase1-reflections.md` postoji

## Šta si naučio

- **4 context nivoa** imaju različite karakteristike: L4 (error logovi) je ephemeral, L2 (SPEC) mora preživjeti kompresiju
- **Checkpoint packet PRIJE /compact** je insurance policy — /compact može izgubiti detalje, checkpoint ih čuva
- **Protected verbatim zones**: exact AC text, exact field names, exact error messages — ove se ne smiju parafrazirati jer parafhraza = drift
- **Compression validation test** (3 pitanja) verificira da checkpoint može zamijeniti session history — ako nova sesija može odgovoriti, checkpoint je dovoljan
- **L4 flooding L2** je česti problem u dugim sesijama: error logovi i test output istiskuju SPEC iz context-a — checkpoint resetuje na čiste L1+L2
