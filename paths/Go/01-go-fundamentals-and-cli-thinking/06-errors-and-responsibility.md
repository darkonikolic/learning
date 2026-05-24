# Unit 6 — Error handling thinking: responsibilities, wrapping, panic discipline

## Learning outcome

Treat Go errors as ordinary **first-class returned values**:

```go
value, err := Do()
```

You practise:

- **`errors.New`**
- **`fmt.Errorf`** with verbs including **`%w`** when layering failure causes expect introspection downstream.

Understand **defer / recovery** folklore only after recognising **`panic`** is rarely your happy-path instrument.

Go **does not** elevate exceptions controlling normal outcomes; pretending it does produces unreliable services quietly.

## Core ideas

- Every failure path chooses **classification**: caller-retry-able? programmer bug? sanitation for user-visible message?
- **Wrap** sparingly yet meaningfully—“open config: …” beats anonymous `return err`.
- **`panic`** signals **stop the world-ish** invariant violation or impossible states after programming mistakes—not missing files in CLI unless you consciously scope recovery at `main`.

## CLI practice sketch

Exercise file operations (read absent file, unreadable permission). Thread errors upward enriching context at boundaries.

Contrast:

- returning wrapped errors,
- logging then swallowing (**forbidden habitual pattern** articulation),

## Lab

Document three scenarios:

1. **network-ish** ephemeral errors (simulate),
2. **validation** misuse,
3. **programmer** misuse.

Argue succinctly panic appropriateness (likely none—but justify edge cases responsibly).

## Interview prompts

| Topic | Probe |
|-------|-------|
| `panic` vs `error` operational culture | articulate |
| sentinel errors introduction (`errors.Is`) | bridging future modules |
| when **not** to wrap (avoid chaining noise pollution) |
