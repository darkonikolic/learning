# Lab 18 — Model audit: dodijeli model svakom agentu

## Cilj
Na kraju ovog laba svaki agent u `.claude/agents/` ima eksplicitni model assignment s komentarom zašto, `docs/decisions/model-assignments.md` tablica postoji, i testiraš code-reviewer na Haiku modelu.

## Preduvjeti
- Lab 04 završen: `.claude/agents/code-reviewer.md` postoji
- Lab 05 završen: `.claude/agents/store-tester.md` postoji
- Lab 13 završen: `.claude/agents/todo-crawler.md` postoji
- `.claude/settings.json` postoji

## Kontekst
Svaki agent ne treba isti model. Code review zahtijeva dubinsku analizu (Opus ili Sonnet). Crawler koji poziva curl komande ne treba kompleksno razmišljanje (Haiku je dovoljan). Model selection je cost-quality tradeoff — ovaj lab te tjera da ga napraviš eksplicitnim umjesto da koristiš default za sve.

## Koraci

### Korak 1 — Inventoriziraj sve agente

```bash
ls -la .claude/agents/
ls -la .claude/skills/
```

Pored agenata iz lab-ova, možda imaš i:
- `code-reviewer.md` (Lab 04, Lab 05)
- `store-tester.md` (Lab 05)
- `todo-crawler.md` (Lab 13)

---

### Korak 2 — Napiši model assignment decision document

Napravi `docs/decisions/model-assignments.md`:

Otvori Claude sesiju:

```bash
claude
```

```
Read all files in .claude/agents/ directory.
Read 18-model-selection/01-model-tiers-and-tradeoffs.md and 18-model-selection/02-when-to-use-which.md.

For each agent, analyze:
1. What kind of reasoning does it require?
2. How complex are its inputs?
3. How critical is output quality vs speed?
4. What is the appropriate model tier?

Create docs/decisions/model-assignments.md with:

## Agent model assignments

| Agent | File | Task type | Model tier | Model ID | Rationale |
|-------|------|-----------|------------|----------|-----------|
...

## Decision rationale (per agent)

### [agent-name]
Task type: [planning/execution/review/classification]
Reasoning depth required: [deep/standard/narrow]
Input complexity: [high/medium/low]
Model: [Opus/Sonnet/Haiku]
Specific reason: [one sentence]

## Cost implications

With all agents on Sonnet vs optimized assignment:
Estimated savings: [rough percentage]
```

---

### Korak 3 — Ažuriraj agent definicije s model assignments

Za svaki agent fajl, dodaj eksplicitni `model:` field u frontmatter:

**Za `code-reviewer.md`:**

```bash
# Pročitaj trenutni sadržaj
head -10 .claude/agents/code-reviewer.md
```

Frontmatter treba izgledati ovako:

```yaml
---
name: code-reviewer
description: Read-only code review agent...
model: claude-sonnet-4-6
# Model rationale: Review requires understanding context and architecture patterns.
# Sonnet is sufficient — not adversarial security review (that would need Opus).
---
```

Uradi isti update za svaki agent. Primjer assignments za task-api:

| Agent | Preporučeni model | Zašto |
|-------|-----------------|-------|
| code-reviewer | claude-sonnet-4-6 | Standard review logic, ne treba deep adversarial reasoning |
| store-tester | claude-sonnet-4-6 | Test writing je execution task, jasni SPEC input |
| todo-crawler | claude-haiku-4-5 | Curl komande + JSON parsing, minimalno razmišljanje |

```
Update each agent file in .claude/agents/ to add:
1. model: field in frontmatter
2. Comment after model field explaining why that tier was chosen

Use these assignments:
- code-reviewer: claude-sonnet-4-6 (review with clear checklist)
- store-tester: claude-sonnet-4-6 (execution from clear spec)
- todo-crawler: claude-haiku-4-5 (simple HTTP calls, no reasoning needed)

Run: ls .claude/agents/ to confirm all are updated.
```

---

### Korak 4 — Testiraj code-reviewer na Haiku

Ovo je eksperiment: da li Haiku može odraditi code review dovoljno dobro?

Otvori Claude sesiju:

```bash
claude
```

```
You are now running as claude-haiku-4-5 (simulating a Haiku-tier model with reduced reasoning depth).

Review tasks/handler.go using the checklist from .claude/agents/code-reviewer.md.

After review, answer:
1. Which checklist items did you PASS/FAIL?
2. Did you find anything non-obvious that requires deep reasoning?
3. Was this task suitable for a Haiku-tier model, or would you need Sonnet/Opus?
```

