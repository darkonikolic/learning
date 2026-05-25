---
# Quick Reference — Go Fundamentals

## Struct
```go
type User struct {
    ID   int
    Name string
    Age  int // zero value: 0
}
u := User{}          // all zero values
u := User{Name: "A"} // partial init
```

## Value vs Pointer receiver
```go
func (u User) Name() string { ... }              // value — copy, safe for reads
func (u *User) SetName(s string) { u.Name = s }  // pointer — mutates
```

## Interface (implicit)
```go
type Stringer interface { String() string }
// any type with String() method satisfies it automatically
```

## Error handling
```go
func divide(a, b int) (int, error) {
    if b == 0 {
        return 0, fmt.Errorf("divide by zero")
    }
    return a / b, nil
}
result, err := divide(10, 0)
if err != nil {
    log.Fatal(err)
}
```

## Composition (not inheritance)
```go
type Admin struct {
    User        // embedded — promotes fields/methods
    Permissions []string
}
```

## Panic vs error
```go
// panic: unrecoverable bug (nil deref, index OOB)
// error: expected failure path — always return and check
```
