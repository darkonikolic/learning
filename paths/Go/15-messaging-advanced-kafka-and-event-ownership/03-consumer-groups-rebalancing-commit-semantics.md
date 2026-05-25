# Unit 3 — Consumer Groups: Rebalancing and Commit Semantics

## Concept

A consumer group is multiple consumers sharing the work of consuming a topic. Each partition is consumed by exactly one consumer in the group at a time. Commit the offset after processing, not before (at-least-once delivery). On restart, the consumer re-reads from the last committed offset — so you may see the last message again. Your processing must be idempotent to handle this safely.

## Code

```go
package main

import (
	"context"
	"fmt"
	"github.com/segmentio/kafka-go"
)

func newGroupReader(brokers []string, topic, groupID string) *kafka.Reader {
	return kafka.NewReader(kafka.ReaderConfig{
		Brokers:  brokers,
		Topic:    topic,
		GroupID:  groupID, // enables consumer group — auto-assigns partitions
		MinBytes: 1,
		MaxBytes: 10e6,
		// CommitInterval: 0 means manual commit
	})
}

func consumeWithManualCommit(ctx context.Context, r *kafka.Reader, process func(kafka.Message) error) error {
	for {
		// FetchMessage does NOT commit the offset.
		m, err := r.FetchMessage(ctx)
		if err != nil {
			return err
		}

		if err := process(m); err != nil {
			// Do not commit — message will be re-delivered on next FetchMessage.
			fmt.Printf("processing failed, not committing offset %d: %v\n", m.Offset, err)
			continue
		}

		// Commit only after successful processing.
		// On crash before this line, the message is re-delivered.
		if err := r.CommitMessages(ctx, m); err != nil {
			return fmt.Errorf("commit offset %d: %w", m.Offset, err)
		}
	}
}
```

## Exercise

**Build:** Start 2 consumers in the same group on a topic with 2 partitions. Publish 100 messages. Each consumer processes its assigned partition. Kill one consumer mid-run.
**Input:** 100 messages published to a 2-partition topic. Two readers with the same `GroupID`.
**Output:** Total messages processed across both consumers = 100. After killing one consumer, the surviving consumer picks up the orphaned partition and processes the remaining messages.
**Acceptance:** No message is skipped (total processed = 100). If your handler is idempotent, no message is double-processed after the rebalance.

## Interview

- What is the difference between `FetchMessage` and `ReadMessage` in kafka-go?
- If you crash after processing but before committing, what happens to that message?
- Can two consumers in the same group read the same partition simultaneously?
