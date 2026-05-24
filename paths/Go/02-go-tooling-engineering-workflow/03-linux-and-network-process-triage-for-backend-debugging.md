# Unit 3 — Linux + network triage beside Delve: processes, sockets, and syscalls

## Learning outcomes

- Map a **listening port** (`LISTEN`) to a **PID** and binary without guessing—which process actually owns `:8080`.
- Inspect **TCP connection state** summaries when backends look “wedged” (many `CLOSE_WAIT`, saturation, asymmetric counts).
- Use **`strace` / `perf`** at a restrained, read-only scope to distinguish “blocked on I/O syscall” vs “burning CPU in userspace”—without treating attach-to-prod lightly.
- Read **`/proc/<pid>/`** essentials (`fd`, `limits`, brief `stack` awareness) when `delve` is unavailable (stripped binaries, hostile environments).

## Concepts to internalise

- **Observability vs debugging**: syscall traces prove behaviour; structured logs/traces explain intent—use each where it earns its blast radius.
- **Production etiquette**: syscall attachment can stall high-throughput processes—prefer replicas, lowered traffic reproduction, or canary namespaces when possible.

## Lab (local or disposable VM)

Pick a toy HTTP listener (your earlier CLI or minimal `chi`/`net/http` service). Without opening the codebase first:

```
identify PID + binary path
enumerate listening sockets correlating fd → socket
simulate slow client behaviour and observe backlog / state changes narratively (even if tooling output only described in prose)
```

## Interview prompts

- When would you **`strace`** a Go binary vs **`go tool pprof`** vs **tracing** vs **TCP dumps** (`tcpdump` only where policy allows)?
- How does **ephemeral-port exhaustion** mimic app bugs?

## Acceptance criteria

Short written note contrasting **three** hypothetical symptoms (high CPU, stalled requests, intermittent timeouts) → **which** Linux/tool signal you’d check first → **why** Delve alone might lie.
