# Unit 1 — Scope: caching as a correctness and economics decision

**Framing:** **`"I'll add Redis"`** is rarely free—it binds you to staleness envelopes, invalidation paths, thundering herds, and incident stories.

Themes to articulate as architecture (not trivia):

```
read-through • cache-aside • write-behind/overwrite caricatures responsibly  
TTL philosophies + misuse of immortal negative caching caricature caution  
invalidate-on-write vs lazy expiry trade spectrum  
warming / cold spikes after rollout honesty  
stampede mitigation ideas (locking, probabilistic early refresh, hedging sparingly…)  
logical namespacing for multi-tenant blast-radius isolation
```

Bridge mentally to **`PHP-Symfony / Redis`** exercises in source material without rewriting implementation depth here.

