# Human-in-the-loop (HITL)

For when to stop Claude, bypass AI, and calibrate trust, see `05-agent-orchestration-and-governance/09-human-authority-and-override.md`.

Human-in-the-loop is the industry term for keeping a human in the approval chain for AI decisions. Not every decision requires human approval — but some decisions must never be made by an agent alone. The skill is knowing which is which.

---

## The HITL spectrum

From full autonomy to full human control:

| Mode | Description | When to use |
|------|-------------|------------|
| Full-auto | Agent acts with no human involvement | Never for irreversible actions |
| Human-on-the-loop | Human monitors, can intervene, but doesn't approve each step | Well-understood, low-risk routine tasks |
| Human-in-the-loop | Human must approve at defined gates before proceeding | Phase gates, irreversible actions, novel situations |
| Human-in-command | Human approves every individual agent action | High-security, compliance-required, untested agents |

The appropriate mode depends on: the reversibility of actions, the blast radius of failures, the agent's track record on similar tasks, and the regulatory or business requirements.

Starting position for new agents: human-in-the-loop. Move toward human-on-the-loop as the agent demonstrates reliability on a class of tasks.

---

## When HITL is non-negotiable

Some situations require human approval regardless of agent confidence or convenience:

**Irreversible actions.** Any action that cannot be undone without significant effort belongs in human-in-the-loop.
- `git push`: once pushed, the remote is changed. Others may have pulled. Force-pushing causes problems.
- Database migrations: once run on production, rollback is complex.
- File deletion: `rm -rf` has no undo.
- Email or notification sends: cannot unsend.

**High blast radius.** Actions affecting many users, many systems, or large amounts of data.
- Deploying to production.
- Changing shared configuration.
- Any operation that scales its impact beyond the developer's machine.

**Low confidence.** When the agent indicates uncertainty or when the task is in a domain it hasn't handled before.
- Novel edge case not covered by the SPEC.
- Ambiguous requirement where two interpretations are equally valid.
- Conflicting constraints where the resolution is not obvious.

**Trust boundary crossing.** Any action that crosses from a trusted environment to a less-trusted or more-trusted environment.
- Reading from/writing to production when working in development.
- Accessing credentials or secrets.
- Calling external APIs with side effects.

---

## Approval gates in the workflow

The structured Claude Code workflow encodes HITL as explicit approval gates. These are the checkpoints where human review is required before the next phase begins.

**Gate 1: frame brief approval (before plan).**
You review `docs/plans/<phase>-context.md` — goals, constraints, non-goals, risks — and confirm it is correct before planning begins. Approving the frame brief means: "this is the right problem and these are the right constraints."

**Gate 2: phase plan approval (before execute).**
You review `docs/plans/<phase>-plan.md` — tasks, waves, acceptance criteria — and confirm it is the right plan before any code is written. Approving the phase plan means: "these tasks, in this order, will correctly implement the goal."

**Gate 3: Verification pass (before ship).**
You run the verification stage and confirm the implementation matches the SPEC before creating a PR. Approving verification means: "the code does what the SPEC says it should do."

These three gates mean no code ships without three human checkpoints. Skipping them speeds up the current session and increases the risk of wrong code reaching the codebase.

The temptation to skip: "I know what the plan should be, I'll just let execute run." The cost of skipping: discovering three waves into execution that the plan was wrong, requiring manual correction of partially-completed work.

---

## Confidence and escalation

A well-configured agent can operate in human-on-the-loop mode for routine tasks where it has demonstrated reliability. Escalate to human-in-the-loop when:

- The situation is novel (not covered by training on similar tasks).
- The SPEC is ambiguous (two valid interpretations, different outcomes).
- The action is irreversible.
- The agent's confidence is explicitly low (it says "I'm not sure" or asks clarifying questions).
- The output of the previous agent is wrong (escalate before continuing).

**Escalation mechanism in Claude Code:**

When Claude Code encounters a situation requiring human input mid-task, it stops and asks. This is not a failure — it is the correct behavior. The agent is surfacing a decision that needs human judgment.

