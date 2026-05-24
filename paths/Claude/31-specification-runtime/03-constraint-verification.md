# Constraint verification

**Theme:** **Constraints survive implementation** — library bans, layering, forbidden patterns—they are gates, not blog decoration.

Stereotypical failure:

Executable constraint: Go stack — **sqlx**, **ORM prohibited** assistant still scaffolds GORM out of convenience habit.

Symfony **CQRS ownership** rule: projections must not import write-side internals—verification catches leaky imports symbolically via arch tests if you introduce them pragmatically eventually.

Go **repository layer** purity vs accidental domain logic bleed—verification checklist crosses package boundaries ethically.

### Per-task rehearsal

Enumerate **constraints** section inside worksheet **before coding**.  

After implementation: **constraint consistency sweep** — static checks, reviewer rubric snippet, scripted grep bans where brittle but valuable.

Discuss **verification ownership**: author ≠ sole verifier optionally—parity with human review / second agent persona ethically.

Discuss **repair workflow**: violating constraint triggers rollback-first instinct if deployed—then refactor forward.

### Checklist

- [ ] Every hard constraint names **verification artifact**—even if temporarily manual scripted command recorded in workbook.  
