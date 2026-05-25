# Unit 1 — JSON vs Protobuf: Where Each Belongs

## Concept

JSON is for external APIs — browsers, mobile clients, third-party integrations. It is human-readable, self-describing, and universally supported without tooling. Protobuf is for internal service-to-service communication. It is compact, schema-enforced, and generates typed code for both sides of the wire. Using JSON over internal gRPC loses type safety and the compact encoding. Exposing raw proto over a public HTTP API breaks discoverability — clients cannot inspect or document it without your `.proto` files.

## Code

```go
package main

import (
	"encoding/json"
	"fmt"
	"log"

	"google.golang.org/protobuf/proto"

	pb "github.com/example/orders/gen/orderpb"
)

// OrderJSON is the external API representation.
type OrderJSON struct {
	ID         string  `json:"id"`
	CustomerID string  `json:"customer_id"`
	Total      float64 `json:"total"`
	Status     string  `json:"status"`
}

func main() {
	// JSON encoding — for external consumers
	order := OrderJSON{
		ID:         "ord_123",
		CustomerID: "cust_456",
		Total:      99.99,
		Status:     "pending",
	}
	jsonBytes, err := json.Marshal(order)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("JSON  (%d bytes): %s\n", len(jsonBytes), jsonBytes)
	// JSON (67 bytes): {"id":"ord_123","customer_id":"cust_456","total":99.99,"status":"pending"}

	// Protobuf encoding — for internal services
	pbOrder := &pb.Order{
		Id:         "ord_123",
		CustomerId: "cust_456",
		Total:      99.99,
		Status:     "pending",
	}
	pbBytes, err := proto.Marshal(pbOrder)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Proto (%d bytes): binary, not human-readable\n", len(pbBytes))
	// Proto (~32 bytes): roughly 50% smaller, no field names transmitted
}
```

## Exercise

**Build:** An encoding comparison tool for an Order struct.
**Input:** A hardcoded order with 5 fields: id, customer_id, item count (int), total (float64), status.
**Output:** Two files written to disk — `order.json` and `order.pb` — plus a printed line: `JSON: 87 bytes | Proto: 38 bytes | Savings: 56%`.
**Acceptance:** Both files exist. `cat order.json` shows readable JSON. `cat order.pb` shows garbage binary. The savings percentage in the output is mathematically correct.

## Interview

- Why would you never expose a proto-only endpoint on a public REST API?
- If JSON is slower and larger than protobuf, why is it still the right choice for external APIs?
- A teammate wants to use `encoding/json` over an internal gRPC call "because it's easier to debug." What is the actual cost of that decision?
