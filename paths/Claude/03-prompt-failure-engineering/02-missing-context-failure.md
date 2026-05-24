# Missing context failure (and over-context)

**Theme:** The model is not psychic — “your project” is not in the prompt unless you put it there. Too much undifferentiated context creates **token pressure** and wrong focus.

## Missing context pattern

**Weak:** “Optimize the query.”  
**Stronger:** Attach minimal **ground truth**: **MySQL**, **~120M rows**, **replica topology**, **read-heavy**, **p95 latency ~900ms**, access pattern (OLTP vs reporting), what “good” means.

**Diagnosis labels:** **missing context**; sometimes **ambiguity** if “optimize” is still undefined.

## Over-context / token pressure pattern

**Symptom:** answer chases the wrong detail, contradicts itself, or stays generic — you pasted whole modules, old tickets, and three unrelated configs.

**Diagnosis label:** **token pressure** / **over-context** (same family: wrong *amount* and *relevance* of context).

## Practice rotations

| Track | Focus |
|-------|--------|
| **Symfony** | **CQRS** read path vs write path — paste only the slice that owns the decision. |
| **Go** | **Worker** path — only handler + retry + message shape that matters today. |
| **Ops** | **Terraform** (or IaC) — only the module + env + state risk for *this* change. |

## Lab — three deliberate sizes

On **one** real question:

1. **Too little context** — observe confident wrong assumptions.  
2. **About right** — minimal facts that change the answer.  
3. **Too much** — observe noise, drift, or generic advice.

**Measure:** quality (quick rubric), **iterations** to acceptable output.

## Checklist

- [ ] You can state **one** decision the message must unlock.  
- [ ] Everything in the paste **earns its tokens** for that decision.  
