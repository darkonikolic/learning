# 07 — Vežba: priprema AI-okvira i sync (GitLab CI)

Pripremaš AI-okvir za rad sa `.gitlab-ci.yml`, pa praktično validiraš pipeline.

## Cilj

- okvir koji pokriva pisanje/validaciju GitLab CI konfiguracije
- `.gitlab-ci.yml` koji prolazi CI Lint bez grešaka

## Deo A — Priprema AI-okvira za CI

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| Validacija YAML/CI | ? | — |

### A2 — Odluka (anti-sprawl)

Preko `/system-maintainer` + `process-feedback`: da li dodati glob-rule za `**/.gitlab-ci.yml` (stages, `rules:`, cache, artifacts checklist) ili je pokriveno. CI se ponavlja (02, 10, 22) → minimalan dodatak je opravdan.

### A3 — Minimalni dodatak (primer)

```
# .cursor/rules/gitlab-ci-checks.mdc — globs: paths/project-A/**/.gitlab-ci.yml
- Svaki job ima `stage`, `rules:` (ne `only/except`), i jasne `needs:`.
- Path-based `rules: changes:` da se ne build-uje sve pri svakom commitu.
- Bez plaintext secrets; koristi CI/CD variables (masked, protected).
- `interruptible: true` za feature grane.
```

## Deo B — Praktičan rad (sync)

### Validacija CI konfiguracije

```bash
# GitLab CI Lint preko glab CLI (ili UI: CI/CD → Editor → Lint)
glab ci lint
# ili YAML sanity:
docker run --rm -v "$PWD":/w -w /w cytopia/yamllint .gitlab-ci.yml
```

Popravi nalaze po checklist-i, pa zapiši sync u `decision_log.md`.

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `glab ci lint` (ili UI Lint) prolazi
- [ ] nema plaintext secrets u konfiguraciji
- [ ] sync zapisan

## AI workflow

```
Evo mog .gitlab-ci.yml i CI Lint greške:
[konfiguracija] [greška]
Objasni uzrok i minimalan fix; da li `rules:` treba prepravku?
```
