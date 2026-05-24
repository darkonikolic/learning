# Feedback integration

**Theme:** After a **wrong turn**, the workflow must **absorb human correction** and **adapt**—not repeat the same failure mode quietly.

Anti-pattern: error detected → same prompt shape → same bad architecture.  

Strong pattern: error → **structured FEEDBACK** → **repair** → **re-verify** → update **alignment** artefacts (SPEC snippet, Rule note, Skill tweak backlog).

### Practice drill (controlled)

Instigate a **deliberately weak architecture** proposal from the assistant; you supply **concrete feedback** (boundary fix, constraint, risk); the next turn must show **traceable adaptation**—not cosmetic rephrase.

**LAB:** Every workflow run documents **minimum two feedback iterations** where useful—if the task was trivially correct, record “N/A + why” to avoid fake busywork.

### Human correction ownership

Name **who may correct** which layer (product vs security vs ops)—and ensure corrections **reach** the agent context explicitly (quoted feedback block, ticket link), not implicit chat memory only.

Tie to **rollback ownership**: if execution already happened, feedback may trigger retreat—not only forward patch.

### Checklist

- [ ] Feedback items have **acceptance**—closed when verification shows they landed in code/spec, not when the model apologises.  
