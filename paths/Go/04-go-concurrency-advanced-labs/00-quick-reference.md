---
# Quick Reference — Advanced Concurrency

## Mutex
```go
var mu sync.Mutex
mu.Lock()
defer mu.Unlock()
// critical section
```

## sync.Map (concurrent-safe, no generics)
```go
var m sync.Map
m.Store("key", value)
v, ok := m.Load("key")
m.LoadOrStore("key", defaultVal)
m.Range(func(k, v any) bool { ...; return true })
```

## errgroup (golang.org/x/sync/errgroup)
```go
g, ctx := errgroup.WithContext(ctx)
g.Go(func() error { return doWork(ctx) })
if err := g.Wait(); err != nil { ... }
```

## context
```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
// check: ctx.Done(), ctx.Err()
```

## Race detector
```sh
go test -race ./...
go build -race ./cmd/app   # run binary with race detection
```

## Worker pool shape
```go
jobs := make(chan Job, 100)
for i := 0; i < numWorkers; i++ {
    go worker(ctx, jobs)
}
```