Common escalation triggers:
- "This file already exists — should I overwrite it?"
- "The SPEC says X but the existing code does Y — which should I follow?"
- "I could implement this two ways — want me to continue or choose?"

These are HITL moments. Answer them deliberately. Do not click through without reading.

---

## HITL anti-patterns

**Auto-approving everything.** Accepting all permission prompts without reading them defeats the purpose. The prompts are the HITL gate.

**Skipping verification.** Marking a task complete because the agent said "done" without verifying the output. The agent summary is not evidence of correctness.

**Skipping phase plan review.** Starting execute immediately after plan because the plan "looks fine." The review is where you catch misunderstandings before they become wrong code.

**Inconsistent HITL.** Applying HITL to some decisions and not others based on how busy you are. Risk does not vary with your schedule.

---

## HITL configuration in Claude Code

The settings.json deny list is a form of HITL configuration. By putting `git push` in deny, you ensure it always requires explicit human action — the agent cannot push without you doing it manually.

The allow list is the set of actions where you have decided human-on-the-loop is sufficient. You are comfortable with `go test ./...` running without explicit approval because you understand what it does and its blast radius is zero.

The design principle: deny list items = human-in-the-loop (human must take the action). Allow list items = human-on-the-loop (human monitors, can intervene, but not prompted). Everything else = human-in-the-loop (prompted per-instance).

---

## HITL in practice: task-api examples

**Scenario 1: Claude wants to run `go test ./...`.**

This is in the allow list. It is human-on-the-loop. Claude runs it without prompting. You can see the output. You are monitoring. If something unexpected happens, you intervene. This is appropriate because go test is: read-only side effects, local, reversible, zero blast radius.

**Scenario 2: Claude wants to run `git push origin main`.**

This is in the deny list. Human-in-the-loop. Claude cannot do this. You must run it manually. Even if you type "please push the branch," Claude should refuse and remind you to push manually. This is appropriate because git push is: remote state change, affects teammates, hard to fully undo.

**Scenario 3: Claude asks "The SPEC says return 404 if task not found, but existing code returns 400 — which should I follow?"**

This is a mid-task escalation. Claude is surfacing an ambiguity that requires human judgment. The SPEC and the code disagree. Which is ground truth?

Your job: answer the question deliberately. "The SPEC is ground truth. Update the code to return 404." This is human-in-the-loop at the decision boundary — Claude identified the decision, you made it.

**Scenario 4: The frame step produces a context brief that misunderstands the goal.**

`docs/plans/<phase>-context.md` says "implement a persistence layer for tasks." Your goal was "add in-memory sorting to the existing list."

If you approve the frame brief without reading it: plan step plans a database migration. Execute starts building a persistence layer. You notice three waves in and everything is wrong.

If you read the frame brief before approving: you catch the misunderstanding at Gate 1. You correct it. Plan step plans the right thing.

The gate's value: catching misunderstandings before they become wrong code.

---

## HITL vs automation: where the line belongs

The question is not "can this be automated?" Everything can be automated. The question is "should this be automated?" meaning: "is the blast radius low enough and the reversibility high enough that automation is safe?"

For task-api development with a single developer:
- Automation is appropriate for: build, test, read operations, local file edits.
- Human-in-the-loop is appropriate for: git push, new PR creation, production operations.
- The line sits after local verification, before remote state change.

For a team working on a shared codebase:
- The line moves left (more things require human approval) because the blast radius of any action is larger — it affects the whole team.

For a solo developer working in a completely sandboxed environment with automatic rollback:
- The line can move right (more things can be automated) because the reversibility of any action is higher.

The principle: blast radius and reversibility determine where the human-in-the-loop line sits. Adjust deliberately, not by accident.

---

## Checklist

- [ ] I know the four HITL modes and when each applies.
- [ ] I know the three workflow approval gates: frame brief, phase plan, verification.
- [ ] I know the four conditions that make HITL non-negotiable: irreversible, high blast radius, low confidence, trust boundary crossing.
- [ ] My settings.json deny list reflects my human-in-the-loop decisions.
- [ ] I never approve a permission prompt without reading what it's approving.
- [ ] I review `docs/plans/<phase>-plan.md` before running execute, not after.
