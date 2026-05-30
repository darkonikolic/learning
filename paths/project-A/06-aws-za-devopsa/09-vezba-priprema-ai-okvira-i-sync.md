# 09 — Vežba: priprema AI-okvira i sync (AWS osnove)

Postavljaš AI-okvir za rad sa AWS resursima i IAM politikama, pa konkretno verifikuješ identitet, dozvole i procenjuješ trošak pre nego što kreneš da praviš resurse.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo pravilo koje AI primenjuje svaki put kad predlaže IAM politike ili AWS resurse — least-privilege, bez wildcard-a, procena troška pre kreiranja.

**Pretpostavke za potvrdu:**
- AWS CLI je konfigurisan i radi (`aws configure list` prikazuje aktivan profil)
- Imaš pristup nalogu sa dovoljnim dozvolama za `sts:GetCallerIdentity` i `iam:SimulatePrincipalPolicy`
- Znaš ARN role/user-a sa kojim radiš

**Van opsega:**
- Kreiranje IAM korisnika ili rola — to je tema oblasti 06, ne ovog sync koraka
- Terraform za IAM — to dolazi u oblasti 08
- Production IAM hardening — ovde radimo razvojno okruženje

**Prompt za diskusiju:**
```
Treba mi IAM policy za [servis] sa minimalnim dozvolama za [akcije]. Daj least-privilege JSON i objasni svaki statement; bez wildcard-a gde nije nužno. Kolika je okvirna mesečna cena ako koristim [tip resursa, region, procenjeni sati/mesec]?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Verifikovati da AI alat razume IAM least-privilege i procenu troška, i da lokalni AWS pristup odgovara očekivanom identitetu.

**Fajlovi koji se diraju:**

- `CLAUDE.md` ili `.claude/rules/aws-checks.md` (Claude Code) — nova sekcija

**Fajlovi koji se NE diraju:**
- IAM politike u AWS konzoli — verifikacija je read-only u ovom koraku
- `~/.aws/credentials` — ne menjamo konfiguraciju, samo verifikujemo

**AI okvir za ovu oblast:**

Dodaj sekciju `## AWS validation checklist` u `CLAUDE.md`, ili napravi `.claude/rules/aws-checks.md`

Sadržaj pravila:
```
- IAM politike: least-privilege — specifični action-i, ne Action: "*".
- Nema wildcard Resource: "*" osim za akcije koje to zahtevaju (navedi razlog u komentaru).
- Pre kreiranja resursa: proceni mesečnu cenu (tip, region, sati/mesec).
- Prefer spot instance ili serverless (Lambda, Fargate) kad je moguće za dev okruženje.
- Svaki resurs nosi standardne tagove: env, project, owner.
```

Anti-sprawl: dodaj samo ako se IAM analiza i cost check ponavljaju kroz više oblasti. AWS se ponavlja kroz oblasti 06, 07, 08, 09 — opravdano.

**Acceptance criteria:**
- [ ] `aws sts get-caller-identity` potvrđuje očekivani Account ID i ARN
- [ ] IAM simulacija za target akcije ne vraća `implicitDeny` za potrebne dozvole
- [ ] IAM simulacija ne pokazuje `*:*` dozvolje (nema admin pristupa gde nije potrebno)
- [ ] okvirni mesečni trošak procenjen i zapisan pre kreiranja bilo kog resursa
- [ ] sync zapisan u decision log

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Verifikovati AWS identitet i dozvole CLI-jem
- Simulirati IAM politiku za target akcije
- Proceniti trošak za planirane resurse
- Napraviti aws-checks rule za AI alat

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

```bash
# 1. Verifikuj identitet — koji nalog i role aktivno koristiš
aws sts get-caller-identity

# 2. Simuliraj IAM dozvole — zameni ARN i akcije sa stvarnim vrednostima
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT_ID:user/USERNAME \
  --action-names s3:PutObject s3:GetObject ec2:DescribeInstances

# 3. Proveri aktivne service quotas za region koji koristiš
aws service-quotas list-service-quotas --service-code ec2 \
  --query "Quotas[?QuotaName=='Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances'].{Name:QuotaName,Value:Value}"

# 4. Procena troška (alternativa AWS Pricing Calculator — CLI varijanta)
aws pricing get-products \
  --service-code AmazonEC2 \
  --filters "Type=TERM_MATCH,Field=instanceType,Value=t3.micro" \
             "Type=TERM_MATCH,Field=location,Value=EU (Ireland)" \
  --max-results 1 \
  --query "PriceList[0]"
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- aws sts get-caller-identity: potvrđuje očekivani Account ID i ARN
- IAM simulacija: nema implicitDeny za potrebne akcije
- IAM simulacija: nema *:* dozvola
- mesečna cena procenjena pre kreiranja resursa

Evo outputa komandi:
[ovde lepiš stvarni output svakog koraka]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali (npr. koja IAM akcija nedostaje, koji wildcard postoji)?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Otvori AWS konzolu → IAM → Users/Roles → pronađi aktivan identitet → klikni Permissions | Lista politika ne sadrži `AdministratorAccess` osim ako je to svesna odluka za dev nalog |
| 2 | U IAM → Policy Simulator: izaberi user/role, unesi `s3:DeleteBucket` kao akciju, pokreni simulaciju | Rezultat je `Deny` — user ne sme brisati bucket-e |
| 3 | Otvori AWS Cost Explorer (Billing → Cost Explorer → Enable ako nije) → Last 30 days | Vidiš troškove po servisu; nema neočekivanih resursa koji troše novac |
| 4 | Otvori EC2 → Instances — proveri da nema running instance koje si zaboravio | Lista je prazna ili sve instance su expected |
| 5 | Otvori AWS Pricing Calculator (calculator.aws) — unesi t3.micro, eu-west-1, 730 sati | Mesečna cena je prikazana i blizu $7-8 (on-demand); zabeleži za decision log |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — AWS osnove sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
