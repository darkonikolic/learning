# Unit 3 — Receivers: behaviour without inheritance

## Learning outcome

You attach behaviour with **`func (receiver) Method()`** idioms while consciously choosing **`(u User)`** vs **`(u *User)`** receivers—because Go has **methods**, not subclasses.

Interpret:

```go
func (u User) FullName() string
```

Understand **copy vs mutation**, **allocation vs aliasing**, and how receiver choice interacts with later **interface satisfaction**.

## Value receiver vs pointer receiver (rules of thumb)

Use **pointer receivers** (`*T`) when the method meaningfully mutates `T`, when `T` is large and copying is wasteful each call, when you must preserve identity across callers, or when `T` carries mutexes/maps/slices backing shared state—consistency drives pointer choice far more often than micro-optimization.

Prefer **value receivers** only when semantics are immutable snapshot operations on small POD-like structs—or when you consciously want intentional copying for safety (rare discipline, not laziness).

## Practice (`Cart`)

Model a shopping-cart-like structure with behaviours:

- `Add(item …)`
- `Remove(id …)`

Select receivers deliberately; document mismatches (“if I mistakenly used value receiver here, duplication bugs appear like X”).

## Lab

Produce a cheat-sheet paragraph **you would say in interview**:

- pointer receiver rationale,
- value receiver pitfalls on mutators,
- when interface satisfaction subtly forces pointer-ness.

## Interview prompts

- receiver dispatch mechanism (non-OO mental model),
- copying slices/maps inside structs on value receivers,
- nil-pointer receiver edge cases (`var p *Cart` then calling method—know what breaks conceptually vs what oddly works depending on receiver type).
