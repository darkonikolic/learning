# 06 — Vežba: Async i redovi

Verifikuješ producer/consumer tok sa idempotentnim handler-ima, retry/backoff mehanizmom i dead-letter queue-om za neuspele poruke.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Implementiramo async worker koji obrađuje poruke iz Redis Streams-a (ili drugog message broker-a) sa idempotentnim handler-ima, eksponencijalnim backoff-om i DLQ za poruke koje ne mogu da se obrade. Verifikujemo da dupla isporuka ne pravi dvostruki efekat.

**Pretpostavke za potvrdu:**
- Message broker (Redis Streams / RabbitMQ / SQS) je dostupan u docker compose
- Worker se može restartovati i nastaviti obradu bez gubitka poruka
- Postoji način da vidimo dubinu reda i starost najstarije poruke (metrike)

**Van opsega:**
- Saga pattern / distribuirane transakcije
- Promena message broker-a (za sada ostaje na izabranom)
- Garantovana exactly-once semantika na nivou infrastrukture

**Prompt za diskusiju:**
```
Imam worker koji obrađuje [poruke tipa]. Isporuka je at-least-once (Redis Streams / broker).
Predloži idempotentan dizajn handler-a sa dedup ključem ili upsert pristupom.
Dodaj retry sa eksponencijalnim backoff-om i dead-letter queue posle N pokušaja.
Koje metrike dubine reda i starosti poruke da pratim i kako ih eksponovati?
Objasni rizike ako preskočim idempotenciju.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Worker obrađuje poruke tačno-jednom efektivno; neuspeh završava u DLQ; dubina reda vidljiva.

**Fajlovi koji se diraju:**
- `internal/worker/handler.go` — idempotentni handler
- `internal/worker/retry.go` — backoff logika
- `internal/worker/dlq.go` — dead-letter queue logika
- `docker-compose.yml` — eventualno dodati DLQ stream/queue

**Fajlovi koji se NE diraju:**
- `internal/api/` — HTTP sloj nije zahvaćen async promenama
- Migracije — shema se menja samo ako handler zahteva novu tabelu (poseban task)

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/async-checks.mdc`
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/async-checks.md`

Sadržaj pravila (isti za oba alata):
```
- Handler mora biti idempotentan (dedup ključ ili upsert); at-least-once isporuka je default.
- Retry sa eksponencijalnim backoff-om; posle N pokušaja poruka ide u dead-letter queue.
- DLQ mora biti eksplicitno imenovan i praćen — nije "baci i zaboravi".
- Metrika dubine reda i starosti najstarije poruke obavezna (observability).
- Worker restart ne sme da izgubi in-flight poruke — koristiti ACK/NACK mehanizam.
```

**Acceptance criteria:**
- [ ] Dupla isporuka iste poruke ne pravi dvostruki efekat (idempotencija potvrđena)
- [ ] Neuspela poruka posle N retry-ja završi u DLQ (proveriti u logovima ili UI-u)
- [ ] Worker se može restartovati i nastaviti obradu bez gubitka poruke
- [ ] Dubina reda vidljiva u metrikama (Prometheus metric ili log)
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Implementirati idempotentan handler sa dedup ključem
2. Dodati retry/backoff logiku sa DLQ after N pokušaja
3. Eksponovati metriku dubine reda
4. Verifikovati sve tri stvari lokalnim testom

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno — posebno oko idempotencije u ovom konkretnom slučaju?
```

---

## 3. Egzekucija

> **Cursor:** koristiš relevantnog agenta
> **Claude Code:** direktno u terminalu

Pokreni stack i verifikuj producer/consumer tok:

```bash
# Digne ceo stack
docker compose up -d

# Objavi test poruku
docker compose exec app ./publish --topic orders --payload '{"id":1,"amount":100}'

# Prati worker logove — treba da vidiš obradu
docker compose logs -f worker

# Verifikuj idempotenciju — pošalji istu poruku ponovo
docker compose exec app ./publish --topic orders --payload '{"id":1,"amount":100}'
docker compose logs -f worker   # ne sme biti dvostruki efekat u DB

# Verifikuj DLQ — pošalji poruku koja će sigurno failovati
docker compose exec app ./publish --topic orders --payload '{"id":999,"invalid":true}'
# posle N retry-ja:
docker compose exec redis redis-cli XLEN orders-dlq   # treba da bude > 0

# Proveri restart
docker compose restart worker
docker compose logs -f worker   # nastavlja obradu, nema izgubljenih poruka

# Metrike dubine reda
curl http://localhost:9090/metrics | grep queue_depth
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- Dupla isporuka ne pravi dvostruki efekat
- Neuspela poruka posle retry-ja završi u DLQ
- Worker restart ne gubi poruke
- Dubina reda vidljiva u metrikama

Evo logova, DB stanja i metrika:
[ovde lepiš stvarni output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali i kako popraviti?
Da li postoji rizik race condition-a u trenutnoj implementaciji?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pošalji poruku sa `id:1`, pričekaj obradu, pošalji istu poruku ponovo | U bazi/logovima tačno jedan zapis za `id:1`; drugi poziv nema efekat |
| 2 | Pošalji namerno nevalidnu poruku (npr. negativan iznos) | Worker pokušava N puta (vidljivo u logovima sa backoff pauzama), zatim poruka prelazi u DLQ |
| 3 | `docker compose restart worker` dok je poruka u obradi | Worker se pokreće, poruka se ponovo obrađuje (ne gubi se), idempotencija sprečava dvostruki efekat |
| 4 | `curl http://localhost:9090/metrics \| grep queue_depth` | Metrika postoji i vrednost se smanjuje kako worker obrađuje poruke |
| 5 | Otvori DLQ stream/queue direktno | Neuspele poruke su tu sa originalnim payloadom i brojem pokušaja |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/async-queues-tooling.md` ili `CLAUDE.md`

```
## [datum] — Async i redovi sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
