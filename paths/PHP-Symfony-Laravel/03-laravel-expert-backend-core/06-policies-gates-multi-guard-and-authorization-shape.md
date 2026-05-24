# Unit 6 — Authorization: policies gates multi-guards

Goals

Map **Symfony Voter mental model → Laravel Policies / Gates**:

- aligning subject + user context ergonomics cleanly,
- **after middleware vs route-model implicit binding interplay** guarding attribute-level checks,
- **resource collections** iterating authorization without N policy roundtrips careless patterns.

Operational angle

API token abilities vs SPA session distinctions—articulate escalation boundaries.
