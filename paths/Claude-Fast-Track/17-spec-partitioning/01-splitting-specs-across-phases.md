# Splitting SPECs across phases

## The signal: when one SPEC is too large

A single SPEC is right for task-api Phase 1 (POST /tasks). It has one ownership domain: the handler calls the store; the store owns the data. One SPEC covers both — the boundary section describes which module is responsible for what.

A SPEC becomes too large when it has **more than two unrelated ownership domains**. The signal is not file count or line count. The signal is: if two different engineers would reasonably disagree about which section they are responsible for, the SPEC covers more than one ownership domain.

| Signal | Action |
|--------|--------|
| SPEC has 1-2 ownership domains | One SPEC. Use Boundary section to separate concerns. |
| SPEC has 3+ unrelated ownership domains | Partition. Each domain gets its own SPEC. |
| Same noun defined differently in two sections | Already drifted. Partition and reconcile. |
| Acceptance criteria from unrelated systems in one list | Partition. Mixed criteria cannot be assigned clearly. |

Unrelated means: the team that owns the auth middleware is not the team that owns the task store. For a solo project, substitute: the module that handles JWTs is not the module that handles SQL. If you would not change them in the same PR, they are unrelated.

---

## How to partition: ownership boundary, not file count

Wrong partition rule: "this SPEC is 200 lines, split it in half."

Correct partition rule: find where one module's contract ends and another begins. That is the cut.

For task-api with auth added in Phase 4:

```
auth SPEC        — owns: JWT creation, token validation, middleware interface
handler SPEC     — owns: per-endpoint auth enforcement, request context propagation
store SPEC       — owns: user-scoped query logic, user_id column, filtered List()
```

The auth SPEC does not describe how the handler attaches the middleware to a route. The handler SPEC does not describe how the JWT is signed. The store SPEC does not describe what a valid token looks like. Each SPEC ends at its own boundary and declares what it **provides** (output contract) and what it **consumes** (input it depends on from another SPEC).

---

## The dependency graph: upstream and downstream

Every partitioned SPEC declares its position in the graph:

```
auth SPEC  →  provides: ValidateToken(token string) (UserID, error)
              consumes: nothing upstream

handler SPEC  →  provides: per-route middleware wiring, UserID in request context
                 consumes: auth SPEC rev 1 (ValidateToken signature)

store SPEC  →  provides: List(userID string) []Task
               consumes: nothing from auth; userID type established by auth SPEC rev 1
```

The graph in ASCII:

```
auth SPEC (upstream)
    ↓ provides ValidateToken contract
handler SPEC
    ↓ provides context.UserID population
store SPEC (downstream, parallel to handler)
    ↓ consumes userID type from auth SPEC
```

**Upstream SPEC defines the contract. Downstream SPEC depends on it.**

This has two consequences:

1. Upstream SPECs must be approved before downstream SPECs can be finalized. You cannot write the handler SPEC's acceptance criteria for "UserID is present in request context" until the auth SPEC defines what UserID looks like.

2. Changing an upstream SPEC is a breaking change until proven otherwise. Any field rename, type change, or removal in an upstream SPEC is a cross-SPEC consistency event.

---

## Cross-SPEC consistency: what triggers a downstream review

When you change an upstream SPEC, run this check:

```
grep -r "ValidateToken\|UserID\|TokenClaims" docs/specs/
```

Any downstream SPEC that references the changed symbol needs a consistency review. The review answers: does the downstream SPEC's acceptance criteria still hold given the upstream change?

| Upstream change | Downstream impact | Action |
|----------------|-------------------|--------|
| Type rename (`UserID` → `SubjectID`) | All SPECs using the field name | Update downstream SPECs before implementation |
| Signature change (`ValidateToken` gains second param) | Handler SPEC's middleware wiring section | Re-review acceptance criteria |
| Error type change | Any SPEC that describes error handling behavior | Re-verify acceptance criteria still binary |
| Field removed from token claims | Any SPEC that depends on that field | Identify replacement or remove acceptance criteria |

The review is not a meeting. It is a diff. Open each downstream SPEC, find every reference to the changed symbol, and verify the acceptance criteria are still binary and correct. If they are not, update them before implementation begins.

**Merge governance:** when two SPECs conflict on a shared noun, the upstream SPEC wins. The downstream SPEC author must adjust. If the conflict cannot be resolved by adjusting one side, escalate to a merge session — both SPECs open, explicit decision written in both Tradeoff sections.

