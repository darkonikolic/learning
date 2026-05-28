# LDAP — LDIF format

## Šta je LDIF?

**LDIF** (LDAP Data Interchange Format) je tekstualni format za opisivanje LDAP objekata i promena. Koristi se za:
- Kreiranje novih objekata (`add`)
- Izmenu postojećih (`modify`)
- Brisanje objekata (`delete`)
- Uvoz i izvoz podataka

## Osnovna sintaksa

```
dn: <distinguished name>
objectClass: <vrednost>
atribut: vrednost
atribut: vrednost

(prazan red = separator između zapisa)
```

---

## Dodavanje objekta (add)

```ldif
# Komentar počinje sa #

dn: ou=People,dc=firma,dc=rs
changetype: add
objectClass: organizationalUnit
ou: People
description: Zaposleni u firmi

dn: ou=Groups,dc=firma,dc=rs
changetype: add
objectClass: organizationalUnit
ou: Groups
```

Kada se koristi `ldapadd` komanda, `changetype: add` nije obavezan — `ldapadd` uvek dodaje.

---

## Dodavanje korisnika

```ldif
dn: uid=darko,ou=People,dc=firma,dc=rs
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: darko
cn: Darko Nikolic
sn: Nikolic
givenName: Darko
mail: darko@firma.rs
telephoneNumber: +381601234567
uidNumber: 1001
gidNumber: 1001
homeDirectory: /home/darko
loginShell: /bin/bash
userPassword: {SSHA}abc123hashovanalozinka==
```

---

## Dodavanje grupe

```ldif
dn: cn=admins,ou=Groups,dc=firma,dc=rs
objectClass: groupOfNames
cn: admins
description: Administratori sistema
member: uid=darko,ou=People,dc=firma,dc=rs
member: uid=ana,ou=People,dc=firma,dc=rs
```

```ldif
# POSIX grupa za Linux
dn: cn=devops,ou=Groups,dc=firma,dc=rs
objectClass: posixGroup
cn: devops
gidNumber: 2001
memberUid: darko
memberUid: ana
```

---

## Izmena objekta (modify)

`changetype: modify` sa jednom ili više operacija: `replace`, `add`, `delete`.

```ldif
dn: uid=darko,ou=People,dc=firma,dc=rs
changetype: modify
replace: telephoneNumber
telephoneNumber: +381609876543
-
add: description
description: Senior Developer
-
delete: facsimileTelephoneNumber
```

Separator između operacija je `-` (crtica na zasebnoj liniji).

---

## Dodavanje člana u grupu (modify)

```ldif
dn: cn=admins,ou=Groups,dc=firma,dc=rs
changetype: modify
add: member
member: uid=ana,ou=People,dc=firma,dc=rs
```

---

## Uklanjanje člana iz grupe

```ldif
dn: cn=admins,ou=Groups,dc=firma,dc=rs
changetype: modify
delete: member
member: uid=ana,ou=People,dc=firma,dc=rs
```

---

## Brisanje objekta (delete)

```ldif
dn: uid=starikorisnik,ou=People,dc=firma,dc=rs
changetype: delete
```

---

## Promena DN-a (modrdn)

```ldif
# Premesti korisnika u drugu OU
dn: uid=darko,ou=People,dc=firma,dc=rs
changetype: modrdn
newrdn: uid=darko
deleteoldrdn: 1
newsuperior: ou=Archived,dc=firma,dc=rs
```

---

## Specijalni karakteri i kodiranje

Vrednosti koje sadrže specijalne karaktere moraju biti Base64 kodirane (prefiks `::`):

```ldif
# Vrednost sa srpskim slovima — Base64 kodirana
dn: uid=darko,ou=People,dc=firma,dc=rs
cn:: RGFya28gTmlrb2xpxIc=
# (Base64 od "Darko Nikolić")
```

```bash
# Kodiranje/dekodiranje
echo -n "Darko Nikolić" | base64
echo "RGFya28gTmlrb2xpxIc=" | base64 -d
```

---

## Izvoz (backup) celokupne baze

```bash
# Izvoz dok slapd radi
ldapsearch -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    -b "dc=firma,dc=rs" \
    "(objectClass=*)" \
    > /backup/ldap-$(date +%Y%m%d).ldif

# Izvoz direktno iz baze (slapd mora biti zaustavljen ili koristiti online backup)
sudo slapcat -v -l /backup/ldap-full-$(date +%Y%m%d).ldif
```

---

## Uvoz iz LDIF fajla

```bash
# Uvoz dok slapd radi
ldapadd -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    -f /backup/ldap-20240101.ldif

# Uvoz izmena
ldapmodify -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    -f /tmp/izmene.ldif

# Direktan uvoz u bazu (slapd mora biti zaustavljen)
sudo slapadd -v -l /backup/ldap-full-20240101.ldif
```
