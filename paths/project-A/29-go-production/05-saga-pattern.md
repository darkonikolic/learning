# 05 — Saga pattern

## Problem: distribuirana transakcija

```
CreateOrder flow:
  1. Rezerviraj inventory       (InventoryService)
  2. Naplati plaćanje           (PaymentService)
  3. Pošalji email potvrdu      (NotificationService)
  4. Ažuriraj analytics         (AnalyticsService)
```

Ako plaćanje uspije ali email fail-uje — šta se desi? Ako rezerviša inventory ali payment fail-uje — treba otpustiti rezervaciju. Klasična DB transakcija ne radi preko servisnih granica.

**Saga** je niz lokalnih transakcija gdje svaka lokalna transakcija ima kompenzacijsku transakciju za rollback.

---

## Dvije varijante

### Choreography (koreografija) — eventi bez centralnog koordinatora

```
OrderService
  │ publishes: order.created
  ▼
InventoryService
  │ listens: order.created
  │ reserves stock
  │ publishes: inventory.reserved  ──OR──  inventory.failed
  ▼                                              │
PaymentService                           OrderService
  │ listens: inventory.reserved            listens: inventory.failed
  │ charges card                           cancels order
  │ publishes: payment.completed
  ▼
NotificationService
  listens: payment.completed
  sends confirmation email
```

Prednosti: jednostavan, nema single point of failure, servisi su potpuno decouplani.
Mane: teško pratiti stanje cijele sage, teško debugirati, kompenzacije moraju biti u svakom servisu.

### Orchestration (orkestracija) — centralni koordinator

```
SagaOrchestrator (go-service)
  │
  ├─ Step 1: InventoryService.Reserve(orderID)
  │     OK → Step 2
  │     FAIL → saga FAILED
  │
  ├─ Step 2: PaymentService.Charge(orderID)
  │     OK → Step 3
  │     FAIL → kompenzacija: InventoryService.Release(orderID)
  │
  ├─ Step 3: NotificationService.SendEmail(orderID)
  │     OK → saga COMPLETED
  │     FAIL → kompenzacija: PaymentService.Refund(orderID)
  │                         InventoryService.Release(orderID)
```

Prednosti: centralizovana vidljivost stanja, lakši debugging, kompenzacije su na jednom mjestu.
Mane: orchestrator je coupling tačka, kompleksniji za implementirati.

Za project-A: choreography za jednostavne tokove, orchestration za kompleksne (naplate s više koraka).

---

## Go implementacija — Orchestration

### Saga state machine

```go
type SagaStep struct {
    Name      string
    Execute   func(ctx context.Context, data *SagaData) error
    Compensate func(ctx context.Context, data *SagaData) error
}

type SagaOrchestrator struct {
    steps  []SagaStep
    db     *sql.DB
    logger *slog.Logger
}

type SagaData struct {
    OrderID     string
    UserID      string
    Amount      float64
    InventoryID string  // postavlja InventoryService
    PaymentID   string  // postavlja PaymentService
}

func (o *SagaOrchestrator) Execute(ctx context.Context, data *SagaData) error {
    executedSteps := []SagaStep{}

    for _, step := range o.steps {
        o.logger.Info("executing saga step", "step", step.Name, "order", data.OrderID)

        if err := step.Execute(ctx, data); err != nil {
            o.logger.Error("saga step failed, compensating", "step", step.Name, "err", err)

            // Kompenzacija u obrnutom redoslijedu
            for i := len(executedSteps) - 1; i >= 0; i-- {
                s := executedSteps[i]
                if compErr := s.Compensate(ctx, data); compErr != nil {
                    o.logger.Error("compensation failed", "step", s.Name, "err", compErr)
                    // Ovo je ozbiljan problem — alarm + ručna intervencija
                }
            }

            return fmt.Errorf("saga failed at step %s: %w", step.Name, err)
        }

        executedSteps = append(executedSteps, step)
    }

    return nil
}
```

### Definicija koraka

