# Quick Reference — Go Runtime Internals

## GMP model
```
G = goroutine (user-space, lightweight ~2KB stack)
M = OS thread (managed by runtime)
P = processor context (GOMAXPROCS count, default=nCPU)
```

## GOMAXPROCS
```go
runtime.GOMAXPROCS(n)   // set P count
GOMAXPROCS=1            // useful to eliminate scheduling noise in benchmarks
```

## Escape analysis
```
go build -gcflags="-m" ./...    // see what escapes to heap
go build -gcflags="-m -m" ./... // verbose (shows reason)
```

## GC tuning
```
GOGC=100      // default: GC when heap 2× live data
GOGC=200      // less frequent GC, more memory
GOMEMLIMIT=512MiB  // Go 1.19+: memory ceiling
```

## Execution trace
```go
import "runtime/trace"
trace.Start(f); defer trace.Stop()
go tool trace trace.out
```

## Blocking categories
```
// Cooperatively yields to scheduler:
channel ops, syscalls, runtime.Gosched(), time.Sleep()
// Does NOT yield (burns P):
pure CPU loops, math-heavy code
```
