# Quick Reference — Go Runtime Deep Dive

## sync.Pool usage pattern
```go
var pool = sync.Pool{New: func() any { return &MyObj{} }}
obj := pool.Get().(*MyObj)
obj.Reset()         // always reset before use
defer pool.Put(obj)
// WARNING: pool items may be GC'd — don't store state you must keep
```

## Escape analysis flags
```
go build -gcflags="-m" .    // shows: "moved to heap: x"
go build -gcflags="-m=2" .  // verbose with reason
```

## Memory alignment — field ordering matters
```go
// Put largest fields first to minimize padding
type Optimal struct {
    a int64  // 8
    b int64  // 8
    c int32  // 4
    d int16  // 2
    e int8   // 1
    // 1 byte padding to align to 8
}
```

## False sharing fix
```go
type Counter struct {
    v   int64
    _   [56]byte  // pad to cache line boundary (64 bytes total)
}
```

## Preemption
```
// Go 1.14+: asynchronous preemption (signal-based)
// Goroutines can be preempted even in tight CPU loops
// Prior to 1.14: only at function call sites
```

## GC phases
```
Mark (concurrent) → Mark termination (STW) → Sweep (concurrent)
STW = stop-the-world pause (microseconds in modern Go)
```
