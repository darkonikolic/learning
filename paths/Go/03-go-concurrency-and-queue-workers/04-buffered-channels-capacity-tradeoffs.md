# Unit 4 — Buffered channels: capacity as temporal slack—not free lunch

Pattern:

```go
make(chan Job, 10)
```

## Learning outcomes

Understand **producer → buffer → receiver** pacing decouples bursty arrivals partially while introducing:

- fullness blocking producers,
- emptiness blocking consumers,
- potential **lost pressure signals** forgetting shutdown coordination.

Capacity choice is behavioural architecture—not magic constant `10`.

## Practice

Maintain bounded backlog ~10 queued fake jobs witnessing producers temporarily quicker than lazy consumer—observe growing occupancy—then choke consumer entirely narrating starvation vs backlog growth consequences qualitatively.

## Lab comparative writing

Enumerate latency / throughput intangible trade-offs **buffer vs unbuffer**.

## Interview prompts

Danger: mistaken belief buffered channels eliminate need for disciplined cancellation.

Deadlocks when both sides blocked incorrectly—diagram mental fix.
