# 09 — Vežba: priprema AI-okvira i sync (Terraform)

Postavljaš AI-okvir za pisanje i validaciju Terraform koda, pa verifikuješ da lokalna konfiguracija prolazi `fmt`, `validate` i `tflint` bez grešaka.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo pravila koja AI primenjuje svaki put kad radi na `.tf` fajlovima — remote state, pinovane verzije, tagovi, bez sekreta u kodu.

**Pretpostavke za potvrdu:**
- Terraform je instaliran i `terraform version` radi
- Postoji makar jedan `.tf` fajl u oblasti na kome možemo pokrenuti provere
- tflint je dostupan (direktno ili kao Docker image)

**Van opsega:**
- Pisanje novog Terraform koda — to je tema oblasti 08 i 14
- Postavljanje remote state backend-a od nule — pretpostavljamo da već postoji ili je oblast 05 to pokrila

**Prompt za diskusiju:**
```
Radim na Terraform kodu za project-A. Koje su najvažnije greške koje AI asistenti prave kada generišu .tf kod — verzije providera, state, secrets, tagovi? Koji automatski check bi odmah uhvatio te greške pre commit-a?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Napraviti AI-okvir za Terraform koji hvata greške u verzijama, state konfiguraciji i sekretima pre nego što kod uđe u repo.

**Fajlovi koji se diraju:**
- `.cursor/rules/terraform-checks.mdc` (Cursor)
- `CLAUDE.md` ili `.claude/rules/terraform-checks.md` (Claude Code)
- `.tf` fajlovi u trenutnoj oblasti — samo za validaciju, bez izmene sadržaja

**Fajlovi koji se NE diraju:**
- `backend.tf` — backend konfiguracija se menja samo svesno, ne kao deo ovog koraka
- `terraform.tfstate` — nikad ručno

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/terraform-checks.mdc` (globs: `paths/project-A/**/*.tf`)
> **Claude Code:** dodaj sekciju `## Terraform validation checklist` u `CLAUDE.md`, ili napravi `.claude/rules/terraform-checks.md`

Sadržaj pravila (isti za oba alata):
```
- required_version i required_providers pinovani (bez ~> Latest ili bez verzije).
- Nema secrets u .tf/.tfvars fajlovima koji se commit-uju u repo — koristi variable bez default-a ili external secrets manager.
- Svaki resurs nosi standardne tagove: env, project, owner.
- State je remote (S3 + DynamoDB lock), ne lokalni — terraform.tfstate ne sme biti u radnom direktorijumu osim privremeno tokom init.
- Moduli imaju source sa pinovanom verzijom ili lokalnim relativnim putem.
```

Anti-sprawl: Terraform se ponavlja kroz oblasti 05, 08, 14, 15 — ovaj rule opravdano postoji. Ne dodavaj poseban rule po oblasti.

**Acceptance criteria:**
- [ ] `terraform fmt -check -recursive` vraća exit code 0
- [ ] `terraform validate` prolazi bez greške
- [ ] `tflint` bez warning-a ili error-a
- [ ] nema `secret`, `password`, `token` kao hardcoded vrednosti u `.tf` fajlovima
- [ ] `required_version` i `required_providers` su pinovani
- [ ] sync zapisan u decision log

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Napraviti terraform-checks rule za AI alat
- Pokrenuti fmt, validate, tflint na .tf fajlovima oblasti 05
- Zabeležiti nalaze i doneti odluku o sprawl-u

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta
> **Claude Code:** direktno u terminalu

Pokreni validaciju redom — svaki korak mora proći pre sledećeg:

```bash
# 1. Proveri formatiranje (ne menja kod, samo prijavljuje)
terraform fmt -check -recursive

# 2. Proveri sintaksu i reference
terraform validate

# 3. Linting — statička analiza (Docker varijanta ako tflint nije instaliran)
docker run --rm -v "$PWD":/data -t ghcr.io/terraform-linters/tflint

# 4. Proveri da nema hardcoded secrets u .tf fajlovima
grep -rn --include="*.tf" -E "(password|secret|token|key)\s*=\s*\"[^\"]{6,}\"" .
```

Ako `terraform fmt -check` prijavi razlike, pokreni `terraform fmt -recursive` da automatski ispravlja, pa ponovo proveri.

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- terraform fmt -check -recursive: exit code 0
- terraform validate: prolazi bez greške
- tflint: bez warning-a
- nema hardcoded secrets u .tf fajlovima
- required_version i required_providers pinovani

Evo outputa komandi:
[ovde lepiš stvarni output svakog koraka]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali i koji je minimalan ispravan oblik?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Otvori bilo koji `.tf` fajl u oblasti i pogledaj `required_providers` blok | Verzija providera je eksplicitno pinovana (npr. `~> 5.0`, ne prazno) |
| 2 | Pretraži sve `.tf` fajlove za string `terraform.tfstate` | Fajl ne postoji u radnom direktorijumu ili je u `.gitignore` |
| 3 | Pokreni `grep -rn "backend" *.tf` ili pogledaj `backend.tf` | Backend je `s3`, ne `local` |
| 4 | Otvori `variables.tf` i proveri varijable za lozinke/tokene | Nema `default` vrednosti za osetljive varijable (tip je `sensitive = true` ili nema default-a) |
| 5 | Pokreni `tflint` i čitaj output red po red | Nula warning-a ili error-a, ili svaki suppressed sa komentarom `# tflint-ignore` i razlogom |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/terraform-tooling.md` ili `CLAUDE.md`

```
## [datum] — Terraform sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
