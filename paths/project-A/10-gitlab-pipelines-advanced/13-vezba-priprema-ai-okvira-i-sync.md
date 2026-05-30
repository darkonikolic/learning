# 13 — Vežba: Napredni GitLab pipeline-i

Validiraš AI-okvir za napredne CI obrasce (DAG needs, child pipeline-i, review apps) i dokazuješ da pipeline prolazi lint i da zavisnosti smanjuju ukupno vreme.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Proširujemo postojeći CI okvir stavkama za review apps i DAG optimizaciju — ne pravimo novi rule, nego dopunjujemo `gitlab-ci-checks`.

**Pretpostavke za potvrdu:**
- `gitlab-ci-checks` rule već postoji iz oblasti 02
- Projekat ima MR-ove za koje review apps ima smisla
- Runner ima pristup Kubernetes-u ili Docker-u za ephemeral env

**Van opsega:**
- Potpuna migracija na child pipeline-e za sve servise
- Postavljanje review app domene i SSL sertifikata

**Prompt za diskusiju:**
```
Hoću review app po merge request-u sa auto-cleanup.
Daj minimalan `.gitlab-ci.yml` blok (environment + on_stop + auto_stop_in)
i objasni kako se čisti.
Potom objasni kako `needs:` DAG skraćuje vreme pipeline-a
u odnosu na klasični stage redosled.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene  
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Proširiti CI okvir za review apps i DAG, i dokazati da pipeline prolazi lint sa kraćim ukupnim vremenom.

**Fajlovi koji se diraju:**
- `.gitlab-ci.yml` — dodaješ review app job i `needs:` deklaracije
- `.cursor/rules/gitlab-ci-checks.mdc` ili `CLAUDE.md` — dopuna pravila

**Fajlovi koji se NE diraju:**
- `src/` — ovo je CI izmena, ne aplikacioni kod
- Ostali rule fajlovi — anti-sprawl, proširujemo postojeći

**AI okvir za ovu oblast:**

> **Cursor:** ažuriraj `.cursor/rules/gitlab-ci-checks.mdc`  
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili ažuriraj `.claude/rules/gitlab-ci-checks.md`

Sadržaj pravila (isti za oba alata):
```
# dopuna gitlab-ci-checks (advanced)
- Review app ima `environment.on_stop` i `auto_stop_in` (cleanup).
- Skupe faze (build/test) koriste `needs:` (DAG), ne čekaju ceo stage.
- Child pipeline-i za nezavisne servise umesto monolitnog joba.
- Pipeline vreme drugog run-a (sa cache-om) mora biti kraće od prvog.
```

Anti-sprawl: ne pravi novi rule — ovo je dopuna `gitlab-ci-checks` koji postoji od oblasti 02.

**Acceptance criteria:**
- [ ] `glab ci lint` prolazi bez grešaka
- [ ] Review app job ima `environment.on_stop` i `auto_stop_in`
- [ ] `needs:` deklaracije su prisutne na barem jednom skupom jobu
- [ ] Drugi pipeline run (cache topao) završava brže od prvog
- [ ] Artifacts su dostupni u GitLab UI posle uspešnog run-a
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Dopuniti gitlab-ci-checks pravila za review apps i DAG
2. Dodati review app job u .gitlab-ci.yml sa on_stop i auto_stop_in
3. Dodati needs: na build/test jobove
4. Pokrenuti glab ci lint
5. Pokrenuti pipeline dva puta i uporediti vreme

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta  
> **Claude Code:** direktno u terminalu

Lint pipeline konfiguracije:

```bash
glab ci lint
```

Pokreni pipeline i sačekaj da završi:

```bash
glab ci run
glab ci view --live
```

Vizuelno: CI/CD → Pipelines → DAG view — proveri da `needs:` zavisnosti formiraju očekivani graf, ne linearni redosled.

Pokreni drugi put da proveris cache benefit:

```bash
glab ci run
# Zabeleži vreme prvog i drugog run-a
```

Proveri artifacts:

```bash
glab ci artifact <job-name> --path <artifact-path>
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- glab ci lint prolazi bez grešaka
- Review app job ima environment.on_stop i auto_stop_in
- needs: deklaracije prisutne na skupim jobovima
- Drugi run brži od prvog (cache radi)
- Artifacts dostupni posle uspešnog run-a

Evo outputa / diff-a / konfiguracije:
[ovde lepiš: output glab ci lint, yaml blok review app joba, vreme prvog i drugog run-a, screenshot ili output artifacts]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Otvori MR i čekaj da pipeline završi | Review app URL se pojavljuje u MR-u |
| 2 | Klikni na review app URL | Aplikacija se otvara u browseru |
| 3 | Zatvori MR (ili klikni "Stop environment") | Review app okruženje se briše automatski |
| 4 | Otvori DAG view u GitLab CI/CD | Build i test jobovi startuju paralelno, ne čekaju ceo stage |
| 5 | Uporedi vreme prvog i drugog pipeline run-a | Drugi run završava brže (cache pomaže) |
| 6 | Otvori tab Artifacts za uspešan job | Artifact je dostupan za download |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`  
> **Claude Code:** zapiši u `docs/decisions/gitlab-ci-advanced-tooling.md` ili `CLAUDE.md`

```
## [datum] — GitLab napredni CI sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
