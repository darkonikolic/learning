# Node scheduling — affinity, taints, tolerations

**Theme:** Scheduling is **silent SLO negotiation** selecting failure domains, noisy-neighbour buffering, heterogeneous capacity islands.

### Affinity dimensions

Required vs preferred affinity / anti-affinity rules  

Spread across zones / racks / SKU pools  

Workload colocation optimisation vs blast radius tradeoff calculus

### Taints communicate intent

Dedicated pools (GPU / high IO / confidential compute) eviction pressure  

Controlled drain preparation surfaces via `NoExecute` escalating urgency

### Tolerations are opt-in exemptions

Danger: silent scheduling onto degraded capacity when toleration breadth too loose.

Labs: perturb node labels / taints in safe sandbox predicting pod migration path before production experiments.

Storyboard outage: accidental **over-constrained affinity** starving scheduling vs **under-constrained spreading** collapsing zone.

### Checklist

- [ ] Document intentional **remainder / overflow pool** behaviours when saturation crosses threshold—avoid infinite Pending mysteries.  
