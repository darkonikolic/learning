---
name: create-learning-path
description: Turn a goal, current level, and available time into a structured learning roadmap with milestones and projects. Use when the user wants a new path, roadmap, or curriculum for a topic.
---

# Create learning path

## Input

- **Goal** — target capability or exam (e.g. "Go backend job", "Goethe B1").
- **Current level** — what the learner already knows.
- **Time available** — discuss in chat only; never write into trace files.

## Output

- **Roadmap** — ordered areas with explicit dependencies.
- **Milestones** — each with a deliverable that proves it.
- **Projects** — what to build at key checkpoints.

## Steps

1. Work backward from the goal to required capabilities.
2. Order capabilities by dependency, then by progressive difficulty.
3. Group into areas; attach one deliverable per milestone.
4. Map areas to the `paths/<Program>/NN-<area>/` layout.

## Constraints (from `plan-ucenja-ciljevi-i-rad.mdc`)

- Layout: `NN-<area>/` + `NN-<subtopic>.md`, no gaps in `NN`.
- On "create a path": scaffold **folders only** unless unit bodies are also requested.
- English content. No README. **No hours / weeks / per-day pacing inside trace `.md`** — keep pacing in chat.