```go
func NewCreateOrderSaga(inv *InventoryClient, pay *PaymentClient, notif *NotifClient) *SagaOrchestrator {
    return &SagaOrchestrator{
        steps: []SagaStep{
            {
                Name: "reserve-inventory",
                Execute: func(ctx context.Context, d *SagaData) error {
                    id, err := inv.Reserve(ctx, d.OrderID, d.Items)
                    if err != nil {
                        return err
                    }
                    d.InventoryID = id
                    return nil
                },
                Compensate: func(ctx context.Context, d *SagaData) error {
                    if d.InventoryID == "" {
                        return nil  // nikad rezervisano
                    }
                    return inv.Release(ctx, d.InventoryID)
                },
            },
            {
                Name: "process-payment",
                Execute: func(ctx context.Context, d *SagaData) error {
                    id, err := pay.Charge(ctx, d.UserID, d.Amount, d.OrderID)
                    if err != nil {
                        return err
                    }
                    d.PaymentID = id
                    return nil
                },
                Compensate: func(ctx context.Context, d *SagaData) error {
                    if d.PaymentID == "" {
                        return nil
                    }
                    return pay.Refund(ctx, d.PaymentID)
                },
            },
            {
                Name: "send-confirmation",
                Execute: func(ctx context.Context, d *SagaData) error {
                    return notif.SendOrderConfirmation(ctx, d.OrderID)
                },
                Compensate: func(ctx context.Context, d *SagaData) error {
                    // Email se ne može "un-send" — log samo, ne fail
                    return nil
                },
            },
        },
    }
}
```

---

## Perzistentno stanje sage — crash recovery

Ako Pod crashne u sredini sage, kompenzacije se nikad ne pokrenu. Zato saga state treba biti u bazi:

```sql
CREATE TABLE sagas (
    id          VARCHAR(36) PRIMARY KEY,
    type        VARCHAR(100) NOT NULL,
    status      ENUM('running', 'completed', 'compensating', 'failed') NOT NULL,
    current_step VARCHAR(100),
    data        JSON NOT NULL,
    created_at  DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at  DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
);

CREATE TABLE saga_steps (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    saga_id     VARCHAR(36) NOT NULL,
    step_name   VARCHAR(100) NOT NULL,
    status      ENUM('pending', 'completed', 'compensated', 'failed') NOT NULL,
    executed_at DATETIME(3),
    FOREIGN KEY (saga_id) REFERENCES sagas(id)
);
```

Saga recovery job (pokreće se na startup i periodično):

```go
func (o *SagaOrchestrator) RecoverStuck(ctx context.Context) error {
    // Pronađi sage koje su zapele (running > 10 minuta)
    rows, err := o.db.QueryContext(ctx, `
        SELECT id, data FROM sagas
        WHERE status = 'running'
        AND updated_at < NOW() - INTERVAL 10 MINUTE
    `)
    // ... za svaku: pokreni kompenzaciju
}
```

---

## Choreography primjer za jednostavni tok

```go
// InventoryService consumer
func (c *InventoryConsumer) OnOrderCreated(ctx context.Context, event OrderCreatedEvent) error {
    if err := c.reserveStock(ctx, event.OrderID, event.Items); err != nil {
        // Objavi failure event — PaymentService ga ne obrađuje, OrderService cancela
        return c.events.Publish(ctx, "inventory.reservation.failed", InventoryFailedEvent{
            OrderID: event.OrderID,
            Reason:  err.Error(),
        })
    }
    return c.events.Publish(ctx, "inventory.reserved", InventoryReservedEvent{
        OrderID:     event.OrderID,
        ReservationID: reservationID,
    })
}

// OrderService consumer — sluša failure i cancela
func (c *OrderConsumer) OnInventoryFailed(ctx context.Context, event InventoryFailedEvent) error {
    return c.orderRepo.UpdateStatus(ctx, event.OrderID, "cancelled")
}
```

---

## Kada orchestration, kada choreography

| Kriterij | Choreography | Orchestration |
|----------|-------------|---------------|
| Broj koraka | 2-3 | 4+ |
| Kompenzacije | Svaki servis sam | Centralizirano |
| Vidljivost toka | Teška | Laka (jedan log) |
| Coupling | Loose | Tighter (orchestrator zna za sve) |
| Debugging | "Gdje je zapelo?" | Odmah vidljivo |
| Project-A preporuka | Jednostavni eventi | Naplatni tok |

---

## Veza sa project-A

```
Choreography: order.created → inventory reservation → stock update
Orchestration: checkout flow → inventory + payment + notification + analytics
```

Checkout tok koristi orchestration jer ima više koraka i kompenzacije moraju biti pouzdane (novac je u pitanju).
