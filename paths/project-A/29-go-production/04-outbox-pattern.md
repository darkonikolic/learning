# 04 — Transactional Outbox pattern

## Problem: izgubljena poruka

```
func (s *OrderService) CreateOrder(ctx context.Context, req *CreateOrderRequest) error {
    // Korak 1: spremi order u DB
    order, err := s.db.CreateOrder(ctx, req)
    if err != nil {
        return err
    }

    // Korak 2: pošalji event na message broker
    err = s.redis.Publish(ctx, "order.created", order)
    if err != nil {
        // Order je u bazi, ali event nije poslan
        // Korisnik je naplaćen ali inventory nije ažuriran
        return err
    }
}
```

Problem: DB i message broker su dva odvojena sistema. Nema distribuirane transakcije koja pokriva oba. Između koraka 1 i 2 može:
- Pasti mreža (Redis nedostupan)
- Pasti Pod (OOMKilled, SIGTERM)
- Redis biti privremeno preopterećen

Rezultat: **ghost order** — postoji u bazi, inventory i billing nikad ne dobijaju event.

---

## Outbox pattern — rješenje

Umjesto direktnog slanja na broker, spremi event u `outbox` tabelu unutar **iste DB transakcije** kao i ostale promjene. Zasebni process čita outbox i šalje na broker.

```
┌─────────────────────────────────────────────────────┐
│  DB transakcija (atomarna)                          │
│                                                     │
│  INSERT INTO orders (...)                           │
│  INSERT INTO outbox (event_type, payload, status)   │
└─────────────────────────────────────────────────────┘
          │
          │ Outbox relay (zasebna goroutina/pod)
          │ čita pending evente, šalje na broker
          ▼
    Redis Streams / SQS / NATS
          │
          ▼
    Consumer servisi
```

Atomarnost garantuje: ili su oba INSERT-a uspjela (order + outbox), ili nijedan. Nema "order bez eventa".

---

## Schema

```sql
CREATE TABLE outbox (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    event_type  VARCHAR(100)    NOT NULL,
    aggregate   VARCHAR(100)    NOT NULL,  -- "order", "user", "invoice"
    aggregate_id VARCHAR(100)   NOT NULL,
    payload     JSON            NOT NULL,
    status      ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
    attempts    INT             NOT NULL DEFAULT 0,
    created_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    sent_at     DATETIME(3)     NULL,
    INDEX idx_status_created (status, created_at)
);
```

---

## Go implementacija

### Service — upis u istoj transakciji

```go
func (s *OrderService) CreateOrder(ctx context.Context, req *CreateOrderRequest) (*Order, error) {
    var order *Order

    err := s.db.Transaction(ctx, func(tx *sql.Tx) error {
        var err error

        // 1. Kreiraj order
        order, err = createOrderTx(ctx, tx, req)
        if err != nil {
            return err
        }

        // 2. Upisi event u outbox — ISTA transakcija
        payload, _ := json.Marshal(OrderCreatedEvent{
            OrderID:    order.ID,
            UserID:     order.UserID,
            Amount:     order.Amount,
            OccurredAt: time.Now(),
        })

        _, err = tx.ExecContext(ctx, `
            INSERT INTO outbox (event_type, aggregate, aggregate_id, payload)
            VALUES (?, ?, ?, ?)`,
            "order.created", "order", order.ID, payload,
        )
        return err
    })

    return order, err
}
```

### Outbox relay — čitaj i šalji

```go
type OutboxRelay struct {
    db     *sql.DB
    redis  *redis.Client
    logger *slog.Logger
}

func (r *OutboxRelay) Run(ctx context.Context) error {
    ticker := time.NewTicker(500 * time.Millisecond)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return nil
        case <-ticker.C:
            if err := r.processBatch(ctx); err != nil {
                r.logger.Error("outbox relay error", "err", err)
            }
        }
    }
}

func (r *OutboxRelay) processBatch(ctx context.Context) error {
    // Zauzmi batch eventa (SELECT FOR UPDATE SKIP LOCKED = nema contention između replika)
    rows, err := r.db.QueryContext(ctx, `
        SELECT id, event_type, aggregate, aggregate_id, payload
        FROM outbox
        WHERE status = 'pending'
        ORDER BY created_at
        LIMIT 100
        FOR UPDATE SKIP LOCKED
    `)
    if err != nil {
        return err
    }
    defer rows.Close()

    for rows.Next() {
        var event OutboxEvent
        if err := rows.Scan(&event.ID, &event.Type, &event.Aggregate,
            &event.AggregateID, &event.Payload); err != nil {
            return err
        }

        if err := r.publishEvent(ctx, event); err != nil {
            r.markFailed(ctx, event.ID)
            continue
        }
        r.markSent(ctx, event.ID)
    }
    return nil
}

func (r *OutboxRelay) publishEvent(ctx context.Context, event OutboxEvent) error {
    return r.redis.XAdd(ctx, &redis.XAddArgs{
        Stream: "events:" + event.Aggregate,
        Values: map[string]interface{}{
            "event_type":   event.Type,
            "aggregate_id": event.AggregateID,
            "payload":      event.Payload,
        },
    }).Err()
}
```

`SKIP LOCKED` je ključno: ako više relay instanci radi paralelno, svaka dobija različiti batch bez čekanja na lock.

---

## Idempotency u consumeru

Outbox relay implementira at-least-once delivery — može poslati isti event više puta (retry). Consumer mora biti idempotentan:

```go
func (c *InventoryConsumer) HandleOrderCreated(ctx context.Context, event OrderCreatedEvent) error {
    // Provjeri jesmo li već obradili ovaj event
    processed, err := c.redis.SetNX(ctx,
        "processed:order.created:"+event.OrderID,
        "1",
        24*time.Hour,
    ).Result()
    if err != nil {
        return err
    }
    if !processed {
        return nil  // već obrađeno — idempotentno ignoriši
    }

    return c.reserveInventory(ctx, event.OrderID, event.Items)
}
```

---

## Dead letter queue za failed evente

```go
func (r *OutboxRelay) markFailed(ctx context.Context, id int64) {
    r.db.ExecContext(ctx, `
        UPDATE outbox
        SET status = CASE WHEN attempts >= 5 THEN 'failed' ELSE 'pending' END,
            attempts = attempts + 1
        WHERE id = ?
    `, id)
    // attempts >= 5 → status = 'failed' → event ne blokira queue, ali je vidljiv za debug
}
```

Alert na `SELECT COUNT(*) FROM outbox WHERE status = 'failed'` — svaki failed event zahtijeva ručnu provjeru.

---

## Veza sa project-A

Outbox se koristi svaki put kada Order service treba notificirati druge servise:
- `order.created` → InventoryService rezerviše stock
- `order.paid` → EmailService šalje potvrdu
- `order.shipped` → NotificationService šalje SMS

Sve kroz outbox — nema direktnih inter-service HTTP poziva za eventual-consistent operacije.
