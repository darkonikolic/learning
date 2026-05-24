# Spec partition + dependency graph

**Theme:** Scale past one monolith SPEC — partitioned docs + clarity on **upstream/downstream** truth.

## Partition pattern

Separate living documents instead of cosmic scroll:

| Example slice |
|---------------|
| `frontend-spec.md` *(if applicable)* |
| `api-spec.md` |
| `worker-spec.md` |
| `db-schema-spec.md` |
| `terraform-spec.md` |

Each references **upstream dependencies succinctly**:

```
worker SPEC  →  consumes queue contract declared in api SPEC revision N
worker SPEC  →  persistence invariants delegated to db SPEC section 3.x
```

## Dependency graph artefacts

Maintain lightweight graph (ASCII or Mermaid-compatible text) tying:

**frontend UI contracts → API payloads → worker processing → datastore invariants → IaC rollout ordering**

Forbidden training anti-pattern here: Claude attempts **whole system code** simultaneously — partitioning enforces phased verification.

### Cross-spec consistency sweeps

When two SPECs cite the same noun (“PaymentIdempotencyKey”), periodic diff must show **matching definitions** — otherwise classification: **SPEC conflict** needing merge session.

### Ownership recap

Higher-level SPEC adjudicates clashes between child SPECs if teams disagree until governance steps in.

## Lab

Produce **five SPECs stubs** minimal but linked for a hypothetical payment platform skeleton + dependency arrows only — no full implementation.

## Checklist

- [ ] Every partitioned SPEC lists **consumes / provides**.  
- [ ] Graph updates when critical contract fields rename.  
