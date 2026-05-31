# 02 — Concurrency patterns

## errgroup — grupe goroutina s error propagacijom

`sync.WaitGroup` ne propagira greške. `errgroup` rješava to: čeka sve goroutine, vraća prvu grešku, i opciono cancel-uje ostale kada jedna fail-uje.

```go
import "golang.org/x/sync/errgroup"

func (s *OrderService) enrichOrder(ctx context.Context, orderID string) (*EnrichedOrder, error) {
    g, ctx := errgroup.WithContext(ctx)

    var user *User
    var inventory *Inventory
    var pricing *Pricing

    // Tri paralelna poziva — svaki u svojoj goroutini
    g.Go(func() error {
        var err error
        user, err = s.userSvc.Get(ctx, orderID)
        return err
    })

    g.Go(func() error {
        var err error
        inventory, err = s.inventorySvc.Check(ctx, orderID)
        return err
    })

    g.Go(func() error {
        var err error
        pricing, err = s.pricingSvc.Calculate(ctx, orderID)
        return err
    })

    // Čeka sve goroutine; ako jedna vrati grešku, ctx se cancel-uje
    // i ostale goroutine trebaju poštovati ctx.Done()
    if err := g.Wait(); err != nil {
        return nil, err
    }

    return &EnrichedOrder{User: user, Inventory: inventory, Pricing: pricing}, nil
}
```

Bez errgroup-a, isti kod bi bio 30+ linija `WaitGroup`, mutex-a i error channel-a.

---

## Semaphore — ograniči paralelizam

Kada imaš 1000 zadataka ali hoćeš max 10 paralelnih (npr. zbog DB connection pool-a):

```go
import "golang.org/x/sync/semaphore"

func processOrders(ctx context.Context, orders []Order) error {
    const maxConcurrent = 10
    sem := semaphore.NewWeighted(maxConcurrent)

    g, ctx := errgroup.WithContext(ctx)

    for _, order := range orders {
        order := order  // capture loop variable

        // Zauzmi jedan slot (blokira ako je puno)
        if err := sem.Acquire(ctx, 1); err != nil {
            return err  // ctx cancelled
        }

        g.Go(func() error {
            defer sem.Release(1)  // oslobodi slot kad završi
            return processOrder(ctx, order)
        })
    }

    return g.Wait()
}
```

Alternativa za jednostavnije slučajeve — buffered channel kao semaphore:

```go
sem := make(chan struct{}, 10)  // max 10 paralelnih

for _, order := range orders {
    sem <- struct{}{}  // zauzmi
    go func(o Order) {
        defer func() { <-sem }()  // oslobodi
        processOrder(ctx, o)
    }(order)
}
```

---

## Fan-out / Fan-in

Fan-out: jedan producer, više consumera koji obrađuju paralelno.
Fan-in: više producera, jedan consumer koji skuplja rezultate.

```go
// Fan-out: distribuiraj posao na N workera
func fanOut(ctx context.Context, jobs <-chan Job, numWorkers int) <-chan Result {
    results := make(chan Result, numWorkers)

    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    return
                case results <- process(ctx, job):
                }
            }
        }()
    }

    // Zatvori results kada svi workeri završe
    go func() {
        wg.Wait()
        close(results)
    }()

    return results
}

// Fan-in: skupi rezultate iz više kanala u jedan
func fanIn(ctx context.Context, channels ...<-chan Result) <-chan Result {
    merged := make(chan Result)
    var wg sync.WaitGroup

    output := func(ch <-chan Result) {
        defer wg.Done()
        for r := range ch {
            select {
            case merged <- r:
            case <-ctx.Done():
                return
            }
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go output(ch)
    }

    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}
```

---

## Pipeline pattern

Svaka faza prima channel, vraća channel. Faze se lako mijenjaju i testiraju zasebno.

