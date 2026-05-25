# Quick Reference — Kafka & Event Ownership

## Producer (segmentio/kafka-go)
```go
w := &kafka.Writer{
    Addr:     kafka.TCP("localhost:9092"),
    Topic:    "orders",
    Balancer: &kafka.Hash{},  // consistent partition by key
}
w.WriteMessages(ctx, kafka.Message{Key: []byte(orderID), Value: payload})
```

## Consumer with group
```go
r := kafka.NewReader(kafka.ReaderConfig{
    Brokers: []string{"localhost:9092"},
    GroupID: "service-name",
    Topic:   "orders",
})
msg, _ := r.FetchMessage(ctx)
// process...
r.CommitMessages(ctx, msg)  // AFTER processing — at-least-once
```

## Ordering guarantee
```
// Within partition: guaranteed
// Across partitions: NO guarantee
// Use consistent key (userID, orderID) for per-entity ordering
```

## Delivery semantics
```
at-most-once:   commit before processing (can lose)
at-least-once:  commit after processing (can duplicate) ← default choice
exactly-once:   transactions on both ends (complex, Kafka-specific)
```

## Patterns
```
Outbox: write event to DB table in same TX as data, poll+publish separately
Inbox:  store processed message IDs to detect and skip duplicates
```
