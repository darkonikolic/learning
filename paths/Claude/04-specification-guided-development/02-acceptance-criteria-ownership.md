# Acceptance criteria ownership

**Theme:** Architect language is not “works” — it is **what “done” means in observable checks**.

## Bad vs good

**Weak:** “Refund works.”  

**Strong:** Refund implies (example bundle — tune to reality):

- **Payment status** transitions per policy.  
- **Inventory restoration** succeeds or saga compensates deterministically.  
- **Audit** record persisted with immutable trail.  
- **Notification** emitted on terminal states.  
- **Rollback rule** when inventory step fails mid-flight.

Every line should be binary checkable (**pass/fail**) if you exercised the behaviour.

## Practice

| Track | Focus |
|-------|--------|
| **Symfony** | **Refund flow** spanning aggregate + integrations. |
| **Go** | **Payment retry** — success criteria per attempt class. |

## Lab

Each feature-shaped task: ship **minimum five acceptance criteria**. If merging two features, multiply carefully — duplication is intentional until your taxonomy matures.

**Measure:** can a teammate sign off via checklist without trusting prose?

## Checklist

- [ ] Criteria read like **verification steps**, not marketing.  
- [ ] Each criterion binds to **ownership** (“who observes / tests this?”).  
