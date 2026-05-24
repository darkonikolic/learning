# Boundary ownership

**Theme:** DDD payoff — SPEC states **who owns what** across contexts.

## Bad vs good

**Weak:** “Order does everything.”  

**Strong:** Explicit separation with ownership:

| Context / module | Owns decisions on |
|------------------|-------------------|
| **Order** | … |
| **Payment** | … |
| **Inventory** | … |
| **Notification** | … |

Interfaces (events, REST, synchronous calls) cite **upstream/downstream SPEC IDs** once you archive multiple docs.

### Spec ownership hierarchy

- **Platform / programme SPEC** owns cross-cutting vocabulary and non-negotiables.  
- **Bounded-context SPECs** own local rules; they reference parent invariants explicitly.  
- **Child must not mute parent acceptance** silently.

## Practice

| Track | Focus |
|-------|--------|
| **Symfony** | **Bounded context** sketch + anti-ball-of-mud guardrails. |
| **Go** | **Payment platform** module boundaries vs generic “utilities”. |

## Lab

Ask for an **ownership / boundary diagram ASCII** plus a **sentence per edge** citing contract direction — **before** implementation files change.

If edges disagree with prior SPECs → **cross-spec inconsistency**: fix SPEC graph first.

## Checklist

- [ ] Each arrow has naming: **owns data / emits event / invokes command**.  
- [ ] Forbidden “reach across” behaviour is spelled as **explicit integration contract**.  
