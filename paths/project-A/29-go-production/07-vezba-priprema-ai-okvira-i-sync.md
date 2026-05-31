# 07 — Vežba: priprema AI-okvira i sync (Go Production)

Potvrđuješ i proširuješ AI-okvir za Go production rad, pa implementiraš distributed lock + outbox pattern u go-service iz graduation projekta.

---

## Cilj

Na kraju vežbe imaš:
- Distributed lock s Redsync-om koji sprečava duplu obradu cron joba
- Transactional outbox koji garantuje da se eventi ne izgube pri crash-u
- Context cancellation u svim downstream pozivima (DB, Redis, HTTP)
- Race detector pokrenut u CI bez grešaka

---

## Korak 1 — Provjeri i produbi AI-okvir

```
1. Reci Claude šta već postoji u go-service (paste relevant code)
2. Pitaj: "Koji dijelovi koda imaju potencijalni race condition?"
3. Pitaj: "Gdje trebam dodati context propagation?"
4. Pitaj: "Kako da implementiram outbox za order.created event?"
```

Očekivani AI output: concrete code review s linijama gdje nedostaje `ctx`, gdje fali lock, i draft outbox implementacije za tvoj konkretni DB schema.

---

## Korak 2 — Race detector u CI

```bash
# Lokalno — pokreni testove s race detectorom
go test -race -count=1 ./...

# Provjeri da nema WARNING: DATA RACE u outputu
```

Dodaj u `.gitlab-ci.yml`:

```yaml
test:go:race:
  stage: test
  script:
    - go test -race -count=1 -timeout=120s ./...
  variables:
    GORACE: "halt_on_error=1 log_path=/tmp/race"
  artifacts:
    when: on_failure
    paths:
      - /tmp/race*
```

Ako postoji race condition — fiksuj ga (atomic, mutex, ili channel) prije nastavka.

---

## Korak 3 — Context propagation audit

Prođi kroz go-service handler-e i provjeri:

```bash
# Pronađi mjesta gdje se context ne prenosi
grep -rn "http.Get\|http.Post\|sql.Query\b" ./services/go-service/
# Svaki poziv bez Context varijante je kandidat za popravak
```

Promijeni sve `http.Get(url)` u `http.NewRequestWithContext(ctx, ...)`.
Promijeni sve `db.Query(query)` u `db.QueryContext(ctx, query)`.

---

## Korak 4 — Distributed lock za cron job

U `go-service/internal/jobs/invoice_job.go`:

```go
func (j *InvoiceJob) Run(ctx context.Context) error {
    // TODO: dodaj Redsync lock ovdje
    // Lock key: "cron:monthly-invoices"
    // TTL: 10 minuta
    // Ako je lock zauzet: log i vrati nil (normalan slučaj)
    return j.generateAll(ctx)
}
```

Verifikuj da dva paralelna pokretanja ne procesiraju isti posao:

```bash
# Pokreni job dva puta paralelno
go run ./cmd/invoice-job &
go run ./cmd/invoice-job &
wait

# Provjeri logove — drugi run treba logirati "already running"
```

---

## Korak 5 — Outbox za order.created

1. Kreiraj `outbox` tabelu u MySQL migration:

```sql
-- migrations/0042_create_outbox.sql
CREATE TABLE outbox (
    id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    event_type   VARCHAR(100) NOT NULL,
    aggregate    VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    payload      JSON NOT NULL,
    status       ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
    attempts     INT NOT NULL DEFAULT 0,
    created_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    sent_at      DATETIME(3) NULL,
    INDEX idx_status_created (status, created_at)
);
```

2. U `CreateOrder` transakciju dodaj INSERT u outbox
3. Implementiraj `OutboxRelay` goroutinu koja se pokreće uz server
4. Verifikuj: ubij proces između INSERT orders i INSERT outbox — order ne smije biti bez eventa

---

## Korak 6 — Provjeri s AI

```
Paste go-service CreateOrder handler.
Pitaj: "Da li je outbox atomarno s kreacijom order-a?"
Pitaj: "Šta se desi ako relay crashne između SELECT i XAdd?"
Pitaj: "Kako testirati outbox relay bez pravog Redis-a?"
```

---

## Checklist

- [ ] `go test -race ./...` prolazi bez DATA RACE upozorenja
- [ ] Svi DB pozivi koriste `QueryContext`, `ExecContext` itd.
- [ ] Svi HTTP pozivi koriste `NewRequestWithContext`
- [ ] Cron job ne pokreće duplu obradu ako se pokrene paralelno
- [ ] `CREATE ORDER` i `INSERT INTO outbox` su u istoj DB transakciji
- [ ] Outbox relay se pokreće kao goroutina uz server
- [ ] Ručni crash test: Order bez eventa nije moguć
- [ ] CI job s `-race` flagom postoji u `.gitlab-ci.yml`
