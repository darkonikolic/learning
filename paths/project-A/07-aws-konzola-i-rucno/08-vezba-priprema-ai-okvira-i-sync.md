# 08 — Vežba: priprema AI-okvira i sync (ručno preko konzole)

Postavljaš AI-okvir koji te vodi kroz ručno pravljenje resursa u AWS konzoli, pa verifikuješ CLI-jem da resurs postoji sa tačnim parametrima i dokumentuješ ga za kasniji prevod u Terraform.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo checklist koji AI primenjuje kada radiš ručne promene u konzoli — koje parametre zabeležiti da bi se resurs verno preveo u Terraform bez ručnog istraživanja posle.

**Pretpostavke za potvrdu:**
- Imaš pristup AWS konzoli i CLI-ju za isti nalog
- Resurs je već napravljen ručno u konzoli (EC2, Security Group, VPC, ili slično)
- Cilj je razumevanje pre automatizacije — ne pravljenje resursa koji ostaju zauvek

**Van opsega:**
- Pisanje Terraform koda za taj resurs — to je oblast 08
- Automatizacija konzolnih koraka skriptom — to dolazi kasnije
- Production hardening ručno kreiranog resursa — ovde radimo dev/learning okruženje

**Prompt za diskusiju:**
```
Napravio sam ručno [resurs, npr. EC2 t3.micro u eu-west-1] sa parametrima [AMI ID, subnet, SG, tagovi]. Koje parametre moram da zabeležim da bih ga kasnije verno opisao u Terraform-u? Koji Terraform resource tip i koji argumenti odgovaraju ovim konzolnim opcijama?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Verifikovati da ručno napravljen resurs postoji sa tačnim parametrima i da je zabeležen u formatu koji omogućava Terraform prevod bez gubitka informacija.

**Fajlovi koji se diraju:**
- `CLAUDE.md` — nova sekcija (ako se checklist ponavlja kroz više modula)
- `.claude/rules/rucni-resurs-checks.md` (alternativa CLAUDE.md sekciji)

**Fajlovi koji se NE diraju:**
- Terraform fajlovi — ne pišemo Terraform u ovoj oblasti, samo dokumentujemo
- AWS konzola — samo čitamo/verifikujemo, ne menjamo resurse u ovom koraku

**AI okvir za ovu oblast:**

Dodaj sekciju `## Ručni resurs — checklist za Terraform prevod` u `CLAUDE.md`

Sadržaj pravila:
```
- Za svaki ručno kreiran resurs zabeleži: ID/ARN, region, tip, ključne parametre.
- Zapiši zavisnosti: koji VPC, subnet, SG, IAM role resurs koristi.
- Mapiraj na Terraform resource tip (npr. aws_instance, aws_security_group).
- Zabeleži tagove — moraju biti isti u Terraform kodu.
- Ako resurs ima state (running/stopped), zabeleži i njega.
```

Anti-sprawl: ručni rad je specifičan za oblast 07 — uvedi pravilo samo ako se gubi trag konfiguracije kroz više modula. Inače je dovoljan jednokratni zapis.

**Acceptance criteria:**
- [ ] `aws ec2 describe-instances` ili odgovarajući `describe-*` vraća resurs sa tačnim parametrima
- [ ] zapis sadrži: ID/ARN, region, tip, ključne parametre, zavisnosti, Terraform resource tip
- [ ] tagovi na resursu u konzoli podudaraju se sa onim što je zabeleženo
- [ ] sync zapisan u decision log

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Verifikovati ručno kreiran resurs CLI-jem
- Izvući sve parametre potrebne za Terraform prevod
- Zabeležiti u strukturiranom formatu
- Napraviti AI checklist ako se situacija ponavlja

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

```bash
# 1. Verifikuj EC2 instancu po tagu (zameni <ime> sa stvarnim tagom)
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=<ime>" \
  --query "Reservations[*].Instances[*].{ID:InstanceId,Type:InstanceType,State:State.Name,AMI:ImageId,Subnet:SubnetId,SG:SecurityGroups,Tags:Tags}" \
  --output table

# 2. Verifikuj Security Group
aws ec2 describe-security-groups \
  --group-ids <sg-id> \
  --query "SecurityGroups[*].{ID:GroupId,Name:GroupName,VPC:VpcId,Inbound:IpPermissions,Outbound:IpPermissionsEgress}" \
  --output json

# 3. Verifikuj VPC i subnet ako su relevantni
aws ec2 describe-vpcs --vpc-ids <vpc-id> --output table
aws ec2 describe-subnets --subnet-ids <subnet-id> --output table

# 4. Izvuci sve tagove sa resursa
aws ec2 describe-tags \
  --filters "Name=resource-id,Values=<instance-id>" \
  --output table
```

Zabeleži output po checklist-i u `docs/decisions/rucni-resursi.md` ili `.claude/memory/decisions.md`.

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- describe-instances vraća resurs sa tačnim parametrima
- zapis sadrži ID/ARN, region, tip, ključne parametre, zavisnosti, Terraform resource tip
- tagovi se podudaraju između konzole i zapisa

Evo outputa komandi:
[ovde lepiš stvarni output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — koji parametar nedostaje ili se ne podudara?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | AWS konzola → EC2 → Instances → pronađi instancu po imenu ili ID-u | Instanca postoji, State je `running` ili `stopped` (ne `terminated`) |
| 2 | Klikni na instancu → Details tab → proveri AMI ID, Instance type, Subnet ID | Vrednosti se podudaraju sa onim što si zabeležio u dokumentu |
| 3 | Klikni na Security group link → Inbound rules | Pravila su tačno ona koja si kreirao — nema neočekivanih otvorenih portova |
| 4 | Tags tab na instanci | Tagovi `env`, `project`, `owner` postoje i imaju ispravne vrednosti |
| 5 | Otvori zapis u `docs/decisions/rucni-resursi.md` i poredi sa konzolom red po red | Svaki parametar u zapisu odgovara stvarnom stanju u konzoli; nema praznina koje bi blokirale Terraform prevod |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Ručni resurs sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
