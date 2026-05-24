# Role prompting

**Theme:** The model’s “stance” changes the kind of mistakes it makes — pick the role to match the review you need.

## Failure mode

**Weak:** “Explain Redis.”  
**Strong:** Give a **ROLE** that encodes **ownership and stakes**, then a narrow question.

### Example

“You are a **senior backend architect** (Symfony ~14y pattern is illustrative — use your real tenure). You own **Go backend** platform decisions. Explain **cache ownership** for Redis in **our** bounded contexts — not a textbook tour.”

## Roles to rehearse

Rotate the same technical question through multiple roles and compare outputs:

- Backend / platform **architect**  
- **Ops engineer** (deployability, rollback, SLO)  
- **Security reviewer** (threats, data paths, blast radius)  
- **Staff engineer** (trade-offs, long-term cost)  
- **Incident responder** (time pressure, evidence-first)  
- **Performance engineer** (latency, queueing, hot paths)  

## Lab

- **One problem** → **five ROLE variants** (everything else as equal as possible).  
- Compare: depth, missed risks, verbosity, actionability.

**Measure:** quality, iterations, subjective “would I ship this advice?”.

## Checklist

- [ ] ROLE binds to **decisions you can make**, not fictional company lore.  
- [ ] You still attach **CONTEXT + CONSTRAINTS** when the problem is real-system sized.  
