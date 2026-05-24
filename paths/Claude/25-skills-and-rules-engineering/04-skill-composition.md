# Skill composition

**Theme:** Serious work **stacks** Skills—one investigation rarely fits a single silo.

### Pattern

```
 Problem statement + frozen constraints
       → PRIMARY skill (e.g. architect)
             → SUPPORT skills (e.g. mysql-review + ops-debug)
                   → consolidated outputs merged by human orchestrator OR explicit synthesis step inside procedure
```

**Example thread**

Refund **latency**:

`mysql-review` (plans, locking, replicas)  

`ops-debug` (saturation signals, rollout correlation)  

`symfony-architect` (CQRS/read path coherence)

Mandatory **LAB heuristic:** orchestrate **two to three** Skills per task when realistic—with notes on how outputs merge without contradicting Rules.

Discuss **routing ownership**: orchestrator persona picks order—avoid parallel contradictory instructions without merge discipline.

Discuss **evaluation**: compose only Skills whose individual rubrics stay compatible—cheap composition otherwise hides weak single Skills.

### Checklist

- [ ] Composed runs still respect **approval matrix**—no Skill bypass of human-only lanes.  
