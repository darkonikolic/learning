# Unit 3 — Consumer groups & partition assignment

Kafka **consumer groups** coordinate who reads partitions:

```
group.members assign partitions ⇒ each partition processed ~once per consumer in steady state (cooperative concurrency model)
```

## Learning anchors

Understand **partition rebalance storms** briefly: scaling consumers or rolling deploys reshuffles assignments—paired with **incorrect offset commit strategies** duplicates or gaps amplify.

Enumerate **delivery honesty** interplay:

- **at-least-once processing** paired with dedupe/idempotency (see inbox pattern next area block),
- “exactly-once Kafka processing” myths vs engineering compensations realistically.

Practice reflection: correlate **Lag metrics** intuition—what infra alarms should exist even if dashboards stub learning-level only now.

Interview drill: summarise **scaling consumer count** ramifications on ordering & hot partitions verbally.

