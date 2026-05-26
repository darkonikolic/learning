# Lab: partition Phase 4 auth feature

Prerequisites: `docs/specs/` exists. Phase 1-3 of task-api are complete (POST /tasks, GET /tasks, PATCH /tasks/:id/done). You have read `17-spec-partitioning/01-splitting-specs-across-phases.md`.

---

## The feature

Phase 4 brief: "Add user authentication so each user only sees their own tasks."

Current state of task-api: no auth. All tasks are global. Any caller can create and read all tasks. The store holds `[]domain.Task` in memory with no user association.

---

## Step 1: identify the ownership domains

Read the Phase 4 brief and list every distinct concern. Do not think about implementation yet. Think about: what module owns this decision? Who would sign off on it?

Work through the feature:

**Token generation**
A new user must get a token. Something must create JWTs. Owns: signing key, claims shape, expiry. Module: `auth` (does not exist yet).

**Token validation**
Every protected request must prove it holds a valid token. Something must parse and verify JWTs. Owns: HMAC verification, expiry check, claims extraction. Module: `auth`.

**Auth middleware**
The HTTP layer must enforce authentication before calling any handler. Something must attach the validated UserID to the request context. Owns: `http.Handler` wrapping, context key, response for 401. Module: `handler` (uses auth package).

**Task store — user scoping**
The in-memory store currently returns all tasks. After Phase 4, `List()` must filter by user. `Create()` must attach a user ID to the task. Owns: `user_id` field on `domain.Task`, filtered retrieval. Module: `store` (and `domain`).

Four concerns. Map them to domains:

| Concern | Domain | Module |
|---------|--------|--------|
| JWT creation and validation | auth | `internal/auth` |
| HTTP middleware enforcement | handler | `internal/handler` |
| User scoping in store | store | `internal/store` + `domain` |
| Token issuance endpoint (POST /token) | handler | `internal/handler` |

Token generation and validation are the same domain — both live in `internal/auth`. Middleware consumes auth. The store scoping is independent of how the token is structured; it only needs the UserID value.

**Identified domains: auth, handler (middleware + token endpoint), store.**

---

## Step 2: apply the partition decision table

| Question | Answer |
|----------|--------|
| How many unrelated ownership domains? | 3 (auth / handler / store) |
| Can acceptance criteria be assigned clearly to one domain each? | Not if all in one SPEC — auth and store criteria are unrelated |
| Would the auth module change independently of the store module? | Yes — token format could change without touching store |
| Is this a genuinely new subdomain (nothing exists yet)? | Yes — no auth package exists |
| Is the project small enough that one SPEC would work? | Borderline — 3 domains is the threshold |

**One SPEC vs multiple — decision table:**

| Criterion | One SPEC | Multiple SPECs |
|-----------|----------|----------------|
| Ownership domains | ≤ 2 | ≥ 3 |
| New subdomain added | No | Yes |
| Acceptance criteria assignable | Yes, single reviewer | No, need per-domain ownership |
| Downstream depends on upstream contract | No | Yes (store depends on UserID type from auth) |
| Phase size (line estimate) | < 100 lines | ≥ 100 lines across new modules |

Phase 4 hits three of the five "multiple SPECs" signals. **Decision: two SPECs.**

Why two and not three? Auth and handler middleware belong together because the middleware is the runtime expression of the auth contract — it calls `auth.ValidateToken()` directly and is not meaningful without it. They are coupled enough to share a single approval. The store is genuinely separate: it does not import auth, it only needs the UserID string that middleware places in context.

```
docs/specs/auth-middleware.md    — auth package + HTTP middleware + POST /token endpoint
docs/specs/store-user-scoping.md — domain.Task user_id field + store.List(userID) + store.Create(userID, title)
```

---

## Step 3: write the dependency graph

Use this format for each SPEC:

```
SPEC: <name>
  provides: <exported interface or behavior>
  consumes: <what it depends on from upstream SPECs, or "nothing">
  must be approved before: <downstream SPECs that cannot finalize without this>
```

Fill it in for Phase 4:

```
SPEC: auth-middleware
  provides:
    - auth.ValidateToken(token string) (UserID string, err error)
    - auth.GenerateToken(userID string) (string, error)
    - handler.AuthMiddleware(next http.Handler) http.Handler
    - POST /token endpoint → returns {"token": "<jwt>"}
    - request context key: contextKeyUserID (type string)
  consumes: nothing upstream
  must be approved before: store-user-scoping (needs UserID type confirmed as string)

SPEC: store-user-scoping
  provides:
    - domain.Task gains UserID string field
    - store.Create(userID, title string) (domain.Task, error)
    - store.List(userID string) []domain.Task
  consumes: auth-middleware rev 1 (UserID type = string; context key for handler integration)
  must be approved before: nothing (no downstream SPECs in Phase 4)
```

**Dependency graph (ASCII):**

```
auth-middleware SPEC  (upstream)
        |
        | provides: UserID type (string), context key name
        ↓
store-user-scoping SPEC  (downstream)
```

Execution order enforced: `auth-middleware` SPEC must be approved before `store-user-scoping` SPEC is finalized. The store SPEC cannot write its acceptance criteria for `List(userID)` until the upstream SPEC confirms that UserID is a plain string (not a struct, not a UUID type alias).

---

## Step 4: write the SPECs (stub level)

For this lab, write stub-level SPECs — fill the `provides/consumes` header, Problem, Goal, Boundary, and at least three acceptance criteria. Implementation strategy and Tradeoff can be brief.

**docs/specs/auth-middleware.md — stub:**

