# Unit 1 — Scope: From Queue to Log — Event Backbone

## Concept

This module builds an event-driven order processing pipeline. The producer is an order-service that publishes `OrderCreated` events to Kafka. The consumer is an inventory-service that processes them. By the end you have working segmentio/kafka-go producers and consumers, consumer group rebalancing, and the outbox pattern for reliable cross-service publication.

## Code

```go
// What you will build across this module:
//
// order-service (producer)
//   - Creates an order in the DB
//   - Writes an OrderCreated event to an outbox table in the same transaction
//   - A background poller reads the outbox and publishes to Kafka
//
// inventory-service (consumer)
//   - Consumer group: reads OrderCreated events from Kafka
//   - Checks inbox table before processing (idempotent)
//   - Commits offset only after successful processing
//
// By end of module the following holds:
//   - Order and event are always consistent (both saved or neither)
//   - Two consumer instances share the partition load
//   - Restarting a consumer replays only uncommitted messages

package main // placeholder — each unit fills this in
```

## Exercise

**Build:** Nothing yet. Sketch on paper: what happens if order-service inserts an order to DB, then crashes before publishing to Kafka?
**Input:** Your reasoning about the gap between DB write and Kafka publish
**Output:** Identify the consistency problem. Write: which approach fixes it — (a) publish to Kafka then write to DB, (b) write to DB then publish to Kafka, (c) write both in one transaction using an outbox table
**Acceptance:** You can explain why (a) and (b) both have failure windows but (c) does not

## Interview

- What is the fundamental difference between a message queue and a Kafka topic?
- Why does Kafka guarantee ordering within a partition but not across partitions?
- What is the outbox pattern and which problem does it solve?
