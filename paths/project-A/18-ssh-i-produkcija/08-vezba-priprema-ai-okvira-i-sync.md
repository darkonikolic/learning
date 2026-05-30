# 08 — Vežba: Priprema AI-okvira i sync (pristup produkciji)

Gradiš AI-okvir koji forsira bezbedan pristup produkciji isključivo kroz bastion host ili SSM Session Manager — bez otvorenog SSH porta (22) prema internetu — i verifikuješ da svaka sesija ostavlja trag u audit logu.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo šta smemo i ne smemo raditi u produkciji tokom ove vežbe, verifikujemo da SSH pristup ide jedino kroz bastion/SSM (ne direktno sa interneta), i potvrđujemo da audit log beleži sesije.

**Pretpostavke za potvrdu:**
- AWS IAM dozvole za SSM Session Manager postoje ili se mogu dodeliti
- Security grupe su pod našom kontrolom (ili imamo pristup uvidu)
- CloudWatch ili S3 je konfigurisan za SSM session logging (ili ćemo konfigurisati)
- Bastion host postoji ili koristimo SSM bez bastion-a

**Van opsega (u ovoj vežbi NE radimo):**
- Deploy ili izmena aplikacijskog koda u produkciji
- Restart produkcijskih servisa bez odobrenja
- Brisanje ili izmena produkcijskih podataka
- Ostavljanje otvorenih SSH sesija bez svrsishodnog razloga

**Prompt za diskusiju:**
```
Hoću pristup prod instancama bez otvorenog SSH porta (22) prema internetu.
Objasni SSM Session Manager pristup:
- Šta tačno treba u IAM politici da SSM Session Manager radi?
- Šta se menja u Security Group (šta se zatvara, šta ostaje)?
- Kako se sesije loguju u CloudWatch/S3 i šta se tačno beleži?
- Koja je razlika između bastion host i SSM pristupa — kada koristiti koje?
- Šta su privremeni (STS) kredencijali i zašto su bolji od trajnih?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Produkcijski pristup radi isključivo kroz SSM Session Manager ili bastion, bez ijednog SG pravila koje otvara port 22 prema 0.0.0.0/0, i svaka sesija se beleži u audit logu.

**Fajlovi koji se diraju:**
- `terraform/security-groups.tf` — ukloni pravilo 22/0.0.0.0/0 ako postoji
- `terraform/iam-ssm.tf` — IAM politika za SSM Session Manager pristup
- `terraform/ssm-logging.tf` — konfiguracija session logging-a u CloudWatch/S3

**Fajlovi koji se NE diraju:**
- `terraform/rds.tf` — baza ostaje kao jeste
- `k8s/` manifesti — ova vežba je o infrastrukturnom pristupu, ne K8s-u

**AI okvir za ovu oblast:**

Dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/prod-access-checks.md`

Sadržaj pravila:
```
- Bez SG pravila 0.0.0.0/0 na portu 22; pristup isključivo preko SSM Session Manager ili bastion.
- Svaki interaktivni pristup produkciji logovan (SSM session logging u CloudWatch/S3).
- Privremeni, ne trajni, kredencijali (STS assume-role) za ljude koji pristupaju prod.
- Bastion host je jedina dozvoljena ulazna tačka ako SSM nije opcija.
- Svaka prod sesija mora imati dokumentovan razlog (ticket, incident broj).
```

Anti-sprawl: proširi postojeće `cluster-security-checks` ako pokriva — novi rule samo ako ne pokriva prod access specifičnosti.

**Acceptance criteria:**
- [ ] `aws ec2 describe-security-groups` ne pokazuje nijedno pravilo `0.0.0.0/0` na portu 22
- [ ] `aws ssm start-session` uspešno otvara sesiju bez SSH ključa
- [ ] sesija se pojavljuje u CloudWatch Logs ili S3 audit logu posle zatvaranja
- [ ] bastion host je jedina EC2 instanca sa pristupom iz javne mreže (ako se koristi bastion model)
- [ ] Sync zapisan u `.claude/memory/decisions.md` ili `CLAUDE.md ## Decision log` / `CLAUDE.md`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Proveravamo sve SG na port 22/0.0.0.0/0 i dokumentujemo nalaze
- Konfigurišemo SSM Session Manager sa IAM politikama
- Konfigurišemo session logging u CloudWatch
- Verifikujemo da sesija radi i ostavlja audit trag

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Proveri da li postoji otvoreni SSH port prema internetu:

```bash
aws ec2 describe-security-groups \
  --query "SecurityGroups[].{Name:GroupName,Rules:IpPermissions[?FromPort==\`22\`&&contains(IpRanges[].CidrIp,\`0.0.0.0/0\`)]}" \
  --output table
# Rezultat mora biti prazan za svaki SG
```

Verifikuj SSM agent na instanci:

```bash
aws ssm describe-instance-information \
  --query "InstanceInformationList[*].{ID:InstanceId,Status:PingStatus}"
# Status mora biti Online
```

Otvori SSM sesiju (bez SSH ključa, bez porta 22):

```bash
aws ssm start-session --target <instance-id>
# Sesija se otvara direktno u terminal
```

Verifikuj da je sesija zabeležena u CloudWatch:

```bash
# Posle zatvaranja sesije:
aws logs get-log-events \
  --log-group-name /ssm/sessions \
  --log-stream-name <session-id> \
  --limit 20
```

Proveri da li bastion ima ograničen pristup (ako se koristi bastion model):

```bash
aws ec2 describe-instances \
  --filters "Name=tag:Role,Values=bastion" \
  --query "Reservations[].Instances[].{ID:InstanceId,PublicIP:PublicIpAddress,SG:SecurityGroups}"
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- nema SG pravila 0.0.0.0/0 na portu 22
- SSM sesija radi bez SSH ključa
- sesija je zabeležena u audit logu
- bastion je jedina javna ulazna tačka

Evo outputa:
[ovde lepiš: aws ec2 describe-security-groups output, aws ssm start-session potvrdna poruka, CloudWatch log events isečak]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `aws ec2 describe-security-groups` filtrirano na port 22, CIDR 0.0.0.0/0 | Nula rezultata — nijedan SG nema otvoreni SSH prema internetu |
| 2 | `aws ssm start-session --target <instance-id>` | Terminal sesija se otvara za ~5 sekundi bez traženja SSH ključa |
| 3 | Unutar SSM sesije: `whoami && hostname` | Prikazuje korisnika i hostname produkcijske instance |
| 4 | Zatvori sesiju; `aws logs get-log-events --log-group-name /ssm/sessions` | Session ID iz koraka 2 je vidljiv u logu sa timestamp-om i trajanjem |
| 5 | Pokušaj direktnog SSH: `ssh ec2-user@<public-ip>` | Konekcija odbijena ili timeout — port 22 nije dostupan |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — SSH i produkcija sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
