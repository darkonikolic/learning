# Unit 4 — Pointer Thinking and Sharing Semantics

## Concept

`&x` takes the address of `x` — it gives you a pointer. `*p` dereferences a pointer — it gives you the value it points to. Passing a pointer to a function means both the caller and the function see the same memory: any change the function makes is visible to the caller. Passing a value means the function gets a copy — changes stay local. Nil pointer dereference is the classic Go panic — always guard pointer inputs before using them.

## Code

```go
package main

import (
	"errors"
	"fmt"
)

type Product struct {
	ID    int
	Name  string
	Price float64
}

// UpdatePrice mutates the product in-place. The caller's product is changed.
func UpdatePrice(p *Product, newPrice float64) error {
	if p == nil {
		return errors.New("UpdatePrice: nil product")
	}
	if newPrice <= 0 {
		return fmt.Errorf("UpdatePrice: price must be positive, got %g", newPrice)
	}
	p.Price = newPrice
	return nil
}

// ApplyDiscount takes a value — it works on a copy and returns the discounted price.
// The original product is not changed.
func ApplyDiscount(p Product, pct float64) float64 {
	p.Price = p.Price * (1 - pct/100) // mutates local copy only
	return p.Price
}

func main() {
	// Pattern 1: pointer passed — mutation is visible to caller.
	product := Product{ID: 1, Name: "Widget", Price: 10.00}
	if err := UpdatePrice(&product, 12.50); err != nil {
		fmt.Println("error:", err)
	}
	fmt.Printf("after UpdatePrice: $%.2f\n", product.Price) // 12.50 — original changed

	// Pattern 2: value passed — caller's product is unchanged.
	discounted := ApplyDiscount(product, 10)
	fmt.Printf("discounted price: $%.2f\n", discounted)    // 11.25
	fmt.Printf("original unchanged: $%.2f\n", product.Price) // still 12.50

	// Pattern 3: nil guard fires.
	var nilProduct *Product
	if err := UpdatePrice(nilProduct, 5.00); err != nil {
		fmt.Println("nil guard caught:", err)
	}

	// Pattern 4: range-variable address trap — common bug in loops.
	products := []Product{{1, "A", 1.0}, {2, "B", 2.0}, {3, "C", 3.0}}
	ptrs := make([]*Product, len(products))
	for i := range products {
		ptrs[i] = &products[i] // correct: address of slice element
		// WRONG: ptrs[i] = &p  (in a range p loop) — all ptrs would point to the same loop variable
	}
	ptrs[0].Name = "Alpha"
	fmt.Println("slice element updated:", products[0].Name) // Alpha
}
```

## Exercise

**Build:** Write `UpdatePrice(p *Product, newPrice float64) error` that returns an error if `p` is nil or `newPrice <= 0`, otherwise sets `p.Price`. Also write `PriceWithTax(p Product, taxPct float64) float64` that returns the taxed price without modifying the original.

**Input:** One valid product, call `UpdatePrice` on it, then call `PriceWithTax` on the updated product.

**Output:** `UpdatePrice` modifies the original. `PriceWithTax` returns a number but the product's price is unchanged afterward.

**Acceptance:** Write tests for: nil pointer returns error, invalid price returns error, valid update modifies in place, `PriceWithTax` does not change `p.Price`. Run `go test ./...`.

## Interview

- What is the difference between passing `Product` and `*Product` to a function?
- Why does `for _, p := range products { ptrs = append(ptrs, &p) }` produce unexpected results?
- When would you return `*Product` from a function versus returning `Product`?
