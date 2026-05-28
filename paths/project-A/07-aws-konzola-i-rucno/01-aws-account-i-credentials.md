# 01 — AWS Account i Credentials

## Cilj

Razumjeti AWS account strukturu i postaviti credentials ispravno — bez root accounta, bez nekontrolisanih access keyeva, sa MFA na svemu što je važno.

---

## Root Account vs IAM Users

### Root Account

Root je email/lozinka kojom si kreirao AWS account. Ima **apsolutno sva prava** — ne može biti ograničen policy-jem, jedini koji može zatvoriti account, jedini koji može promijeniti billing postavke.

**Nikad ne korisiti root za svakodnevni rad.** Razlog nije samo "best practice" — razlog je konkretan: ako ti kompromituju root credentials, napadač može:
- Obrisati sve resurse
- Iskopirati sve podatke
- Promijeniti email i lozinku i zaključati te iz accounta
- Ukloniti MFA sa root accounta sam sebi

Root treba iskoristiti za:
1. Kreiranje prvog IAM admin korisnika
2. Billing/account management (ako to treba)
3. Oporavak ako se zaključaš

### Kako zaštititi root

Odmah nakon kreiranja accounta:
- **Console → top-right click na account name → Security credentials**
- Enable MFA: preporuka je hardware key (YubiKey) ili authenticator app
- Nemoj kreirati root access keyeve — ako postoje, odmah ih obriši
- Postavi billing alarm: **CloudWatch → Alarms → Create → Billing → Threshold 10 USD**

---

## Kreiranje IAM Admin Korisnika

**Console → Services → IAM → Users → Create user**

Korak po korak:
1. **User name**: `darko-admin` (ili tvoje ime, izbjegavaj generičko "admin")
2. **Provide user access to the AWS Management Console**: ✓ (kvačica)
3. **I want to create an IAM user**: izaberi (ne Identity Center za sada)
4. **Console password**: Custom password, snažna lozinka
5. **Users must create a new password**: opciono, za tvoj lični korisnik isključi
6. Next → **Attach policies directly**
7. Traži i dodaj: `AdministratorAccess`
8. Create user

**AdministratorAccess je preširok za produkciju** — daje sve. Za inicijalni setup je OK, ali plan je da ga kasnije zamijeniš custom policy-jem koji daje samo ono što treba.

### MFA za IAM admin korisnika

**IAM → Users → darko-admin → Security credentials → Assign MFA device**

- Device name: `darko-phone`
- MFA device type: Authenticator app
- Scaniraj QR u Google Authenticator / Authy
- Unesi 2 uzastopna koda da verifikuješ
- Assign MFA

Bez MFA IAM admin korisnik je skoro jednako rizičan kao root.

---

## Access Keys — Kada Da, Kada Ne

Access key = `AKIAIOSFODNN7EXAMPLE` + secret. Traje zauvijek (dok ga ne obrišeš ili deaktiviješ). **Ako iscuri, napadač ima pristup bez ikakvog MFA-a.**

### Kada kreirati access key

**Jedino opravdanje**: lokalni razvoj, AWS CLI na tvojoj mašini.

**Console → IAM → Users → darko-admin → Security credentials → Create access key**

- Use case: CLI
- Kvačica na "I understand the above recommendation"
- **Odmah spremi** Access key ID i Secret access key — secret se vidi samo jednom

### Kada NE kreirati access key

| Scenario | Rješenje |
|----------|----------|
| EC2 instance treba AWS API | IAM Role attachana na instancu (instance metadata service) |
| EKS Pod treba AWS API | IRSA — IAM Role za Service Account |
| GitLab CI treba AWS API | OIDC federation — privremeni credentials per pipeline |
| Lambda function | Execution role |

**Na EKS nodovima nikad ne stavljati access keyeve.** Ako node bude kompromitovan, napadač ih može pročitati. IRSA daje privremene credentials koji expiraju.

---

## AWS CLI kroz Docker

Ne instalirati AWS CLI lokalno — koristiti Docker image. Prednost: izolacija verzije, nema instalacije, isti image u CI-u i lokalno.

```bash
# Jednokratna konfiguracija — kreira ~/.aws/credentials i ~/.aws/config
docker run --rm -it \
  -v ~/.aws:/root/.aws \
  amazon/aws-cli:latest configure
```

Prompts:
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: eu-west-1
Default output format [None]: json
```

Ovo kreira dva fajla:

`~/.aws/credentials`:
```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

`~/.aws/config`:
```ini
[default]
region = eu-west-1
output = json
```

---

## Named Profiles za Multiple Environments

Nikad ne miješati dev i prod credentials u istom profilu — greška u pogrešnom terminalu može destroy-ati produkciju.

```bash
# Konfiguracija dev profila
docker run --rm -it \
  -v ~/.aws:/root/.aws \
  amazon/aws-cli:latest configure --profile dev

# Konfiguracija prod profila (drugačiji access key!)
docker run --rm -it \
  -v ~/.aws:/root/.aws \
  amazon/aws-cli:latest configure --profile prod
```

`~/.aws/credentials` nakon toga:
```ini
[default]
aws_access_key_id = AKIA...DEV
aws_secret_access_key = ...

[dev]
aws_access_key_id = AKIA...DEV
aws_secret_access_key = ...

[prod]
aws_access_key_id = AKIA...PROD
aws_secret_access_key = ...
```

Korištenje u CLI:
```bash
docker run --rm -it \
  -v ~/.aws:/root/.aws \
  amazon/aws-cli:latest --profile dev s3 ls

docker run --rm -it \
  -v ~/.aws:/root/.aws \
  amazon/aws-cli:latest --profile prod s3 ls
```

Ili postavi env var da ne moraš kucati `--profile`:
```bash
export AWS_PROFILE=dev
```

---

## Verifikacija

Provjeri da si prijavljen kao IAM korisnik, **ne** kao root:

```bash
docker run --rm \
  -v ~/.aws:/root/.aws \
  amazon/aws-cli:latest sts get-caller-identity
```

Očekivani output:
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/darko-admin"
}
```

Ako `Arn` sadrži `:root` — odmah se odjavi, prijavi kao IAM korisnik.

Ako dobiješ `An error occurred (InvalidClientTokenId)` — access key je pogrešan ili obrisan.

---

## Napomena za Sljedeći Modul

Sve što ćeš raditi u konzoli od ovog trenutka raditi s `darko-admin` IAM korisnikom. Root neće biti potreban sve do kraja projekta.

GitLab CI credentials (OIDC) se podešavaju u modulu 08 — pipeline konfiguracija. Za sada, access key za lokalni CLI je dovoljan.
