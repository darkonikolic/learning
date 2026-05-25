# Unit 5 — Interfaces: Implicit Contracts

## Concept

A type satisfies an interface simply by having the right methods — no `implements` keyword, no registration, no inheritance. If your type has a `Price() float64` method, it satisfies `Pricer`. This makes interfaces in Go decoupled by default: the interface and the concrete type can live in completely separate packages and never reference each other. The rule of thumb: accept interfaces, return concrete types. Keep interfaces small — one or two methods is better than ten.

## Code

```go
package main

import "fmt"

// Pricer is satisfied by any type that has a Price() float64 method.
type Pricer interface {
	Price() float64
}

// Product is a physical item with stock.
type Product struct {
	ID    int
	Name  string
	BasePrice float64
}

func (p Product) Price() float64 {
	return p.BasePrice
}

// DigitalProduct has no stock — it's a download.
type DigitalProduct struct {
	ID          int
	Name        string
	LicensePrice float64
}

func (d DigitalProduct) Price() float64 {
	return d.LicensePrice
}

// TotalCost accepts a slice of Pricer — works for any type that satisfies the interface.
// It does not know or care whether items are physical or digital.
func TotalCost(items []Pricer) float64 {
	var total float64
	for _, item := range items {
		total += item.Price()
	}
	return total
}

// Discount returns a new Pricer that applies a percentage discount.
// Uses an anonymous struct that satisfies Pricer without a named type.
func Discount(p Pricer, pct float64) Pricer {
	return discountedItem{original: p, pct: pct}
}

type discountedItem struct {
	original Pricer
	pct      float64
}

func (d discountedItem) Price() float64 {
	return d.original.Price() * (1 - d.pct/100)
}

func main() {
	physical := Product{ID: 1, Name: "Keyboard", BasePrice: 79.99}
	digital := DigitalProduct{ID: 2, Name: "License", LicensePrice: 29.99}

	// Both satisfy Pricer — can be used anywhere the interface is accepted.
	items := []Pricer{physical, digital}
	fmt.Printf("total: $%.2f\n", TotalCost(items)) // 109.98

	// Wrap with discount — still a Pricer, TotalCost still works.
	discounted := []Pricer{Discount(physical, 10), digital}
	fmt.Printf("after 10%% discount on keyboard: $%.2f\n", TotalCost(discounted)) // 101.99

	// Interface variable — runtime type is checked with type assertion.
	var p Pricer = physical
	if conc, ok := p.(Product); ok {
		fmt.Printf("concrete type: %s\n", conc.Name)
	}
}
```

## Exercise

**Build:** Define `type Pricer interface { Price() float64 }`. Create `Product` (physical, has `BasePrice`) and `DigitalProduct` (has `LicensePrice`). Both satisfy `Pricer`. Write `TotalCost(items []Pricer) float64`. Write a third type `BundledProduct` with two inner `Pricer` items — its `Price()` returns the sum of both at a 15% discount.

**Input:** A slice containing one `Product`, one `DigitalProduct`, and one `BundledProduct`.

**Output:** `TotalCost` returns the correct sum.

**Acceptance:** `TotalCost` must not use type switches or type assertions — it only calls `.Price()`. Run `go test ./...` with a test that checks the math.

## Interview

- How does Go's implicit interface satisfaction differ from Java's `implements`? What does it enable?
- Why is a large interface (10+ methods) a design smell in Go?
- What does "accept interfaces, return concrete types" mean, and why is it the dominant pattern?