---

## task-api Phase 4: auth partitioning worked example

Phase 4 feature: "add user authentication so each user only sees their own tasks."

This involves:
- JWT generation and validation (auth domain)
- Middleware that enforces authentication on routes (handler domain)
- Filtering tasks by user ID in the store (store domain)

**Does this need three SPECs?**

Apply the partition rule: are these unrelated ownership domains? In task-api, the answer is nuanced. For a small project with one engineer:

- auth + handler middleware: these are closely related. The auth logic is minimal (stdlib `crypto/hmac`, one function). The middleware is three lines that call that function. This could be one SPEC with two boundary sections.
- store: List(userID) is a separate concern from auth itself. But it is a simple filter on an existing function — additive, not a replacement.

**Decision for task-api Phase 4 (small project):**

```
Option A: three SPECs (auth, handler, store)
  Pro: matches large-system partitioning exactly
  Con: three approval gates for a 150-line feature; overhead exceeds benefit

Option B: one auth SPEC + one store-scoping SPEC
  Pro: auth boundary is meaningful; store change is separate enough to own its own acceptance
  Con: handler middleware section lives in auth SPEC (minor boundary blur)

Option C: single SPEC for all of Phase 4
  Pro: minimal overhead; total feature is small
  Con: mixed acceptance criteria; hard to assign clearly; violates the >2 domains rule
       (auth + handler + store = 3 domains)

Decision: Option B. task-api is small enough that auth+handler middleware belong together.
Store scoping is distinct enough (different package, different acceptance criteria) to own its own SPEC.
```

Write:
- `docs/specs/auth-middleware.md` — JWT validation + route enforcement, provides UserID in context
- `docs/specs/store-user-scoping.md` — consumes UserID from context, provides filtered List()

---

## The single-SPEC rule for task-api

For most task-api phases, one SPEC per phase is correct. The project is small. The ownership is clear from the module structure (handler / store / domain). The Boundary section of a single SPEC handles separation without requiring multiple documents.

Partition only when:
- A phase adds a genuinely new subdomain (auth is new in Phase 4 — no auth logic exists yet)
- Acceptance criteria from two domains cannot be assigned to the same reviewer
- A downstream module cannot start implementation until an upstream contract is finalized

Do not partition to signal thoroughness. A project with five SPECs for a 500-line codebase has more process overhead than working code. The partition exists to serve clarity, not to demonstrate rigor.

---

## Approving partitioned SPECs in the right order

Partitioned SPECs have an approval sequence. Approving them out of order wastes the exercise.

The rule: an upstream SPEC must be **approved** (not just drafted) before any downstream SPEC acceptance criteria are finalized. "Approved" means: the Boundary section is stable, the `provides` list is locked, and the team has agreed it will not change without a consistency sweep.

For task-api Phase 4:

```
1. Draft auth-middleware SPEC
2. Review: is ValidateToken signature stable? Is UserID type confirmed?
3. Approve auth-middleware SPEC  ← lock point
4. Draft store-user-scoping SPEC  ← now you can write List(userID string) with confidence
5. Review store-user-scoping SPEC against auth-middleware provides
6. Approve store-user-scoping SPEC
7. Implementation begins
```

If you draft both SPECs simultaneously before approving the upstream one, you will write downstream acceptance criteria against an assumption that may change. That produces a SPEC conflict the moment the upstream is revised. The cost is rewriting downstream criteria before implementation, which is exactly the rework partitioning is meant to prevent.

One exception: when the upstream SPEC's provides list is trivially stable from day one (e.g., adding a single new field to an existing type), you can draft both simultaneously. State the assumption explicitly in the downstream SPEC's `consumes` section: "consumes: domain.Task.UserID will be plain string — assumed stable, verify before implementation."

---

## Checklist

- [ ] I can identify the ownership domains in a SPEC using the signal table
- [ ] When partitioning, I split at the module boundary, not at line count
- [ ] Each partitioned SPEC declares what it provides and what it consumes
- [ ] I can draw the dependency graph showing upstream → downstream arrows
- [ ] I know which downstream SPECs to review when an upstream SPEC changes
- [ ] I can apply the single-SPEC rule to task-api and justify when to partition Phase 4
- [ ] Merge conflicts between SPECs are resolved at the upstream SPEC level, not the downstream
