# LDAP — Hijerarhija i pojmovi

## DIT — Directory Information Tree

LDAP organizuje podatke u stablo zvano **DIT**. Svaki čvor je objekat sa atributima.

```
dc=firma,dc=rs                         ← Root (koren stabla)
├── ou=People                          ← Organizational Unit — korisnici
│   ├── uid=darko
│   │   ├── cn: Darko Nikolic
│   │   ├── sn: Nikolic
│   │   ├── mail: darko@firma.rs
│   │   └── userPassword: {SSHA}...
│   └── uid=ana
│       ├── cn: Ana Popovic
│       └── mail: ana@firma.rs
│
├── ou=Groups                          ← Organizational Unit — grupe
│   ├── cn=admins
│   │   ├── member: uid=darko,ou=People,dc=firma,dc=rs
│   │   └── member: uid=ana,ou=People,dc=firma,dc=rs
│   └── cn=developers
│       └── member: uid=darko,ou=People,dc=firma,dc=rs
│
└── ou=Computers                       ← Organizational Unit — računari
    └── cn=server01
        └── description: Web server
```

---

## Ključni pojmovi

### DN — Distinguished Name

Jedinstveni identifikator svakog objekta — kao apsolutna putanja do fajla.

```
uid=darko,ou=People,dc=firma,dc=rs
```

Čita se **s desna na levo**: `firma.rs` → `People` OU → `darko` objekat

### RDN — Relative Distinguished Name

Samo lokalni deo DN-a unutar roditeljskog objekta:
```
uid=darko
```

### Base DN

Polazna tačka za pretragu — određuje od kog čvora stabla krenuti.
```
dc=firma,dc=rs          ← pretražuj celo stablo
ou=People,dc=firma,dc=rs ← pretražuj samo korisnike
```

---

## Atributi

Svaki objekat ima atribute — parovi ključ:vrednost. Mogu imati više vrednosti.

| Atribut | Opis | Primer |
|---------|------|--------|
| `uid` | Korisničko ime | `darko` |
| `cn` | Common Name (puno ime) | `Darko Nikolic` |
| `sn` | Surname (prezime) | `Nikolic` |
| `givenName` | Ime | `Darko` |
| `mail` | Email adresa | `darko@firma.rs` |
| `userPassword` | Lozinka (hash) | `{SSHA}abc123...` |
| `memberOf` | Grupe korisnika | `cn=admins,ou=Groups,dc=firma,dc=rs` |
| `telephoneNumber` | Telefon | `+381601234567` |
| `ou` | Organizational Unit | `People` |
| `dc` | Domain Component | `firma` |
| `uidNumber` | POSIX UID broj | `1001` |
| `gidNumber` | POSIX GID broj | `1001` |
| `homeDirectory` | Home direktorijum | `/home/darko` |
| `loginShell` | Shell | `/bin/bash` |

---

## ObjectClass

Definiše koji atributi su **obavezni** i koji su **opcioni** za objekat. Svaki objekat mora imati bar jednu objectClass.

### Česte objectClass vrednosti

```
top                  ← apstraktna klasa, roditelj svih
├── organization     ← organizacija (obavezno: o)
├── organizationalUnit ← OU (obavezno: ou)
├── person           ← osoba (obavezno: cn, sn)
│   └── inetOrgPerson ← internet osoba (opciono: uid, mail, telephoneNumber...)
│       └── posixAccount ← Linux nalog (obavezno: uid, uidNumber, gidNumber, homeDirectory)
│           └── shadowAccount ← password policy za Linux
├── groupOfNames     ← grupa sa listom članova (obavezno: cn, member)
└── posixGroup       ← Linux grupa (obavezno: cn, gidNumber)
```

### Primer: korisnik sa više objectClass vrednosti

```ldif
dn: uid=darko,ou=People,dc=firma,dc=rs
objectClass: inetOrgPerson      ← puno ime, email, telefon...
objectClass: posixAccount       ← Linux login (uid, shell, home)
objectClass: shadowAccount      ← password expiry politika
uid: darko
cn: Darko Nikolic
sn: Nikolic
mail: darko@firma.rs
uidNumber: 1001
gidNumber: 1001
homeDirectory: /home/darko
loginShell: /bin/bash
```

---

## Scope pretrage

Scope određuje koliko duboko u stablu se pretražuje:

| Scope | Opis | Primer |
|-------|------|--------|
| `base` | Samo navedeni objekat | Čitanje atributa konkretnog DN-a |
| `one` | Direktni potomci base DN-a | Svi objekti u OU, bez sub-OU |
| `sub` | Celo podstablo od base DN-a | Najčešće korišćeno — traži sve |

```bash
# base — samo sam objekat
ldapsearch -b "uid=darko,ou=People,dc=firma,dc=rs" -s base "(objectClass=*)"

# one — direktni potomci
ldapsearch -b "ou=People,dc=firma,dc=rs" -s one "(objectClass=*)"

# sub — celo podstablo (default)
ldapsearch -b "dc=firma,dc=rs" -s sub "(objectClass=inetOrgPerson)"
```
