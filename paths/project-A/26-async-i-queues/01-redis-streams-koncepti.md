# 01 — Redis Streams koncepti

## Redis data strukture za queuing — razlike

| Struktura | Pattern | Replay | Consumer Groups | Persistence | Koristiti za |
|-----------|---------|--------|-----------------|-------------|-------------|
| List (LPUSH/BRPOP) | Queue | Ne | Ne | AOF/RDB | Jednoredno, ne treba replay |
| Pub/Sub | Fan-out | Ne | Ne | Ne (fire & forget) | Real-time notifikacije |
| **Streams** | **Queue + Log** | **Da** | **Da** | **AOF/RDB** | **Async tasks (naš slučaj)** |
| SQS | Queue | Ne (DLQ) | Da | AWS managed | Enterprise, garantovana dostava |

---

## Redis Streams — ključni koncepti

```
Stream = append-only log s automatskim ID-om po vremenskom markeru
  XADD email-queue * to user@firma.com token abc123
  XADD email-queue * to other@firma.com token def456
  
  ID format: 1705312800123-0 (timestamp_ms - sequence)

Consumer Group = grupa workera koji dijele poruke
  XGROUP CREATE email-queue email-workers $ MKSTREAM
  
  Consumer A dobija poruku 1
  Consumer B dobija poruku 2
  (ne duplikacija — dijele posao)

ACK = potvrda da je poruka obrađena
  XACK email-queue email-workers 1705312800123-0
  
  Bez ACK: poruka ostaje u Pending Entries List (PEL)
  → može biti "reclaimed" od drugog workera
```

---

## Zašto Streams > List za ovu upotrebu

- **Replay**: ako worker padne bez `XACK` → drugi worker preuzima iz PEL
- **Consumer groups**: više workera dijele opterećenje bez duplikacije
- **Monitoring**: `XPENDING` pokazuje zaglavljene poruke i koliko dugo čekaju
- **Dead letter**: poruke s previše retry-a premjestiti u `email-queue:dead`

---

## Tok poruke — lifecycle

```
Registration handler
  ↓ XADD queue:email *  (producer)
  
Redis Stream: queue:email
  ├── 1705312800100-0  { to: a@b.com, token: abc }
  ├── 1705312800200-0  { to: c@d.com, token: def }
  └── 1705312800300-0  { to: e@f.com, token: ghi }
  
Consumer Group: email-workers
  ├── Worker pod-1  ← čita poruku 1 (XREADGROUP)
  └── Worker pod-2  ← čita poruku 2 (XREADGROUP)
  
Uspješna obrada:
  → XACK → poruka izlazi iz PEL
  
Neuspješna obrada (crash/error):
  → poruka ostaje u PEL > 30s
  → reclaimOldMessages je preuzima (XAUTOCLAIM)
  → after MaxRetries → XADD queue:email:dead
```

---

## Korisne Redis CLI naredbe za dijagnostiku

```bash
# Koliko poruka čeka u streamu
XLEN queue:email

# Pregled pending poruka (neacknowledged)
XPENDING queue:email email-workers - + 10

# Čitanje dead letter queue
XRANGE queue:email:dead - + COUNT 10

# Info o consumer group
XINFO GROUPS queue:email

# Info o svim consumerima u grupi
XINFO CONSUMERS queue:email email-workers
```
