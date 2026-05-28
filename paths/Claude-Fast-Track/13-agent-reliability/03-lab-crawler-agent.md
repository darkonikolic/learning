# Lab 13 — Crawler agent: dohvati todos i umetni u task-api

## Cilj
Na kraju ovog laba imaš Claude subagent koji dohvata todos s `https://jsonplaceholder.typicode.com/todos`, umeće ih kao taskove u `task-api`, klasificiraš failure kada task-api nije up, i postoji dokumentovani recovery prompt s backoffom.

## Preduvjeti
- Lab 09 završen: Docker Compose s MySQL radi
- Lab 12 završen: task-api koristi MySQL storage (ili in-memory — obje varijante rade)
- `go build ./...` prolazi, server se može pokrenuti

## Kontekst
Crawler je klasičan agent reliability scenarij: agent koji poziva vanjski API (jsonplaceholder), transformira podatke, i umeće ih u drugu uslugu (task-api). Kada task-api nije up, crawler mora detektovati grešku, klasificirati je i imati recovery strategiju. Ovo je real-world pattern za data pipeline agents.

**External API:** `https://jsonplaceholder.typicode.com/todos`
- Javni, besplatni API
- Uvijek up, bez autentikacije
- Vraća 200 todos s poljem: userId, id, title, completed

## Koraci

### Korak 1 — Napiši crawler agent definition

```bash
mkdir -p .claude/agents
```

Napravi `.claude/agents/todo-crawler.md`:

```markdown
---
name: todo-crawler
description: Fetch todos from jsonplaceholder.typicode.com and insert them as tasks in task-api. Use when asked to crawl, import, or seed todos.
model: claude-sonnet-4-6
---

# Todo Crawler Agent

## Role
Ti si crawler agent koji dohvata todos iz javnog JSONPlaceholder API-a
i umeće ih kao taskove u lokalni task-api server.

## Allowed tools
- Bash (curl, jq, sleep)
- Read (čitanje config fajlova)

## Forbidden
- Write/Edit (ne modifikuješ kod)
- Bash (go, git, docker komande)

## Task

1. Dohvati todos:
   curl -s https://jsonplaceholder.typicode.com/todos | jq '.[0:10]'

2. Za svaki todo, umetni kao task:
   curl -s -X POST http://localhost:8080/tasks \
     -H "Content-Type: application/json" \
     -d '{"title": "[todo title]"}'

3. Verificiraj insertion:
   curl -s http://localhost:8080/tasks | jq 'length'

## Error handling

Ako task-api nije dostupan (connection refused):
1. Klasificiraj grešku: "Task-api is not running"
2. Čekaj 2 sekunde, pokušaj ponovo (max 3 pokušaja)
3. Ako 3 pokušaji propadnu: STOP i report "FAILURE: task-api unavailable after 3 retries"

Ako todo insert faili:
1. Log failed todo title
2. Nastavi s ostalim todos (ne staj na prvom failure)
3. Na kraju report: N inserted, M failed

## Output format

Nakon crawlera, report:
```
## Crawler Run Report
Status: SUCCESS/FAILURE
Todos fetched: N
Tasks inserted: N
Tasks failed: N
Failures:
- [title]: [error]
Next action: [preporuka]
```
```

---

### Korak 2 — Napiši crawler Go binary

Osim Claude agenta, napiši i CLI crawler koji task-api može koristiti samostalno:

```bash
mkdir -p cmd/crawler
```

Otvori Claude sesiju:

```bash
claude
```

```
Read docs/specs/ and tasks/store.go to understand the Task structure.

Create cmd/crawler/main.go — a Go CLI that:
1. Fetches todos from https://jsonplaceholder.typicode.com/todos
2. Takes first 10 todos (to avoid flooding)
3. For each todo, POSTs to http://localhost:8080/tasks (or $TASK_API_URL env var)
4. Implements simple retry: 3 attempts with 2s backoff on connection error
5. Reports: N inserted, M failed

Requirements:
- stdlib only: net/http, encoding/json, os, time, fmt, log
- No external packages
- Error handling: if connection refused, retry with backoff
- Log each insertion attempt

Run go build ./cmd/crawler/... after creation.
```

---

### Korak 3 — Namjerno uzrokuj failure: crawler kad task-api nije up

**Provjeri da task-api NIJE pokrenut:**

```bash
# Zaustavi server ako radi
docker compose down
# ili
pkill -f "task-api" 2>/dev/null
```

**Pokreni crawler (mora failikovati):**

```bash
go run cmd/crawler/main.go 2>&1
```

**Očekivani output:**
Crawler treba prikazati retry pokušaje i na kraju reportovati failure:

