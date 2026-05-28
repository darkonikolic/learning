# LDAP — Pretrage i ldapsearch

## Sintaksa ldapsearch

```bash
ldapsearch [opcije] [filter] [atributi]

Opcije:
  -x          Simple autentifikacija (ne SASL)
  -H url      LDAP URL (ldap://host ili ldaps://host)
  -b base     Base DN — odakle početi pretragu
  -D dn       Bind DN (ko se loguje)
  -W          Pitaj za lozinku interaktivno
  -w lozinka  Lozinka u komandi (za skripte)
  -s scope    Scope: base, one, sub (default: sub)
  -L          LDIF format izlaza
  -LL         Ukloni komentare iz LDIF
  -LLL        Minimalni LDIF (bez verzije)
```

---

## Osnovna pretraga

```bash
# Svi korisnici
ldapsearch -x -H ldap://localhost \
    -b "ou=People,dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(objectClass=inetOrgPerson)"

# Konkretan korisnik po uid-u
ldapsearch -x -H ldap://localhost \
    -b "dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(uid=darko)"

# Prikaži samo određene atribute (cn i mail)
ldapsearch -x -H ldap://localhost \
    -b "dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(uid=darko)" cn mail

# Prikaži samo DN-ove (bez atributa)
ldapsearch -x -H ldap://localhost \
    -b "dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(objectClass=inetOrgPerson)" dn
```

---

## LDAP Filter sintaksa

### Osnovni operatori

```
(atribut=vrednost)       tačno poklapanje
(atribut=vred*)          počinje sa "vred"
(atribut=*vred)          završava sa "vred"
(atribut=*vred*)         sadrži "vred"
(atribut=*)              atribut postoji (bilo koja vrednost)
(!(atribut=vrednost))    negacija
```

### Logički operatori

```
(&(filter1)(filter2)(filter3))   AND — svi uslovi moraju biti tačni
(|(filter1)(filter2)(filter3))   OR — bar jedan uslov mora biti tačan
(!(filter))                      NOT — negacija
```

### Primeri filtera

```bash
# AND — korisnik koji ima i email i telefon
ldapsearch ... "(&(objectClass=inetOrgPerson)(mail=*)(telephoneNumber=*))"

# OR — korisnik sa jednim od dva emaila
ldapsearch ... "(|(mail=darko@firma.rs)(mail=ana@firma.rs))"

# NOT — svi korisnici osim admina
ldapsearch ... "(&(objectClass=inetOrgPerson)(!(uid=admin)))"

# Složeni filter — član grupe sa email-om
ldapsearch ... "(&(objectClass=inetOrgPerson)(memberOf=cn=admins,ou=Groups,dc=firma,dc=rs)(mail=*))"

# Svi korisnici sa prezimenom koje počinje na "N"
ldapsearch ... "(sn=N*)"
```

---

## Česte pretrage

```bash
# Svi korisnici sa email-om
ldapsearch -x -LLL -H ldap://localhost \
    -b "ou=People,dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(&(objectClass=inetOrgPerson)(mail=*))" \
    uid cn mail

# Svi članovi grupe "admins"
ldapsearch -x -LLL -H ldap://localhost \
    -b "cn=admins,ou=Groups,dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(objectClass=groupOfNames)" \
    member

# Sve grupe korisnika darko
ldapsearch -x -LLL -H ldap://localhost \
    -b "ou=Groups,dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(&(objectClass=groupOfNames)(member=uid=darko,ou=People,dc=firma,dc=rs))" \
    cn

# Verifikacija lozinke (bind kao taj korisnik)
ldapsearch -x -H ldap://localhost \
    -b "ou=People,dc=firma,dc=rs" \
    -D "uid=darko,ou=People,dc=firma,dc=rs" \
    -W \
    "(uid=darko)" cn
# Ako vrati rezultat → lozinka je ispravna
# Ako vrati "Invalid credentials" → lozinka je pogrešna
```

---

## Sortiranje i ograničavanje rezultata

```bash
# Ograniči na prvih 10 rezultata
ldapsearch -x -H ldap://localhost \
    -b "dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    -z 10 \           # sizelimit: max 10 rezultata
    "(objectClass=inetOrgPerson)"

# Traži samo na jednom nivou (direktni potomci OU)
ldapsearch -x -H ldap://localhost \
    -b "ou=People,dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    -s one \          # scope: one level
    "(objectClass=inetOrgPerson)" uid cn
```

---

## Anonimni pristup (ako je dozvoljeno)

```bash
# Bez bind DN i lozinke — anonimni bind
ldapsearch -x -H ldap://localhost \
    -b "dc=firma,dc=rs" \
    "(objectClass=inetOrgPerson)" cn mail
```

---

## Pretraga Active Directory servera

AD koristi drugačije atribute od standardnog OpenLDAP-a.

```bash
# AD — drugačiji format DN-a za bind
ldapsearch -x -H ldap://ad.firma.rs \
    -D "darko@firma.rs" \    # ili: "FIRMA\darko"
    -W \
    -b "dc=firma,dc=rs" \
    "(&(objectClass=user)(sAMAccountName=darko))" \
    displayName mail memberOf sAMAccountName

# AD specifični atributi
# sAMAccountName  → korisničko ime (Windows)
# userPrincipalName → darko@firma.rs
# displayName     → puno ime
# memberOf        → grupe (DN format)
# distinguishedName → puni DN
# pwdLastSet      → kada je lozinka zadata (Windows timestamp)
# accountExpires  → kada nalog ističe
```

---

## Bash skripta — provjera da li korisnik postoji

```bash
#!/bin/bash
check_user() {
    local username="$1"
    local result

    result=$(ldapsearch -x -H ldap://localhost \
        -b "ou=People,dc=firma,dc=rs" \
        -D "cn=admin,dc=firma,dc=rs" \
        -w "$LDAP_ADMIN_PW" \
        -LLL \
        "(uid=${username})" dn 2>/dev/null)

    if [ -n "$result" ]; then
        echo "Korisnik $username postoji"
        return 0
    else
        echo "Korisnik $username NE postoji"
        return 1
    fi
}

check_user "darko"
check_user "nepostojeci"
```
