# 06 — Vežba: AI-assisted DevOps (meta-konsolidacija)

Konsoliduješ sve AI agente, rules i skills koje su oblasti 01–11 uvele, eliminišeš preklapanja i dokazuješ da svaki AI-generisani artefakt prolazi domensku validaciju pre primene.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Ovo je meta-oblast — predmet rada je sam AI-okvir. Mapiramo sve što je akumulirano, spajamo preklapajuća pravila, brišemo neiskorišćena, i definišemo jasan kriterijum za verifikaciju AI-izlaza.

**Pretpostavke za potvrdu:**
- Postoji barem 3–4 rule fajla iz prethodnih oblasti (dockerfile-checks, gitlab-ci-checks, k8s-manifest-checks, terraform-checks, observability-checks)
- Barem jedan AI-generisan artefakt postoji u radnom repou za testiranje
- Domenski alati su dostupni: `hadolint`, `kubeconform`, `terraform validate`, `glab ci lint`, `promtool`

**Van opsega:**
- Dodavanje novih pravila ili skill-ova — ovde je akcenat na uklanjanju, ne dodavanju
- Izmena aplikacionog koda
- Podešavanje novih agenata

**Prompt za diskusiju:**
```
Evo svih .cursor pravila/skills koje sam uveo do sada:
[lista fajlova iz .cursor/rules/ i skills/]

Koja se preklapaju ili se ne koriste?
Predloži spajanje/brisanje — ne menjaj automatski, samo predloži.
Potom: koji zadaci su pogodni za AI generisanje, a koji zahtevaju obaveznu ručnu verifikaciju?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene  
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Dobiti konsolidovan AI-okvir bez dupliranja, gde svako pravilo ima jasan trigger i gde postoji eksplicitan standard za verifikaciju AI-izlaza.

**Fajlovi koji se diraju:**
- `.cursor/rules/*.mdc` — spajanje ili brisanje preklapajućih rule fajlova
- `.cursor/skills/` — brisanje neiskorišćenih candidate skill-ova
- `CLAUDE.md` ili `.claude/rules/` — iste izmene za Claude Code

**Fajlovi koji se NE diraju:**
- `src/`, `terraform/`, `k8s/` — ne menjamo aplikacioni ili infra kod
- `docker-compose.yml` — stack ostaje nepromenjen

**AI okvir za ovu oblast:**

> **Cursor:** napravi ili ažuriraj `.cursor/rules/ai-output-verification.mdc`  
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/ai-output-verification.md`

Sadržaj pravila (isti za oba alata):
```
# ai-output-verification
- Svaki AI-generisan artefakt (Dockerfile, manifest, .tf, pipeline) mora proći
  domensku validaciju iz svoje oblasti PRE commit-a.
- AI-izlaz nije dokaz tačnosti — domenski alat je.
- Zadaci pogodni za AI: scaffolding, boilerplate, transformacije.
- Zadaci koji zahtevaju ručnu verifikaciju: sigurnosne konfiguracije, IAM policy,
  mrežne rute, produkcione tajne.
```

Anti-sprawl: ovo je jedini novi rule u ovoj oblasti — sve ostalo je spajanje postojećih.

**Acceptance criteria:**
- [ ] Nema dva rule fajla koja rade istu stvar
- [ ] Svako pravilo ima trigger (glob pattern ili agent) i aktivno se koristi
- [ ] Neiskorišćeni candidate skill-ovi su obrisani ili eksplicitno opravdani
- [ ] Barem jedan AI-generisan artefakt je prošao domensku validaciju u ovoj vežbi
- [ ] Zabeleženа je barem jedna greška ili propust koji je AI napravio
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Izlistati sve rule fajlove i mapirati preklapanja
2. Doneti odluku: spoji, obriši ili zadrži (za svaki par koji se preklapa)
3. Dodati ai-output-verification rule
4. Uzeti jedan AI-generisan artefakt i provući ga kroz domensku validaciju
5. Zabeležiti šta je AI pogrešio

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta ili `/system-maintainer`  
> **Claude Code:** direktno u terminalu

Izlistaj sve rule fajlove:

```bash
# Cursor
ls -la .cursor/rules/

# Claude Code
ls -la .claude/rules/
grep -n "## " CLAUDE.md | head -40
```

Pronađi duplicirana pravila (ručno ili uz AI pomoć), a zatim izvrši odluke o spajanju/brisanju.

Uzmi jedan AI-generisan artefakt i provuci kroz domensku validaciju:

```bash
# Dockerfile
hadolint Dockerfile

# Kubernetes manifest
kubeconform -strict manifest.yaml

# Terraform
terraform validate

# GitLab CI
glab ci lint

# Prometheus pravila
promtool check rules rules/*.yml
```

Zabeleži output — posebno greške koje su prošle AI generisanje, a uhvatio ih je domenski alat.

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- Nema dva rule fajla koja rade istu stvar
- Svako pravilo ima trigger i koristi se
- Neiskorišćeni kandidati obrisani ili opravdani
- Barem jedan AI artefakt prošao domensku validaciju
- Zabeleženа barem jedna AI greška

Evo outputa / diff-a / konfiguracije:
[ovde lepiš: ls output rule fajlova pre i posle, output domenskog alata na AI artefaktu, listu obrisanih/spojenih pravila]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Izlistaj sve rule fajlove u .cursor/rules/ ili CLAUDE.md | Nema dva fajla sa identičnom svrhom |
| 2 | Za svaki rule: proveri da li ima definisan trigger (glob/agent) | Svako pravilo ima jasan uslov aktivacije |
| 3 | Uzmi AI-generisan Dockerfile i pokreni `hadolint` | Output pokazuje prolaz ili konkretne greške (ne prazan) |
| 4 | Primeni AI sugestiju na jedan artefakt, pa pokreni domenski alat | Alat potvrđuje ispravnost ili prijavljuje tačan problem |
| 5 | Proveri da AI sugestija nije uvela regresiju u susednim fajlovima | Susedni testovi/lint prolaze |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`  
> **Claude Code:** zapiši u `docs/decisions/ai-devops-tooling.md` ili `CLAUDE.md`

```
## [datum] — AI-assisted DevOps sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