```
2026/05/26 10:30:00 Attempt 1/3: connecting to http://localhost:8080...
2026/05/26 10:30:00 Attempt 1/3 failed: dial tcp 127.0.0.1:8080: connect: connection refused
2026/05/26 10:30:02 Attempt 2/3: connecting to http://localhost:8080...
2026/05/26 10:30:02 Attempt 2/3 failed: ...
2026/05/26 10:30:04 Attempt 3/3: connecting to http://localhost:8080...
2026/05/26 10:30:04 FATAL: task-api unavailable after 3 retries
```

---

### Korak 4 — Klasificiraj failure koristeći taxonomy

Otvori Claude sesiju i klasificiraj grešku:

```
The todo-crawler agent failed with this output:
[Paste output iz Koraka 3]

Classify this failure using the taxonomy from 13-agent-reliability/03-claude-failure-taxonomy.md:
1. What is the failure class?
2. What is the detection signal?
3. What is the confidence level?
4. What is the retry decision?
5. What is the fallback while repair is in progress?

Fill in the 7-field reliability template from 13-agent-reliability/01-when-agents-fail.md.
Write analysis to docs/crawler/failure-analysis-001.md.
```

Provjeri da je analiza kreirana:

```bash
mkdir -p docs/crawler
cat docs/crawler/failure-analysis-001.md
```

---

### Korak 5 — Napiši recovery prompt s backoffom

```
Based on the failure analysis in docs/crawler/failure-analysis-001.md,
write a recovery prompt for when task-api is unavailable.

The prompt should:
1. Check if task-api is up before starting
2. If not up: wait 5 seconds and check again (up to 3 times)
3. If still not up: report failure with exact error and suggested fix
4. If up: proceed with crawling

Write the recovery procedure to docs/crawler/recovery-procedure.md
```

---

### Korak 6 — Uspješno pokretanje crawler-a

Sada pokreni task-api:

```bash
go run main.go &
# ili
docker compose up -d
```

Provjeri da je server up:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/tasks
# Ocekivano: 200
```

Pokreni crawler:

```bash
go run cmd/crawler/main.go
```

**Očekivani output:**
```
2026/05/26 10:35:00 Fetching todos from https://jsonplaceholder.typicode.com/todos...
2026/05/26 10:35:01 Fetched 10 todos
2026/05/26 10:35:01 Inserting todo 1/10: "delectus aut autem"
2026/05/26 10:35:01 Inserted: id=abc123
...
2026/05/26 10:35:02 DONE: 10 inserted, 0 failed
```

Verificiraj da su taskovi umetnuti:

```bash
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
print(f'Total tasks: {len(tasks)}')
print('First 3 tasks:')
for t in tasks[:3]:
    print(f'  - {t[\"title\"]}')
"
```

**Provjeri barem 10 tasks:**

```bash
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
assert len(tasks) >= 10, f'Expected >= 10 tasks, got {len(tasks)}'
print(f'SUCCESS: {len(tasks)} tasks found')
"
```

---

### Korak 7 — Pokreni Claude crawler agent

Uz server koji radi, pokreni Claude crawler agent direktno:

```bash
claude
```

```
Use the todo-crawler agent to fetch todos from jsonplaceholder and insert them into task-api.

The server is running at http://localhost:8080.
Insert todos 11-20 (to avoid duplicates with Go binary run).

After completing, provide the Crawler Run Report.
```

Provjeri report i verificiraj da je barem 10 novih todos umetno (ukupno sada 20+):

```bash
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
print(f'Total tasks after agent run: {len(tasks)}')
"
```

---

### Korak 8 — Commituj sve

```bash
git add cmd/crawler/ .claude/agents/todo-crawler.md docs/crawler/
git commit -m "feat: todo-crawler agent + CLI with retry backoff and failure classification"
```

## Verifikacija

- [ ] `go run cmd/crawler/main.go` insertuje barem 10 todos kad je task-api up
- [ ] `go run cmd/crawler/main.go` prikazuje retry pokušaje i FAILURE poruku kad task-api nije up
- [ ] `docs/crawler/failure-analysis-001.md` postoji s popunjenim 7-field reliability template-om
- [ ] `docs/crawler/recovery-procedure.md` postoji s recovery koracima
- [ ] `.claude/agents/todo-crawler.md` postoji
- [ ] Claude crawler agent uspješno insertuje todos
- [ ] Failure log postoji (docs/crawler/ direktorijum)

## Šta si naučio

- **Agent reliability nije iznimka — to je norma**: crawler koji poziva vanjski API UVIJEK mora imati retry strategiju i failure classification
- **7-field reliability template** je tvoj dijagnostički alat — popuniš ga PRIJE nego dotakneš kod, ne poslije
- **Backoff retry** znači: čekaj 2s, pa 4s, pa 8s — ne ponavljaj odmah jer se greška vjerovatno neće popraviti za 100ms
- **Klasifikacija failure-a** (connection refused vs timeout vs 5xx) daje različite recovery strategije
- **Failure log na disku** je trace koji možeš pročitati sutra, za razliku od chat history koji je ephemeral
