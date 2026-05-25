# Unit 3 — Methods: Value and Pointer Receivers

## Concept

A method with a value receiver operates on a copy of the struct — the original is unchanged. A method with a pointer receiver operates on the original. The rule is simple: if the method modifies state, use a pointer receiver. If it only reads, a value receiver is fine — but be consistent within a type. Mixing receiver types on the same struct causes subtle bugs and prevents clean interface satisfaction.

## Code

```go
package main

import "fmt"

type CartItem struct {
	ProductID int
	Name      string
	Price     float64
	Quantity  int
}

type Cart struct {
	Items []CartItem
}

// AddItem uses a pointer receiver — it modifies the Cart's Items slice.
func (c *Cart) AddItem(item CartItem) {
	c.Items = append(c.Items, item)
}

// RemoveItem uses a pointer receiver — it modifies the Cart's Items slice.
func (c *Cart) RemoveItem(productID int) {
	filtered := c.Items[:0]
	for _, item := range c.Items {
		if item.ProductID != productID {
			filtered = append(filtered, item)
		}
	}
	c.Items = filtered
}

// Total uses a value receiver — it only reads data, never modifies.
func (c Cart) Total() float64 {
	var total float64
	for _, item := range c.Items {
		total += item.Price * float64(item.Quantity)
	}
	return total
}

// ItemCount uses a value receiver — read-only, consistent with Total.
func (c Cart) ItemCount() int {
	return len(c.Items)
}

func demonstrateValueReceiverBug() {
	// BUG: calling AddItem on a value copy does nothing to the original.
	cart := Cart{}
	valueCopy := cart                      // copies the struct
	valueCopy.Items = append(valueCopy.Items, CartItem{Name: "Ghost"})
	fmt.Println("original cart after value copy mutation:", cart.ItemCount()) // still 0
}

func main() {
	cart := &Cart{}

	cart.AddItem(CartItem{ProductID: 1, Name: "Widget", Price: 9.99, Quantity: 2})
	cart.AddItem(CartItem{ProductID: 2, Name: "Gadget", Price: 24.99, Quantity: 1})

	fmt.Printf("items: %d, total: $%.2f\n", cart.ItemCount(), cart.Total())

	cart.RemoveItem(1)
	fmt.Printf("after remove — items: %d, total: $%.2f\n", cart.ItemCount(), cart.Total())

	demonstrateValueReceiverBug()
}
```

## Exercise

**Build:** A `Cart` struct with `Items []CartItem`. Implement `AddItem(item CartItem)` (pointer receiver), `RemoveItem(productID int)` (pointer receiver), and `Total() float64` (value receiver).

**Input:** Add three items with different prices and quantities. Remove one. Compute total.

**Output:** Correct item count and dollar total after each operation.

**Acceptance:** Add a test that creates a `Cart` by value (not pointer), calls `AddItem` on it, and confirms the original cart is unaffected — demonstrating why the pointer receiver matters. Run `go test ./...`.

## Interview

- Why does calling a pointer receiver method on a value type sometimes fail to compile?
- A colleague wrote `Total()` with a pointer receiver. Is that wrong? What are the tradeoffs?
- What happens when you call a pointer receiver method on a nil pointer? When does it panic and when doesn't it?
