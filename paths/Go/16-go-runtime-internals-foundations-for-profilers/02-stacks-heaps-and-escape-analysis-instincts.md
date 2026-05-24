# Unit 2 — Memory model basics: stacks, heaps, escape analysis instincts

Understand **why** escapes matter economically (heap allocation + GC pressure) even if correctness remains fine.

Operational bridge:

```
go build -gcflags="-m" (escape diagnostics noise—interpret cautiously—compiler updates shift lines)
benchmark + heap profile evidence still king when confused
```

## Interview prompt

Misusing escape logs as astrology—profiler remains authority for hot paths realistically.
