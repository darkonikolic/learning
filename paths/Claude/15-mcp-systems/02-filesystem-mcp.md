# Filesystem MCP

**Theme:** The assistant anchors work in **file truth**—“which file owns this invariant?” precedes pasted code glaciers.

CQRS-informed drill objects (Symfony mental model):

`Order`, `Payment`, `Refund` vertical slices  
- Trace **handlers / aggregates / projections** for each concept without crossing bounded contexts blindly.  

- Map **ownership** in words before speculative edits.
Go worker analogue: filesystem walk from **enqueue site → consumer implementation → retry policy module**.

### Operational chain you rehearse

```
 filesystem discovery (controlled roots)
       → dependency / import impact cones
               → enumerated impacted modules
                       → narrowed edit plan
```

### LAB invariant

Each proposed functional change cites **minimum three foreseeably impacted files** (configs, fixtures, migrations tangential counts if touched). If fewer exist, articulate **explicitly narrow blast**—don't fake breadth.

Discuss **risk** when broad glob searches traverse secrets or generated vendor trees unnecessarily.

### Checklist

- [ ] Search patterns avoid dumping entire binaries / artifact caches unintentionally via naive globs—scope consciously.  
