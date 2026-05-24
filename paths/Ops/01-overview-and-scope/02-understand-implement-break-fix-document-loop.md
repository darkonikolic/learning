# Practise discipline — intentional fault injection and documentation

## Rule of the entire path — theory grounded in breakage

Standalone theory consumption is insufficient: for each competency cluster you practise the loop:

Understand the concept → implement it cleanly → deliberately fault the system → **interpret what telemetry and symptoms mean** → repair with controlled reversibility → **document hypotheses, evidence chain, corrective steps, rollback notes**, plus follow-ups that harden recurrence probability downward.

Operational mindset aspiration:

Listen for what the infrastructure is trying to imply — not vague “broken” vibes without inspectable artefacts (logs, service states, resource budgets, timelines).
