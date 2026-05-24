# Unit 2 — Labs: blueprint a guarded multi-step workflow

Produce **`ORCHESTRATION-BLUEPRINT.md`** for a hypothetical feature (“add read-model projection consumer” flavour optional).

Mandatory elements:

Plan states table: `idle → plan → revise → approve? → exec → verify → merge-hold`

Each transition lists **OWNER** (human / agent role) + **TOOLS allowed** + **STOP condition**.

Embed one **planned failure injection** (“reviewer rejects missing benchmark”) illustrating recovery—not happy path fantasy.

Conduct **mental dry run** ≤15 minutes narrating divergence if executor skipped verification node.
