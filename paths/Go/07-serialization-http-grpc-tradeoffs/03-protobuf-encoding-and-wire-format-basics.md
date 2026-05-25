# Unit 3 — Protobuf Encoding and Wire Format Basics

## Concept

Protobuf encodes each field as a tag-value pair where the tag is `(field_number << 3) | wire_type`. Field names never go over the wire — only numbers. This is why field numbers are sacred: if you change field number 1 from `id` to `user_id`, every existing encoded message in storage or in-flight will decode incorrectly. Adding a new optional field with a new number is safe — old decoders simply skip unknown field numbers, which gives forward compatibility for free.

## Code

```go
package main

import (
	"fmt"
	"log"

	"google.golang.org/protobuf/proto"

	pb "github.com/example/events/gen/eventpb"
)

// Proto definition for reference:
//
// message Event {
//   string id      = 1;
//   string type    = 2;
//   bytes  payload = 3;
//   int64  ts      = 4;
//   // string source = 5; // added later
// }

func main() {
	// Encode with original 4-field message
	original := &pb.Event{
		Id:      "evt_001",
		Type:    "order.created",
		Payload: []byte(`{"order_id":"ord_123"}`),
		Ts:      1716000000,
	}

	data, err := proto.Marshal(original)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Encoded: %d bytes\n", len(data))

	// Forward compatibility: decode old bytes with new struct that has Source field 5.
	// The new field will be zero-valued — old bytes decode cleanly.
	newMsg := &pb.EventV2{} // same fields 1-4 + Source at field 5
	if err := proto.Unmarshal(data, newMsg); err != nil {
		log.Fatal(err)
	}

	fmt.Printf("ID:     %s\n", newMsg.Id)      // "evt_001" — preserved
	fmt.Printf("Type:   %s\n", newMsg.Type)    // "order.created" — preserved
	fmt.Printf("Source: %s\n", newMsg.Source)  // "" — zero value, not an error
}
```

## Exercise

**Build:** A forward-compatibility demonstration.
**Input:** Define an `Event` proto with fields: `id` (1), `type` (2), `payload` (3), `timestamp` (4). Marshal one event to bytes and save to `event_v1.pb`.
**Output:** Define `EventV2` with the same 4 fields plus `source string = 5`. Unmarshal `event_v1.pb` bytes into an `EventV2`. Print all fields — the first 4 should have their values, `source` should be empty string.
**Acceptance:** No error on unmarshal. All original fields print correctly. Now try changing field 2's number from 2 to 6 in your V2 struct and unmarshal again — observe that `type` is now empty. Document why in a comment.

## Interview

- Why are protobuf field numbers immutable once a schema is in production?
- What happens when a new decoder receives a message with an unknown field number?
- Why can't you rely on field names for forward compatibility the way you might with JSON?
