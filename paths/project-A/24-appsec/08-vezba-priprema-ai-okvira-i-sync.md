# 08 — Vežba: priprema AI-okvira i sync (AppSec)

Pripremaš AI-okvir za bezbednost aplikacije (SAST, dependency scan, DAST, security headers), pa pokrećeš provere.

## Cilj

- okvir koji ugrađuje AppSec u pipeline (shift-left)
- dokazano: SAST/dependency/DAST bez critical nalaza, headers postavljeni

## Deo A — Priprema AI-okvira za AppSec

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Security persona | da | `/security-trainer` |
| CI/secrets checklist | da | `gitlab-ci-checks`, `secrets-hygiene` |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `appsec-checks` (SAST + dependency scan u CI; security headers; OWASP Top 10 svest). Uvedi — bezbednost aplikacije je presečna briga.

### A3 — Minimalni dodatak (primer)

```
# kandidat: appsec-checks
- CI faza za SAST (semgrep) i dependency scan; build pada na critical.
- Security headers: CSP, HSTS, X-Content-Type-Options, X-Frame-Options.
- Validacija/escaping inputa po OWASP Top 10 (injection, XSS).
```

## Deo B — Praktičan rad (sync)

### Pokretanje provera

```bash
docker run --rm -v "$PWD":/src returntocorp/semgrep semgrep --config=auto /src
docker run --rm -v "$PWD":/src aquasec/trivy fs /src      # dependency CVE
docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t https://<host>
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `semgrep` bez critical nalaza
- [ ] dependency scan bez critical CVE (ili svesno prihvaćeno)
- [ ] ZAP baseline bez high-risk alarma
- [ ] security headers prisutni
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Evo CI konfiguracije i app endpoint-a. Dodaj SAST + dependency scan fazu
koja obara build na critical i predloži minimalan set security headers. Objasni.
```
