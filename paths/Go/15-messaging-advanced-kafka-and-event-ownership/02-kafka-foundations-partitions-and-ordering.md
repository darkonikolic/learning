# Unit 2 — Kafka Foundations: Partitions and Ordering

## Concept

A Kafka topic is an append-only log split into partitions. Ordering is guaranteed within a partition, not across partitions. Messages with the same partition key always go to the same partition. Use a consistent partition key (e.g., orderID or userID) when order matters for that entity. A message published without a key is round-robined across partitions.

## Code

```go
package main

import (
	"context"
	"fmt"
	"github.com/segmentio/kafka-go"
)

func newWriter(brokers []string, topic string) *kafka.Writer {
	return &kafka.Writer{
		Addr:     kafka.TCP(brokers...),
		Topic:    topic,
		Balancer: &kafka.Hash{}, // consistent: same key → same partition
	}
}

func publishOrder(ctx context.Context, w *kafka.Writer, userID, orderID string, payload []byte) error {
	return w.WriteMessages(ctx, kafka.Message{
		Key:   []byte(userID), // partition key: all orders for same user go to same partition
		Value: payload,
		Headers: []kafka.Header{
			{Key: "orderID", Value: []byte(orderID)},
		},
	})
}

func readPartition(brokers []string, topic string, partition int) {
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:   brokers,
		Topic:     topic,
		Partition: partition,
		MinBytes:  1,
		MaxBytes:  10e6,
	})
	defer r.Close()

	for {
		m, err := r.ReadMessage(context.Background())
		if err != nil {
			break
		}
		fmt.Printf("partition=%d offset=%d key=%s\n", m.Partition, m.Offset, m.Key)
	}
}
```

## Exercise

**Build:** Publish 10 orders for 3 users (key = userID, e.g., "user-1", "user-2", "user-3"). Read them back directly from each partition.
**Input:** 10 messages with keys distributed across 3 users on a topic with 3 partitions
**Output:** Print each message with its partition number and offset. Show that all messages for "user-1" are in the same partition.
**Acceptance:** For each userID, all messages land in one partition. Within each partition, messages appear in the order they were published.

## Interview

- A topic has 3 partitions. Two messages have the same key. Are they guaranteed to be in the same partition?
- Can you reorder messages within a partition by replaying from an earlier offset?
- What happens to ordering guarantees if you increase partition count on an existing topic?
