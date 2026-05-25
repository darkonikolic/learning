# Unit 4 — Choosing Serialization: Decision Matrix

## Concept

The choice between JSON and protobuf is about audience and contract enforcement, not performance. External consumers (browsers, mobile apps, third parties) need JSON — it is self-describing, requires no tooling, and is debuggable with any HTTP client. Internal services need protobuf — the schema is the contract, type mismatches fail at compile time, and the encoding is compact. Never choose based on raw speed alone. A gateway service translates between the two: proto internally, JSON externally.

## Code

```go
// Serialization decision matrix
//
// | Scenario                         | Format    | Reason                                      |
// |----------------------------------|-----------|---------------------------------------------|
// | Public REST API (browsers/mobile)| JSON      | Self-describing, no client tooling needed   |
// | Internal gRPC service call       | Protobuf  | Type-safe, compact, schema-enforced         |
// | Kafka event payload (internal)   | Protobuf  | Schema registry, compact, versioned         |
// | Kafka event payload (external)   | JSON      | Consumer has no .proto files                |
// | Stored DB blob                   | Protobuf  | Compact, schema evolution via field numbers |
// | Log/audit trail                  | JSON      | Must be human-readable without tooling      |

package main

import (
	"encoding/json"
	"net/http"

	"google.golang.org/protobuf/proto"

	pb "github.com/example/orders/gen/orderpb"
)

// Gateway: receives JSON from client, calls internal service via proto.
func orderGatewayHandler(w http.ResponseWriter, r *http.Request) {
	// 1. Decode external JSON request
	var req struct {
		CustomerID string   `json:"customer_id"`
		ItemIDs    []string `json:"item_ids"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}

	// 2. Translate to internal proto and call downstream service
	pbReq := &pb.CreateOrderRequest{
		CustomerId: req.CustomerID,
		ItemIds:    req.ItemIDs,
	}
	pbBytes, _ := proto.Marshal(pbReq)
	_ = pbBytes // send to internal gRPC service

	// 3. Translate proto response back to JSON for the client
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "created"})
}
```

## Exercise

**Build:** A written serialization strategy (in comments in a `.go` file) for three systems, plus working gateway translation code.
**Input:** Three scenarios: (a) public REST API for a mobile app, (b) internal order→inventory service call over gRPC, (c) event payload published to Kafka for internal consumers.
**Output:** For each scenario: chosen format, one-sentence justification, and any trade-offs. Plus a gateway function that decodes a JSON `PlaceOrderRequest` and encodes it as a proto `InternalOrderRequest`.
**Acceptance:** Justifications address audience, not just performance. Gateway compiles and the translation is lossless — all fields from JSON appear in the proto output.

## Interview

- A teammate says "just use JSON everywhere, it's simpler." What are the concrete costs at scale?
- When would you store event payloads in Kafka as JSON instead of protobuf?
- What does a gateway service's job look like when it sits between a JSON public API and a proto internal service?
