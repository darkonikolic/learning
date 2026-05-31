# 03 — Distributed locking

## Problem koji lock rješava

U horizontalno skaliranoj aplikaciji (više pod instanci), isti posao može pokrenuti više instanci paralelno:

```
Pod A                    Pod B
  │                        │
  ├─ provjeri inventory     ├─ provjeri inventory
  │  (result: 1 item)       │  (result: 1 item)
  │                        │
  ├─ rezerviraj item ──────┤─ rezerviraj item
  │                        │
  ↓                        ↓
  Oba potvrde rezervaciju za isti item koji postoji samo jednom
```

Lokalni `sync.Mutex` ne pomaže — vrijedi samo unutar jednog procesa.

---

## Redis SETNX — jednoatomarni lock

Princip: `SET key value NX EX ttl` je atomarni "set if not exists with expiry". Ako ključ ne postoji, postavi ga i vrati OK. Ako postoji (lock drži neko drugi), vrati nil.

```go
type RedisLock struct {
    client *redis.Client
    key    string
    value  string        // jedinstveni ID za sigurno otpuštanje
    ttl    time.Duration
}

func NewLock(client *redis.Client, key string, ttl time.Duration) *RedisLock {
    return &RedisLock{
        client: client,
        key:    "lock:" + key,
        value:  uuid.New().String(),  // jedinstven po instanci
        ttl:    ttl,
    }
}

// Acquire — pokušaj zauzeti lock, max `timeout` čekaj
func (l *RedisLock) Acquire(ctx context.Context, timeout time.Duration) (bool, error) {
    deadline := time.Now().Add(timeout)

    for time.Now().Before(deadline) {
        ok, err := l.client.SetNX(ctx, l.key, l.value, l.ttl).Result()
        if err != nil {
            return false, err
        }
        if ok {
            return true, nil  // lock zauzet
        }

        // Čekaj malo prije ponovnog pokušaja
        select {
        case <-ctx.Done():
            return false, ctx.Err()
        case <-time.After(50 * time.Millisecond):
        }
    }

    return false, nil  // timeout
}

// Release — otpusti lock SAMO ako ga mi držimo (atomarni Lua script)
func (l *RedisLock) Release(ctx context.Context) error {
    // Lua script: provjeri value, pa obriši — atomarno
    script := redis.NewScript(`
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
    `)
    return script.Run(ctx, l.client, []string{l.key}, l.value).Err()
}
```

Zašto `value` = UUID: bez provjere UUID, Pod A bi mogao otpustiti lock koji drži Pod B (ako je Pod A-ov lock istekao zbog TTL-a).

---

## Upotreba u praksi

```go
func (s *OrderService) ProcessPayment(ctx context.Context, orderID string) error {
    lock := NewLock(s.redis, "payment:"+orderID, 30*time.Second)

    // Pokušaj zauzeti lock, čekaj max 5s
    acquired, err := lock.Acquire(ctx, 5*time.Second)
    if err != nil {
        return fmt.Errorf("lock acquire: %w", err)
    }
    if !acquired {
        return ErrPaymentAlreadyInProgress
    }
    defer lock.Release(ctx)

    // Samo jedan Pod dolazi ovdje za isti orderID
    return s.doProcessPayment(ctx, orderID)
}
```

---

## TTL — ključna odluka

```
TTL prekratak → lock istekne dok operacija još traje → drugi Pod ulazi
TTL predugačak → ako Pod crashne, lock blokira sve dok ne istekne
```

Pravilo: TTL = 2-3× očekivano trajanje operacije.

Za dugotrajne operacije: extend lock periodično ("heartbeat"):

```go
func (l *RedisLock) ExtendTTL(ctx context.Context) error {
    // EXPIRE samo ako mi držimo lock (isti Lua pattern)
    script := redis.NewScript(`
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
    `)
    return script.Run(ctx, l.client, []string{l.key}, l.value,
        int(l.ttl.Seconds())).Err()
}

// U background goroutini dok operacija traje
func withHeartbeat(ctx context.Context, lock *RedisLock, fn func() error) error {
    heartbeatCtx, stop := context.WithCancel(ctx)
    defer stop()

    go func() {
        ticker := time.NewTicker(l.ttl / 3)
        defer ticker.Stop()
        for {
            select {
            case <-heartbeatCtx.Done():
                return
            case <-ticker.C:
                lock.ExtendTTL(heartbeatCtx)
            }
        }
    }()

    return fn()
}
```

---

## Redsync — production-ready library

Za produkciju koristiš `go-redsync/redsync` umjesto ručne implementacije:

```go
import (
    "github.com/go-redsync/redsync/v4"
    "github.com/go-redsync/redsync/v4/redis/goredis/v9"
)

func NewOrderService(redisClient *redis.Client) *OrderService {
    pool := goredislib.NewPool(redisClient)
    rs := redsync.New(pool)

    return &OrderService{
        redis: redisClient,
        rs:    rs,
    }
}

func (s *OrderService) ProcessPayment(ctx context.Context, orderID string) error {
    mutex := s.rs.NewMutex("payment:"+orderID,
        redsync.WithExpiry(30*time.Second),
        redsync.WithTries(10),
        redsync.WithRetryDelay(100*time.Millisecond),
    )

    if err := mutex.LockContext(ctx); err != nil {
        return fmt.Errorf("lock: %w", err)
    }
    defer mutex.UnlockContext(ctx)

    return s.doProcessPayment(ctx, orderID)
}
```

Redsync implementira Redlock algoritam — koristi quorum na više Redis instanci za otpornost na failover.

---

## Kada koristiti distributed lock

Koristiti:
- Sprečavanje duplikatne obrade: samo jedan worker obrađuje isti order
- Cron job na više instanci: samo jedan Pod pokrene midnight job
- Rate limiting per resource: max N operacija na istom accountu

Ne koristiti:
- Umjesto database transakcija — DB ima MVCC, lock + query nije atomarno
- Za dulje od nekoliko sekundi bez heartbeat-a
- Kao zamjena za idempotency — lock + idempotency su komplementarni, ne zamjena

---

## Veza sa project-A

Cron job za generisanje invoica u go-service treba lock:

```go
// K8s CronJob koji se pokreće svakih sat — ali samo jedan Pod smije raditi
func (s *InvoiceService) GenerateMonthlyInvoices(ctx context.Context) error {
    lock := s.rs.NewMutex("cron:monthly-invoices",
        redsync.WithExpiry(10*time.Minute),
    )

    if err := lock.LockContext(ctx); err != nil {
        // Drugi Pod već radi — normalan slučaj, ne greška
        s.logger.Info("monthly invoices already running on another instance")
        return nil
    }
    defer lock.UnlockContext(ctx)

    return s.generateAll(ctx)
}
```
