# Security in SPEC and PLAN

## Security requirements belong in the SPEC

Security is not a phase you add at the end. It is a set of requirements that constrain implementation the same way functional requirements do. A SPEC that says nothing about security is a SPEC that implicitly accepts all security risks.

The place to catch "task IDs should not be sequential integers" is the SPEC, before any code exists. Catching it after implementation means retrofitting UUID generation, updating all tests, and explaining to stakeholders why IDs changed.

---

## Acceptance criteria for security

Security acceptance criteria go in the SPEC's acceptance section. They are binary — pass or fail, verifiable against the implementation.

**Poorly written (not binary, not verifiable):**
```markdown
- [ ] The API should be reasonably secure
- [ ] Error handling should be good
```

**Correctly written (binary, verifiable):**
```markdown
## Acceptance criteria — security

- [ ] POST /tasks rejects request bodies larger than 10KB with HTTP 413 (prevents payload flooding)
- [ ] API does not include Go stack traces in error responses (prevents internal structure disclosure)
- [ ] Task IDs are UUIDs, not sequential integers (prevents enumeration of all tasks)
- [ ] Completed tasks can be read (GET /tasks) but cannot be un-completed (state machine enforced at handler level)
- [ ] Invalid JSON in request body returns 400 with message "invalid request body" — not the JSON parse error text
```

Each criterion names: what the behavior is, how to test it, and why it matters.

---

## NFR section for security

Non-functional requirements (NFRs) capture security properties that apply across the whole phase, not to individual endpoints.

```markdown
## NFR — security

- No SQL injection risk: storage is in-memory for this phase; note here when database is added so this NFR is revisited
- No path traversal risk: no file system operations in this phase
- No credentials in logs: config.go reads PORT and LOG_LEVEL; neither is sensitive; log at startup is acceptable
- No credentials in responses: no config values are returned by any endpoint
- Error responses contain error message only — never stack traces, never internal field names
- All handler functions are covered by unit tests that verify error response format
```

Mark "N/A for this phase" explicitly rather than omitting. An omitted NFR looks like an oversight. "N/A for this phase — revisit when database is added" signals intentional scoping.

---

## SPEC template — security section

Insert this section into every SPEC.md between functional requirements and implementation notes:

```markdown
## Security requirements

### Input validation
- Maximum request body size: [specify or "N/A — no request body"]
- Accepted content types: [e.g., "application/json only; 415 for others"]
- Required fields validation: [list required fields and what happens if missing]

### Output safety
- Stack traces: never in responses
- Internal field names: [list any fields that must not appear in responses]
- Error message text: [specify the pattern — generic or specific?]

### Identifiers
- ID format: [UUID / sequential int / other] — document the choice and rationale

### State transitions
- [For each resource: list valid state transitions and invalid ones that must be rejected]

### NFR checklist
- [ ] SQL injection risk: [present / N/A — in-memory / mitigated by ORM parameterization]
- [ ] Path traversal risk: [present / N/A — no file ops]
- [ ] Credential exposure in logs: [present / mitigated / N/A]
- [ ] Credential exposure in responses: [present / mitigated / N/A]
```

---

## STRIDE threat modeling for task-api

STRIDE is a structured threat model: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege.

For each threat, identify: does it apply to this system? If yes, what is the mitigation? If the mitigation is "out of scope for this phase", say so explicitly — this creates a future requirement.

| Threat | Description | Phase 1–3 exposure | Mitigation or deferral |
|--------|-------------|-------------------|----------------------|
| Spoofing | Attacker impersonates a user | No auth in Phase 1–3 | Out of scope; add auth phase before any real data |
| Tampering | Attacker modifies another user's task | No per-user isolation in Phase 1–3 | Out of scope; single-user in-memory store |
| Repudiation | User denies creating a task; no audit trail | No audit log in Phase 1–3 | Out of scope; note for Phase 4+ |
| Information disclosure | Sequential IDs allow enumeration of all task IDs | IDs would reveal total task count and ordering | Mitigation: UUID v4 for all task IDs |
| Denial of service | Flood POST /tasks with large bodies | Unlimited body size would exhaust memory | Mitigation: 10KB body limit via `http.MaxBytesReader` |
| Elevation of privilege | Mark any task complete, not just user's own | No per-user isolation in Phase 1–3 | Out of scope; single-user store |

Add this table to your SPEC.md or to a SECURITY.md that lives alongside it.

---

## Security verification pass

A security verification pass runs after execute-phase. It reads the threat mitigations documented in PLAN.md and SPEC.md and verifies they exist in the implemented code.

**When to run it:**
- After any phase that handles user input
- After any phase that stores or retrieves data
- After any phase that adds authentication or authorization
- After any phase that exposes new endpoints

**Not needed for:**
- Documentation-only phases
- Internal refactors that do not change input handling
- Configuration changes that do not affect the attack surface

**What it produces:**

A SECURITY.md with each threat mitigation marked:

```markdown
## Security verification — Phase 1

| Mitigation | Status | Evidence |
|-----------|--------|---------|
| Task IDs are UUIDs | VERIFIED | tasks/store.go:12 — uuid.New() |
| Body size limited to 10KB | VERIFIED | tasks/handler.go:34 — http.MaxBytesReader |
| Stack traces not in responses | VERIFIED | tasks/handler.go:writeError uses fixed message strings |
| Invalid JSON returns 400 | VERIFIED | tasks/handler.go:45 — json.Decode error path |
| SQL injection risk | N/A | In-memory store; no database in this phase |
```

A MISSING status means: the SPEC required this mitigation, the code was searched, it was not found. You must either implement it or update the SPEC to defer it with documented rationale.

---

## Encoding security in PLAN.md tasks

Security mitigations need to appear as explicit PLAN.md tasks, not as implicit expectations:

```markdown
## Wave 2 — Task storage

### Task 2.3 — Task ID generation
Implement UUID v4 generation for task IDs.
File: tasks/store.go
Implementation: use `github.com/google/uuid` — `uuid.New().String()`
Verification: POST /tasks 10 times; IDs must all be different UUIDs (format: 8-4-4-4-12 hex)
Security note: satisfies STRIDE-ID (information disclosure via sequential IDs)

### Task 2.4 — Request body size limit
Add `http.MaxBytesReader` to POST /tasks handler before JSON decode.
Limit: 10240 bytes (10KB)
Verification: POST with 11KB body returns 413; POST with 1KB body returns 201
Security note: satisfies STRIDE-DOS (memory exhaustion via large bodies)
```

Without explicit tasks, security mitigations depend on the implementer remembering them. Explicit tasks make them checkable.

---

## Checklist

- [ ] I understand that security requirements belong in the SPEC, not as a separate phase.
- [ ] I can write binary, verifiable security acceptance criteria.
- [ ] I know what NFR means and how to write security NFRs.
- [ ] I can explain the STRIDE model and apply it to task-api.
- [ ] task-api SPEC includes security acceptance criteria: UUID IDs, body size limit, no stack traces in responses.
- [ ] I know when to run a security verification pass and what it produces.
- [ ] I know how to encode security mitigations as explicit PLAN.md tasks with verification steps.
- [ ] I understand that "N/A for this phase" is an explicit, documented decision — not an omission.
