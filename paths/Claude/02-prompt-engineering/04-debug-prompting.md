# Debug prompting

**Theme:** An architecture assistant **does not** jump to “try X” without a **hypothesis ladder**.

## Required flow

```
problem (evidence) → hypothesis → validation plan → only then fix
```

## Practice rotations

| Track | Scenario idea |
|-------|----------------|
| **Go** | **Worker slow** — queue lag vs CPU vs IO vs retry storms. |
| **DB** | **Query latency** — plan, locks, hot rows, missing index vs bad access pattern. |
| **Ops** | **Pod restart loop** — crash vs probe vs OOM vs config vs dependency. |

## Lab — forbidden output pattern

Ask the model **not** to output bare **“try X”** without structure.

**Require instead:**

1. **At least five hypotheses** (ranked or grouped).  
2. **Order of checks** with **expected signal** if true/false.  
3. **Risk** of each check (blast radius, time cost, false confidence).

**Measure:** how often the first draft still sneaks in magic fixes — that’s your prompt debt.

## Checklist

- [ ] You pasted **minimal logs / metrics** first, not entire bundles.  
- [ ] You demanded **evidence-linked** reasoning.  