**Usporedi s Sonnet review-om:**

Pošalji isti zahtjev bez Haiku simulacije (Claude koristi defaultni Sonnet):

```
Review tasks/handler.go using the checklist from .claude/agents/code-reviewer.md.
After review, answer:
1. PASS/FAIL for each checklist item
2. Any HIGH severity findings?
3. Was this a complex review requiring deep reasoning, or routine?
```

**Dokumentuj razliku:**

```bash
mkdir -p docs/experiments
```

Napravi `docs/experiments/haiku-vs-sonnet-review.md`:

```markdown
# Experiment: Haiku vs Sonnet for code review

## Task
Code review of tasks/handler.go using code-reviewer.md checklist.

## Haiku results
[Paste summary od Haiku simulated review]
Time-equivalent: [bila bi brža/jeftinija]
Quality: [da li je uhvatio sve HIGH findings?]

## Sonnet results
[Paste summary od Sonnet review]

## Comparison

| Aspect | Haiku | Sonnet |
|--------|-------|--------|
| Found all HIGH findings | | |
| Nuanced observations | | |
| Missed anything critical | | |
| Cost (relative) | ~0.1x | 1x |
| Speed | ~5x faster | baseline |

## Conclusion
For this task (checklist-based handler review):
Haiku adequate? [YES/NO]
Reason: [1-2 rečenice]

Recommendation: [ostavi Sonnet za reviewer, ili prebaci na Haiku?]
```

---

### Korak 5 — Kada koristiti Opus

Dokumentuj scenarije kada bi koristio/la Opus za task-api:

```
Based on 18-model-selection/01-model-tiers-and-tradeoffs.md and the task-api project,
identify 3-4 specific scenarios where you would upgrade a task to Opus tier.

Examples to consider:
- SPEC authoring for a complex multi-domain feature
- Security review of authentication code
- Architecture decision for moving from monolith to microservices
- Debugging a race condition in concurrent code

For each scenario, explain:
- Why Sonnet would be insufficient
- What specifically Opus's deeper reasoning adds

Write to docs/decisions/model-assignments.md under "## When to use Opus".
```

---

### Korak 6 — Napiši finalni model assignments summary

Ažuriraj `docs/decisions/model-assignments.md` s finalnom tablicom:

```
Finalize docs/decisions/model-assignments.md.

The document should contain:
1. Agent assignments table (from Step 2)
2. Decision rationale per agent (from Step 2)
3. Haiku vs Sonnet experiment findings (from Step 4)
4. When to use Opus scenarios (from Step 5)
5. Cost implications table:
   - All agents on Opus: [100% cost]
   - All agents on Sonnet: [~15-20% of Opus]
   - Optimized (current assignments): [estimate %]

Confirm: is the document complete and would a new team member understand
why each agent has the model it has?
```

---

### Korak 7 — Commituj sve

```bash
git add .claude/agents/ docs/decisions/model-assignments.md docs/experiments/
git commit -m "config: explicit model assignments per agent with documented rationale"
```

## Verifikacija

- [ ] Svaki agent fajl u `.claude/agents/` ima `model:` field u frontmatteru
- [ ] Svaki model field ima comment koji objašnjava zašto
- [ ] `docs/decisions/model-assignments.md` postoji s agent tablicom
- [ ] `docs/experiments/haiku-vs-sonnet-review.md` postoji s comparison-om
- [ ] Haiku review eksperiment je dokumentiran s konkretnim findings
- [ ] "When to use Opus" sekcija ima ≥3 konkretna scenarija

## Šta si naučio

- **Model tier ≠ model quality za sve taskove**: Haiku je lošiji za kompleksno planiranje, ali za cursor komande i checklist review može biti dovoljan
- **Eksplicitni model assignment** sprečava "drift" na skuplje modele — default je obično Sonnet, ali bez eksplicitnog assignmenta možeš završiti s Opus na trivijalnim taskovima
- **Cost ratio se akumulira**: ako imaš 10 agenata koji svi koriste Opus kad bi Haiku bio dovoljan za 7 njih, plaćaš 3-4x više po sesiji
- **Dokumentovati zašto** je jednako važno kao i sam assignment — "model: haiku" bez objašnjenja ostavlja pitanje "zašto ne Sonnet?" za narednog čitatelja
- **Haiku adequate** za: checklist-based review, simple CRUD operations, curl/HTTP calls, classification tasks — NE za: architecture decisions, ambiguous SPECs, security adversarial review
