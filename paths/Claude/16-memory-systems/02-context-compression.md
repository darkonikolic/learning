# Context compression

**Theme:** You do not ship the repository as an undifferentiated slab into the model—**curated signal** wins over brute token dumping.

Contrast:

| Poor | Strong |
|------|--------|
| Huge undifferentiated paste (thousands of incidental lines, whole trees) | Tight packet: **ownership**, **constraints**, **boundaries**, **NFR**/SLO only where decisive |

Practice slices:

Symfony **CQRS** flow refactor planning—articulate aggregates + command/query ownership without vending entire vendors.  

Go **queue subsystem** tweaks—expose contracts (ACK semantics, retry policy knobs) crisply versus entire module trees.

Compression tactics you rehearse aloud:

Headline invariant bullets  

Structural diagrams shrunk to captions + symbol names already in repo    

Pointer references (`SERVICE.md`, RULE ids, SPEC anchors) pulling truth lazily   

Strip historical chatter duplicated in git archaeology unless episodic hinge matters now

LAB: Take one scenario task twice—**(A)** maximal naive context dump intuition vs **(B)** compressed packet—observe qualitative answer precision and iteration counts; note subjective token budgeting learnings introspectively (you need not quantify unless tooling available).

Discuss **risk**: over-compression hides critical negative knowledge (“we removed feature X”—must remain discoverable episodically).

### Checklist

- [ ] Compression **never deletes** contradictory historical facts silently—migrate them to episodic artefacts if still decision-relevant.  
