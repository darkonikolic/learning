# 01 — Context i cancellation

## Zašto context postoji

Go nema built-in mehanizam za "otkaži sve što radi ovaj zahtjev". Context rješava to: prenosi signal otkazivanja, deadline i request-scoped vrijednosti kroz cijeli call stack — od HTTP handlera do baze podataka.

```
HTTP handler
  │ ctx s deadlineom 5s
  ├─ service.ProcessOrder(ctx)
  │    ├─ db.QueryRow(ctx, ...)     ← baza poštuje cancel
  │    ├─ redis.Get(ctx, ...)       ← Redis poštuje cancel
  │    └─ paymentAPI.Charge(ctx)   ← HTTP client poštuje cancel
```

Ako korisnik zatvori konekciju ili istekne deadline — sve operacije ispod dobijaju cancel signal i odmah se gase. Bez context-a, upiti bi nastavili trošiti resurse za zahtjev koji niko više ne čeka.

---

## Četiri tipa context-a

```go
// 1. Root — koristi se samo kao polazna točka, ne direktno u handleru
ctx := context.Background()

// 2. WithCancel — ručno otkazivanje
ctx, cancel := context.WithCancel(parent)
defer cancel()  // uvijek defer cancel — sprečava goroutine leak

// 3. WithTimeout — automatski cancel nakon trajanja
ctx, cancel := context.WithTimeout(parent, 5*time.Second)
defer cancel()

// 4. WithDeadline — automatski cancel u apsolutnom vremenu
deadline := time.Now().Add(5 * time.Second)
ctx, cancel := context.WithDeadline(parent, deadline)
defer cancel()
```

`WithTimeout` je shorthand za `WithDeadline(time.Now().Add(d))`. U praksi koristiš `WithTimeout` jer je čitljiviji.

---

## Cancellation tree — kako se propagira

```
context.Background()
  └── WithTimeout(10s)          ← HTTP request deadline
        ├── WithCancel()        ← user klikne "cancel"
        │     └── db.Query()   ← otkaže se ako user cancela ILI timeout
        └── WithTimeout(3s)    ← kraći deadline za payment API
              └── http.Do()    ← otkaže se ako 3s prođe ili parent cancela
```

Child nikad ne može nadživjeti parenta. Ako parent cancel-uje, svi children automatski dobijaju cancel — nema eksplicitnog propagiranja.

---

## Goroutine leak — najčešća greška

```go
// POGREŠNO — goroutine leakuje ako se nikad ne pozove cancel
func handler(w http.ResponseWriter, r *http.Request) {
    ctx, _ := context.WithTimeout(r.Context(), 5*time.Second)
    //        ^ _ zanemarujemo cancel — leak!
    result, err := db.QueryRow(ctx, query)
}

// ISPRAVNO — uvijek defer cancel
func handler(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()  // ← poziva se kada handler završi, bez obzira na grešku
    result, err := db.QueryRow(ctx, query)
}
```

`defer cancel()` je cheap (samo zatvori interni kanal), ali bez njega context i svi njegovi resursi ostaju u memoriji do isteka deadlinea.

---

## Provjeri cancel u petlji

```go
func processItems(ctx context.Context, items []Item) error {
    for _, item := range items {
        // Provjeri cancel PRIJE svake iteracije
        select {
        case <-ctx.Done():
            return ctx.Err()  // context.Canceled ili context.DeadlineExceeded
        default:
        }

        if err := processItem(ctx, item); err != nil {
            return err
        }
    }
    return nil
}
```

`ctx.Done()` je channel koji se zatvori kada context istekne ili bude otkazan. `ctx.Err()` vraća razlog: `context.Canceled` ili `context.DeadlineExceeded`.

---

## Context values — samo request-scoped podaci

