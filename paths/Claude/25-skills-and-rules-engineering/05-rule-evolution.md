# Rule evolution

**Theme:** Production reality drifts—**today’s default becomes tomorrow’s mistake** unless Rules have **version ownership**.

Illustrative pivot:

Once: “ORM X preferred” → Later: “sqlx-style explicit SQL default” after incident / perf lessons.

### Practice

Maintain generational markers—e.g. `rules-v1` archive vs active **v2** surface—**not** silent overwrite without changelog.

Each change entry records:

**What** flipped  

**Why** (incident id, benchmark, compliance)  

**Who** approved  

**Migration** note for open branches / human habit lag

**LAB:** Mutate **five** Rule lines in a sandbox copy—then **validate** downstream: sample tasks, Skills checklists, CI grep if you use it—prove nothing stale references retired phrasing.

Discuss **communication**: diff broadcast to team—Rules hidden only in one laptop harm everyone when AI assists widely.

### Checklist

- [ ] Deprecated Rules stay **searchable** briefly with “superseded by” pointer—avoid orphan duplicates.  