```go
// Pipeline: fetch → validate → enrich → save
func run(ctx context.Context, orderIDs []string) error {
    // Faza 1: generiraj IDs
    ids := generate(ctx, orderIDs)

    // Faza 2: dohvati iz baze (paralelno)
    orders := fetch(ctx, ids, 5)

    // Faza 3: validiraj
    validated := validate(ctx, orders)

    // Faza 4: spremi u S3
    return save(ctx, validated)
}

func fetch(ctx context.Context, ids <-chan string, workers int) <-chan Order {
    out := make(chan Order, workers)

    go func() {
        defer close(out)
        sem := semaphore.NewWeighted(int64(workers))

        for id := range ids {
            if err := sem.Acquire(ctx, 1); err != nil {
                return
            }
            id := id
            go func() {
                defer sem.Release(1)
                order, err := db.GetOrder(ctx, id)
                if err == nil {
                    select {
                    case out <- order:
                    case <-ctx.Done():
                    }
                }
            }()
        }
        // Čekaj da svi završe
        sem.Acquire(ctx, int64(workers))
    }()

    return out
}
```

---

## sync.Once — inicijalizacija točno jednom

```go
type DBPool struct {
    once sync.Once
    pool *sql.DB
}

func (d *DBPool) Get() *sql.DB {
    d.once.Do(func() {
        var err error
        d.pool, err = sql.Open("mysql", dsn)
        if err != nil {
            panic(err)  // inicijalizacija se neće ponoviti — panic je ispravan
        }
    })
    return d.pool
}
```

`sync.Once` garantuje da se funkcija pozove točno jednom, čak i ako se `Get()` pozove konkurentno iz 1000 goroutina.

---

## sync.Map — concurrent-safe mapa

```go
// Standardna mapa nije thread-safe:
var cache map[string]string  // RACE CONDITION bez mutex-a

// sync.Map je thread-safe, ali samo za specifične use case:
// - mnogo čitanja, malo pisanja
// - isti ključ se ne ažurira često
var cache sync.Map

// Pisanje
cache.Store("key", "value")

// Čitanje
if val, ok := cache.Load("key"); ok {
    fmt.Println(val.(string))
}

// Load ili Store (atomarno)
actual, loaded := cache.LoadOrStore("key", "default")

// Brisanje
cache.Delete("key")

// Iteracija
cache.Range(func(k, v interface{}) bool {
    fmt.Printf("%s: %s\n", k, v)
    return true  // false = stop
})
```

Za high-contention slučajeve (često pisanje istog ključa), mutex + standardna mapa je brži od `sync.Map`.

---

## Graceful shutdown s kontekstom

```go
func main() {
    // ctx se cancel-uje na SIGTERM ili SIGINT (Ctrl+C)
    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
    defer stop()

    srv := &http.Server{Addr: ":8080", Handler: router}

    // Pokreni server u goroutini
    g, ctx := errgroup.WithContext(ctx)
    g.Go(func() error {
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            return err
        }
        return nil
    })

    // Čekaj signal za shutdown
    g.Go(func() error {
        <-ctx.Done()

        // Daj 30s za in-flight zahtjeve da završe
        shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()

        return srv.Shutdown(shutdownCtx)
    })

    if err := g.Wait(); err != nil {
        log.Fatal(err)
    }
}
```

Kubernetes šalje SIGTERM kada hoće ugasiti Pod. Bez graceful shutdown-a, in-flight zahtjevi dobijaju connection reset umjesto normalnog odgovora.

---

## Veza sa project-A

U go-service, enrichOrder pattern s errgroup-om zamjenjuje sekvencijalne DB pozive:

```
// Sekvencijalno: 3 × 50ms = 150ms
user := getUser(ctx, id)       // 50ms
inventory := getInventory(...)  // 50ms
pricing := getPricing(...)      // 50ms

// Paralelno s errgroup: ~50ms (najsporiji određuje ukupno)
```

Semaphore kontrolira broj paralelnih DB konekcija — sprečava connection pool exhaustion pri burst prometu.
