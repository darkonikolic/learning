# 11 — Vežba: priprema AI-okvira i sync (Terraform na AWS)

Proširuješ AI-okvir za Terraform sa AWS-specifičnim bezbednosnim pravilima, pa validiraš plan i pokrećeš security scan pre `apply`-a.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Dopunjujemo postojeći `terraform-checks` rule iz oblasti 05 sa AWS-specifičnim stavkama — enkripcija, public access, security group pravila. Onda verifikujemo da `terraform plan` nema iznenađenja i da security scan prolazi.

**Pretpostavke za potvrdu:**
- `terraform-checks` rule iz oblasti 05 već postoji (Cursor ili Claude Code)
- `terraform init` je uspešno pokrenuto i remote backend je konfigurisan
- Imaš pristup AWS nalogu gde se resursi kreiraju
- checkov ili tfsec je dostupan (Docker je OK)

**Van opsega:**
- `terraform apply` bez prethodnog pregleda plana — nikad
- Kreiranje novog Terraform modula od nule — to je sadržaj oblasti 08, ovo je sync korak
- Postavljanje CI/CD pipeline-a sa security scan-om — dolazi u kasnijim oblastima

**Prompt za diskusiju:**
```
checkov/tfsec prijavljuje: [nalaz]
Evo modula: [.tf kod]
Da li je nalaz realan rizik ovde i koji je minimalan fix bez rušenja arhitekture?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Proširiti AI-okvir AWS security pravilima i verifikovati da plan i security scan prolaze pre bilo kakvog `apply`-a.

**Fajlovi koji se diraju:**
- `.cursor/rules/terraform-checks.mdc` — dopuna postojećeg rule-a (Cursor)
- `CLAUDE.md` ili `.claude/rules/terraform-checks.md` — dopuna sekcije (Claude Code)
- `.tf` fajlovi u oblasti — samo za validaciju, ne za izmenu sadržaja u ovom koraku

**Fajlovi koji se NE diraju:**
- `terraform.tfstate` — nikad ručno
- `backend.tf` — menja se samo svesno, ne kao deo ovog koraka
- AWS konzola — read-only verifikacija posle apply-a

**AI okvir za ovu oblast:**

> **Cursor:** dopuni `.cursor/rules/terraform-checks.mdc` AWS sekcijom (globs: `paths/project-A/**/*.tf`)
> **Claude Code:** dopuni sekciju `## Terraform validation checklist` u `CLAUDE.md` ili `.claude/rules/terraform-checks.md`

Sadržaj pravila — dodati uz postojeća iz oblasti 05 (isti za oba alata):
```
# AWS-specifično (dopuna terraform-checks)
- S3 bucket: versioning uključen, public access blocked, server-side enkripcija (AES256 ili KMS).
- EBS volume: encrypted = true.
- RDS: storage_encrypted = true, backup_retention_period >= 7.
- Security group: bez 0.0.0.0/0 na portu 22 ili 3306 — pristup samo kroz bastion ili SSM.
- IAM role: jedna po servisu, ne deljeni admin role; inline policy samo ako je jedinstven.
- Nema aws_iam_access_key resursa sa hardcoded secret-om.
```

Anti-sprawl: ovo je dopuna postojećeg `terraform-checks` rule-a iz oblasti 05, ne novi rule. Ne praviti `aws-terraform-checks` odvojeno.

**Acceptance criteria:**
- [ ] `terraform plan -out=tfplan` prikazuje samo očekivane create/change/destroy operacije (nema iznenađenja)
- [ ] `checkov` ili `tfsec` bez HIGH ili CRITICAL nalaza — ili svaki suppressed sa komentarom i razlogom
- [ ] nema resursa sa `public` pristupom koji ne treba da budu javni (S3, RDS, EC2 bez namere)
- [ ] security group pravila ne otvaraju 22/3306 prema `0.0.0.0/0`
- [ ] sync zapisan u decision log

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Dopuniti terraform-checks rule AWS security stavkama
- Pokrenuti terraform plan i pregledati output
- Pokrenuti checkov/tfsec i rešiti HIGH/CRITICAL nalaze
- Verifikovati u AWS konzoli posle apply-a

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta
> **Claude Code:** direktno u terminalu

```bash
# 1. Osvezi provider-e i module
terraform init -upgrade

# 2. Generiši plan i sačuvaj u fajl (obavezno pre apply-a)
terraform plan -out=tfplan

# 3. Pregled plana u čitljivom formatu
terraform show -no-color tfplan | grep -E "^  # |will be created|will be destroyed|must be replaced"

# 4. Security scan — checkov (Docker varijanta)
docker run --rm -v "$PWD":/src bridgecrew/checkov -d /src --quiet

# 5. Alternativno: tfsec
docker run --rm -v "$PWD":/src aquasec/tfsec /src

# 6. Tek posle pregleda plana i čistog scana — apply
terraform apply tfplan
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- terraform plan: samo očekivane operacije (bez iznenađenja)
- checkov/tfsec: bez HIGH/CRITICAL nalaza ili suppressed sa razlogom
- nema nenamerno javnih resursa
- security group ne otvara 22/3306 prema 0.0.0.0/0

Evo outputa komandi:
[ovde lepiš terraform plan output i checkov/tfsec output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — koji nalaz je realan rizik i koji je minimalan fix?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | AWS konzola → VPC → Your VPCs → pronađi VPC po tagu | VPC postoji sa CIDR blokom koji odgovara `main.tf` konfiguraciji |
| 2 | VPC → Subnets — filtriraj po VPC ID | Vidljivi su svi subnets (public i private) sa ispravnim CIDR-ovima i availability zones |
| 3 | EC2 → Security Groups → pronađi SG po imenu → Inbound rules | Port 22 nije otvoren prema `0.0.0.0/0`; pristup je ograničen na specifičan CIDR ili SG |
| 4 | S3 → pronađi bucket → Permissions tab → Block public access | Sva četiri "Block public access" podešavanja su `On` |
| 5 | AWS konzola → EC2 (ili RDS) → pronađi resurs → Storage tab | EBS volume ili RDS storage prikazuje `Encrypted: Yes` |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/terraform-aws-tooling.md` ili `CLAUDE.md`

```
## [datum] — Terraform AWS sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