```go
type contextKey string

const (
    requestIDKey contextKey = "request_id"
    userIDKey    contextKey = "user_id"
)

// Postavi u middleware
func requestIDMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        id := uuid.New().String()
        ctx := context.WithValue(r.Context(), requestIDKey, id)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Čitaj duboko u call stacku
func (s *Service) Process(ctx context.Context) {
    requestID, ok := ctx.Value(requestIDKey).(string)
    if !ok {
        requestID = "unknown"
    }
    s.logger.Info("processing", "request_id", requestID)
}
```

**Ne stavljaj u context:** database konekcije, konfiguracije, dependency-je. Context nije dependency injection. Koristi ga samo za: request ID, user ID, trace ID, auth token — stvari koje su specifične za jedan zahtjev.

---

## Race detector

Go ima ugrađen race detector koji detektuje concurrent read/write na dijeljenu memoriju bez sinhronizacije.

```bash
# Pokretanje testova s race detectorom
go test -race ./...

# Pokretanje aplikacije s race detectorom (dev/CI, ne prod — 5-10x sporije)
go run -race main.go

# Build s race detectorom
go build -race -o myapp-race .
```

### Primjer race conditiona koji detector hvata

```go
// PROBLEM — race condition
var counter int

func increment() {
    counter++  // read + write, nije atomarno
}

func main() {
    for i := 0; i < 1000; i++ {
        go increment()  // 1000 goroutina piše counter bez lock-a
    }
}
```

```
==================
WARNING: DATA RACE
Write at 0x00c000018090 by goroutine 7:
  main.increment()
      /app/main.go:6 +0x2c

Previous write at 0x00c000018090 by goroutine 6:
  main.increment()
      /app/main.go:6 +0x2c
==================
```

### Rješenje

```go
// Opcija 1: sync/atomic
var counter atomic.Int64
counter.Add(1)

// Opcija 2: mutex
var mu sync.Mutex
var counter int

func increment() {
    mu.Lock()
    defer mu.Unlock()
    counter++
}

// Opcija 3: channel (kada trebaš i prenijeti vrijednost)
counterCh := make(chan int, 1)
counterCh <- 0

go func() {
    val := <-counterCh
    counterCh <- val + 1
}()
```

### Race detector u CI

```yaml
# .gitlab-ci.yml
test:race:
  stage: test
  script:
    - go test -race -count=1 ./...
  variables:
    GORACE: "halt_on_error=1"  # Fail odmah na prvom race-u
```

Race detector mora biti u CI — lokalni testovi ne pokrivaju sve moguće scheduling scenarije.

---

## Deadline propagacija kroz HTTP klijente

```go
// POGREŠNO — ne prenosi context deadline
func callPaymentAPI(amount float64) (*PaymentResponse, error) {
    resp, err := http.Get("https://payment.api/charge")  // ignoriše context
    ...
}

// ISPRAVNO — HTTP klijent poštuje context deadline/cancel
func callPaymentAPI(ctx context.Context, amount float64) (*PaymentResponse, error) {
    req, err := http.NewRequestWithContext(ctx, "POST", "https://payment.api/charge", body)
    if err != nil {
        return nil, err
    }

    resp, err := http.DefaultClient.Do(req)
    ...
}
```

`http.NewRequestWithContext` je jedini način da HTTP klijent poštuje context. `http.Get` i `http.Post` ne prenose context.

---

## Veza sa project-A

U go-service, svaki gRPC handler dobija context od grpc servera koji sadrži connection deadline. Ten context propagiraj u sve downstream pozive:

```go
func (s *OrderService) CreateOrder(ctx context.Context, req *pb.CreateOrderRequest) (*pb.CreateOrderResponse, error) {
    // ctx dolazi od gRPC servera s request deadlineom

    // Kraći timeout za DB upit unutar ukupnog deadlinea
    dbCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
    defer cancel()

    order, err := s.db.CreateOrder(dbCtx, req)
    if err != nil {
        if errors.Is(err, context.DeadlineExceeded) {
            return nil, status.Error(codes.DeadlineExceeded, "db timeout")
        }
        return nil, status.Error(codes.Internal, err.Error())
    }
    return &pb.CreateOrderResponse{Order: order}, nil
}
```
