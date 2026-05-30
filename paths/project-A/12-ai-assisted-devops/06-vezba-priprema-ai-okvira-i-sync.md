# 06 — Vežba: priprema AI-okvira i sync (AI-assisted DevOps)

Ovo je meta-oblast: predmet rada je sam AI-okvir. Konsoliduješ agente/rules/skills koje su prethodne oblasti uvele i proveravaš da nema preklapanja.

## Cilj

- konsolidovan, ne-naduvan AI-okvir bez dupliranja pravila
- jasan kriterijum: kako se proverava (verifikuje) AI-generisani DevOps izlaz

## Deo A — Priprema/konsolidacija AI-okvira

### A1 — Mapiraj akumulirano

Izlistaj sve što su oblasti 01–11 uvele: `dockerfile-checks`, `gitlab-ci-checks`, `k8s-manifest-checks`, `terraform-checks`, `observability-checks`, kandidat-skill-ovi.

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: spoji preklapajuća pravila, obriši neiskorišćena, potvrdi da svako ima jasan trigger (glob/agent). Ovde je akcenat na **uklanjanju** suvišnog, ne dodavanju.

### A3 — Minimalni dodatak (primer)

```
# kandidat rule: ai-output-verification
Svaki AI-generisan artefakt (Dockerfile, manifest, .tf, pipeline) mora proći
domensku validaciju iz svoje oblasti PRE commit-a. AI-izlaz nije dokaz tačnosti.
```

## Deo B — Praktičan rad (sync)

### Provera kvaliteta AI-izlaza

Uzmi jedan AI-generisan artefakt iz radnog repoa i provuci ga kroz njegovu domensku validaciju (npr. `hadolint`, `kubeconform`, `terraform validate`). Zabeleži gde je AI pogrešio.

## Validacija — acceptance kriterijumi

- [ ] nema dva pravila koja rade istu stvar
- [ ] svako pravilo ima trigger (glob ili agent) i koristi se
- [ ] neiskorišćeni kandidat-skill-ovi obrisani ili opravdani
- [ ] bar jedan AI-izlaz verifikovan domenskim alatom
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Evo svih .cursor pravila/skills koje sam uveo do sada:
[lista]
Koja se preklapaju ili se ne koriste? Predloži spajanje/brisanje (ne menjaj automatski).
```