```markdown
# SPEC: auth-middleware

## Provides
- auth.ValidateToken(token string) (userID string, err error)
- auth.GenerateToken(userID string) (string, error)
- handler.AuthMiddleware wraps http.Handler; injects UserID into context
- POST /token: accepts {"user_id":"<id>"}, returns {"token":"<jwt>"}

## Consumes
- nothing upstream

## Problem
No authentication exists. Any caller can read and create tasks for any user.

## Goal
POST /token issues a signed JWT. Authenticated endpoints reject requests without a valid token
and expose the validated UserID to downstream handlers via request context.

## Boundary
- internal/auth: owns signing key, JWT creation, JWT validation
- internal/handler: owns middleware wiring, context key, 401 responses
- handler does not re-implement token validation; it calls auth.ValidateToken()

## Acceptance
- [ ] POST /token with body {"user_id":"alice"} returns 200 and {"token":"<non-empty string>"}
- [ ] GET /tasks without Authorization header returns 401 and {"error":"unauthorized"}
- [ ] GET /tasks with valid token returns 200 (user sees only their tasks — see store SPEC)
- [ ] GET /tasks with expired token returns 401 and {"error":"token expired"}
- [ ] auth.ValidateToken(token) returns ("alice", nil) for a token generated by auth.GenerateToken("alice")
```

**docs/specs/store-user-scoping.md — stub:**

```markdown
# SPEC: store-user-scoping

## Provides
- domain.Task.UserID string field
- store.Create(userID, title string) (domain.Task, error)
- store.List(userID string) []domain.Task — returns only tasks owned by userID

## Consumes
- auth-middleware SPEC rev 1: UserID type confirmed as plain string

## Problem
The task store is global. Any authenticated user retrieves all tasks regardless of ownership.

## Goal
store.List(userID) returns only tasks whose UserID matches the argument.
store.Create(userID, title) persists the userID on the new task.

## Boundary
- domain package: owns Task struct — UserID field added here, not in handler
- store package: owns filtering logic — handler does not filter; it passes userID from context
- handler extracts userID from context and passes to store; store does not touch context

## Acceptance
- [ ] store.List("alice") after creating tasks for "alice" and "bob" returns only alice's tasks
- [ ] store.List("alice") with no tasks for alice returns []
- [ ] store.Create("alice", "buy milk") returns a task with UserID == "alice"
- [ ] GET /tasks as alice after bob created tasks returns only alice's tasks (integration)
- [ ] domain.Task JSON response does not expose user_id field to API callers (omitempty or omit)
```

---

## Step 5: identify cross-SPEC consistency risks

Two SPECs referencing a shared concept can drift after initial approval. Identify two risks for Phase 4.

**Format for each risk:**

```
Shared symbol: <name>
Defined in: <upstream SPEC>
Used in: <downstream SPEC>
Risk: <what happens if the upstream definition changes>
Detection: <grep command or review trigger>
Mitigation: <process step>
```

**Risk 1:**

```
Shared symbol: UserID (type and context key)
Defined in: auth-middleware SPEC (plain string, context key = contextKeyUserID)
Used in: store-user-scoping SPEC (List(userID string), Create(userID string, ...))
Risk: if auth SPEC changes UserID to a struct (type UserID struct{Sub string}) the store
      SPEC's function signatures and acceptance criteria become type-incorrect without a
      corresponding update.
Detection: grep -r "UserID\|contextKeyUserID" docs/specs/
Mitigation: any type change to UserID in auth-middleware SPEC triggers mandatory re-review
            of store-user-scoping SPEC before implementation begins.
```

**Risk 2:**

```
Shared symbol: user_id JSON field visibility
Defined in: store-user-scoping SPEC (acceptance criterion: user_id not exposed in API response)
Used in: auth-middleware SPEC implicitly (POST /token response shape; GET /tasks response shape)
Risk: if handler SPEC (embedded in auth-middleware) adds user_id to the task response for
     debugging, it contradicts the store SPEC's explicit exclusion criterion, causing a
     verification conflict at acceptance time.
Detection: grep -r "user_id\|UserID" docs/specs/ && diff acceptance criteria sections manually
Mitigation: any change to task response fields in auth-middleware SPEC requires checking
            store-user-scoping acceptance criteria for contradictions before approval.
```

---

## Step 6: verify your partition

Before submitting the SPECs for approval, run these checks:

Can you grep the store SPEC for any mention of JWT, HMAC, or signing? If yes, the boundary is leaking — remove it.

Can you grep the auth SPEC for any mention of SQL, in-memory slice, or filtering? If yes, the boundary is leaking — remove it.

Does each SPEC's acceptance criteria list contain only criteria the owning module can satisfy alone (plus integration criteria clearly marked)? If a criterion requires both modules to work, mark it explicitly as an integration criterion with the dependency noted.

---

## Checklist

- [ ] I identified all four concerns in Phase 4 and mapped them to three domains
- [ ] I applied the partition decision table and chose two SPECs with written justification
- [ ] I wrote the dependency graph showing auth-middleware as upstream of store-user-scoping
- [ ] auth-middleware SPEC declares `provides` and `consumes: nothing upstream`
- [ ] store-user-scoping SPEC declares `consumes: auth-middleware SPEC rev 1`
- [ ] I wrote at least three acceptance criteria per SPEC, all binary
- [ ] I identified two cross-SPEC consistency risks using the shared-symbol format
- [ ] Each risk includes a grep-based detection method and a process mitigation
- [ ] Neither SPEC's acceptance criteria reference internals of the other SPEC's module
- [ ] I can explain why three SPECs was rejected in favor of two for this project size
