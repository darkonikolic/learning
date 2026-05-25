# Quick Reference — Interview Gotchas

## Concurrency traps
// Loop var capture (pre-1.22): pass as arg or assign tc:=tc
// WaitGroup.Add BEFORE go, never inside goroutine
// Close channel from SENDER only, never receiver
// Closing nil channel panics; sending to closed channel panics

## Slice traps
b := a[1:3]              // shares backing array — writes affect original
copy(out, src)           // safe copy — use when you need independence
data[:10]                // 10MB backing array still held — GC can't free it

## Context traps
// Always defer cancel() immediately after WithTimeout/WithCancel
// Check ctx.Done() in long-running goroutines or they leak
// Don't store ctx in structs — pass as first parameter

## Interface nil trap
var p *MyStruct = nil
var i MyInterface = p   // i != nil (has type info)!
if i == nil { ... }     // NEVER true — check the concrete value instead

## defer gotcha
for i := 0; i < 5; i++ {
    defer fmt.Println(i) // all defers run at function exit, LIFO
}                         // prints: 4 3 2 1 0

## Common interview questions
1. What happens if you range over nil map? → safe, zero iterations
2. What happens if you read from nil channel? → blocks forever
3. Difference between make([]T,0) and var s []T? → both nil-safe, make allocates
4. When does append allocate? → when len == cap
