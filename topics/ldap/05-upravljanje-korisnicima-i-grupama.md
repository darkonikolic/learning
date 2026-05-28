# LDAP — Upravljanje korisnicima i grupama

## Kreiranje osnovne strukture

```bash
# Kreiraj OU za korisnike i grupe
cat > /tmp/base-structure.ldif << 'EOF'
dn: ou=People,dc=firma,dc=rs
objectClass: organizationalUnit
ou: People
description: Korisnici firme

dn: ou=Groups,dc=firma,dc=rs
objectClass: organizationalUnit
ou: Groups
description: Grupe i uloge
EOF

ldapadd -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W -f /tmp/base-structure.ldif
```

---

## Dodavanje korisnika

```bash
# Generiši lozinku hash
HASH=$(slappasswd -s "MojaLozinka123!")
echo $HASH
# {SSHA}e3Rd7KqGm9WJlFOhPr2vX8yNbT4uZ1sA==

cat > /tmp/novi-korisnik.ldif << EOF
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
userPassword: $HASH
EOF

ldapadd -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W -f /tmp/novi-korisnik.ldif
```

---

## Kreiranje grupe i dodavanje članova

```bash
cat > /tmp/grupe.ldif << 'EOF'
dn: cn=admins,ou=Groups,dc=firma,dc=rs
objectClass: groupOfNames
cn: admins
description: Administratori sistema
member: uid=darko,ou=People,dc=firma,dc=rs

dn: cn=developers,ou=Groups,dc=firma,dc=rs
objectClass: groupOfNames
cn: developers
description: Razvojni tim
member: uid=darko,ou=People,dc=firma,dc=rs
EOF

ldapadd -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W -f /tmp/grupe.ldif
```

---

## Izmena atributa korisnika

```bash
# Promeni telefon i dodaj opis
ldapmodify -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W << 'EOF'
dn: uid=darko,ou=People,dc=firma,dc=rs
changetype: modify
replace: telephoneNumber
telephoneNumber: +381609876543
-
add: description
description: Senior DevOps Engineer
EOF
```

---

## Promena lozinke

```bash
# Admin menja lozinku korisniku
ldappasswd -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    -S "uid=darko,ou=People,dc=firma,dc=rs"
# Pita za novu lozinku dva puta

# Direktno zadaj novu lozinku (za skripte)
ldappasswd -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -w "AdminLozinka" \
    -s "NovLozinka123!" \
    "uid=darko,ou=People,dc=firma,dc=rs"

# Korisnik menja svoju lozinku (self-service)
ldappasswd -x -H ldap://localhost \
    -D "uid=darko,ou=People,dc=firma,dc=rs" \
    -W \
    -S
```

---

## Dodavanje korisnika u grupu

```bash
ldapmodify -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W << 'EOF'
dn: cn=admins,ou=Groups,dc=firma,dc=rs
changetype: modify
add: member
member: uid=ana,ou=People,dc=firma,dc=rs
EOF
```

---

## Uklanjanje korisnika iz grupe

```bash
ldapmodify -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W << 'EOF'
dn: cn=admins,ou=Groups,dc=firma,dc=rs
changetype: modify
delete: member
member: uid=ana,ou=People,dc=firma,dc=rs
EOF
```

---

## Brisanje korisnika

```bash
# Brisanje korisnika
ldapdelete -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "uid=bivsiradnik,ou=People,dc=firma,dc=rs"

# Pre brisanja — ukloni iz svih grupa (ručno ili skripta)
```

---

## Deaktivacija korisnika (bez brisanja)

Umesto brisanja, korisnika se može "zaključati" promenom loginShell-a ili dodavanjem shadow atributa:

```bash
# Promeni shell na /sbin/nologin (ne može se logovati na Linux)
ldapmodify -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W << 'EOF'
dn: uid=darko,ou=People,dc=firma,dc=rs
changetype: modify
replace: loginShell
loginShell: /sbin/nologin
EOF

# Ili premesti u ou=Archived
ldapmodify -x -H ldap://localhost \
    -D "cn=admin,dc=firma,dc=rs" \
    -W << 'EOF'
dn: uid=darko,ou=People,dc=firma,dc=rs
changetype: modrdn
newrdn: uid=darko
deleteoldrdn: 1
newsuperior: ou=Archived,dc=firma,dc=rs
EOF
```

---

## Bash skripta za batch kreiranje korisnika

```bash
#!/bin/bash
# create-ldap-users.sh

LDAP_HOST="ldap://localhost"
BIND_DN="cn=admin,dc=firma,dc=rs"
BIND_PW="AdminLozinka"
BASE_DN="ou=People,dc=firma,dc=rs"
START_UID=2000

# CSV format: username,firstname,lastname,email
while IFS=, read -r username firstname lastname email; do
    HASH=$(slappasswd -s "TempLozinka123!")
    UID_NUM=$((START_UID++))

    ldapadd -x -H "$LDAP_HOST" -D "$BIND_DN" -w "$BIND_PW" << EOF
dn: uid=${username},${BASE_DN}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: ${username}
cn: ${firstname} ${lastname}
sn: ${lastname}
givenName: ${firstname}
mail: ${email}
uidNumber: ${UID_NUM}
gidNumber: 1000
homeDirectory: /home/${username}
loginShell: /bin/bash
userPassword: ${HASH}
EOF

    echo "Kreiran korisnik: ${username}"
done < korisnici.csv
```

```csv
# korisnici.csv
marko,Marko,Jovic,marko@firma.rs
jelena,Jelena,Markovic,jelena@firma.rs
```
