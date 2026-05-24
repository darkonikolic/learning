# Unit 2 — Problem → requirements → constraints → trade-offs → failure model

Mental choreography (adapt names, keep structure):

```
Problem statement
Functional requirements  
Non-functional requirements (NFRs)
Constraints (hard vs soft)
Design options (few, not infinitely many)
Comparable trade-offs (what you buy / what you pay)
Explicit failure scenarios + detection + rollback posture
```

## Practice

Pick an existing codebase (Symfony monolith referenced in source—or your job system). Produce:

```
functional vs non-functional requirements table
explicit scale assumptions (“100 users”, “100k concurrent sessions”, …)
explicit failure hypotheses (dependency X dies, hotspot key, operator misconfig…)
```

## Lab (blog trajectory)

Contrast **three** evolutionary loads for the same product story:

```
~100 concurrent writers/readers caricature humble start
mid-scale traffic & storage amplification
million-user read-heavy skew with operational maturity expectations
```

State **what subsystem changes first** each time—not “everything becomes microservices magically.”

