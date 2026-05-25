---
# Quick Reference — Concurrency Primitives

## Goroutine launch
```go
go func() { ... }()             // fire and forget (needs coordination)
var wg sync.WaitGroup
wg.Add(1)
go func() { defer wg.Done(); work() }()
wg.Wait()
```

## Channel directions
```go
ch := make(chan int)            // unbuffered — blocks until receiver ready
ch := make(chan int, 10)        // buffered — blocks only when full
func send(ch chan<- int) {}     // send-only
func recv(ch <-chan int) {}     // receive-only
```

## Select
```go
select {
case v := <-ch1: ...
case ch2 <- val: ...
case <-ctx.Done(): return ctx.Err()
default: ...                   // non-blocking
}
```

## Close and range
```go
close(ch)                      // signal no more sends
for v := range ch { ... }      // reads until closed
```

## Common mistakes
```go
// WRONG: goroutine outlives main
go func() { time.Sleep(1*time.Second); fmt.Println("done") }()
// main exits before goroutine prints — add wg.Wait()
```
