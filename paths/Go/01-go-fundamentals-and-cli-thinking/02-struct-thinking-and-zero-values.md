# Unit 2 — Struct Thinking and Zero Values

## Concept

Structs are Go's primary way to group related data. Every field has a zero value — `int` is 0, `string` is `""`, `bool` is `false`, pointer is `nil` — and Go initializes them automatically. This matters in production because it eliminates the "uninitialized variable" class of bugs common in other languages. Your job is to decide whether the zero value is valid for your type. If `Price == 0` means "free product" in your domain, fine. If it means "someone forgot to set a price", enforce that with a constructor.

## Code

```go
package main

import "fmt"

type Product struct {
	ID    int
	Name  string
	Price float64
	Stock int
}

// IsAvailable returns true if the product can be purchased.
func (p Product) IsAvailable() bool {
	return p.Stock > 0 && p.Price > 0
}

// NewProduct is a constructor used because Price=0 and Stock<0 are invalid.
func NewProduct(id int, name string, price float64, stock int) (Product, error) {
	if price <= 0 {
		return Product{}, fmt.Errorf("NewProduct: price must be positive, got %g", price)
	}
	if stock < 0 {
		return Product{}, fmt.Errorf("NewProduct: stock cannot be negative, got %d", stock)
	}
	return Product{ID: id, Name: name, Price: price, Stock: stock}, nil
}

func main() {
	var p Product // zero value: ID=0 Name="" Price=0 Stock=0
	fmt.Printf("zero value: %+v\n", p)
	fmt.Printf("zero IsAvailable: %v\n", p.IsAvailable()) // false — price is 0

	partial := Product{Name: "Widget"} // partial init — ID, Price, Stock are zero
	fmt.Printf("partial: %+v\n", partial)

	good, err := NewProduct(1, "Gadget", 9.99, 10)
	if err != nil {
		fmt.Println("error:", err)
	} else {
		fmt.Printf("valid product: %+v, available: %v\n", good, good.IsAvailable())
	}

	_, err = NewProduct(2, "Ghost", 0, 5) // price=0 rejected
	fmt.Println("invalid price:", err)

	_, err = NewProduct(3, "Broken", 5.0, -1) // negative stock rejected
	fmt.Println("invalid stock:", err)
}
```

## Exercise

**Build:** A `Product` struct with `ID int`, `Name string`, `Price float64`, `Stock int`. Add an `IsAvailable() bool` method (pointer receiver is fine) and a `NewProduct()` constructor that validates inputs.

**Input:** Call `NewProduct` with valid args, with `price=0`, and with `stock=-1`.

**Output:** Valid product prints with `IsAvailable: true`. Invalid inputs return descriptive errors, not panics.

**Acceptance:** Write a `_test.go` file with at least three test cases (valid, zero price, negative stock). Run `go test ./...` — all pass.

## Interview

- What is the zero value of a struct field, and why does Go guarantee it?
- When should you write a constructor function (`NewX`) versus letting callers use struct literals directly?
- What is the difference between `Product{}` and `var p Product`?
