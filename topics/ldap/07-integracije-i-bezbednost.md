# LDAP — Integracije i bezbednost

## Linux PAM/NSS — login na Linux sistem

Omogućava login na Linux server koristeći LDAP nalog.

```bash
sudo apt install libnss-ldap libpam-ldap ldap-utils nslcd
# Tokom instalacije: unesi LDAP URL i base DN
```

### /etc/nslcd.conf

```
uid nslcd
gid nslcd
uri ldaps://ldap.firma.rs
base dc=firma,dc=rs
binddn cn=nslcd,dc=firma,dc=rs
bindpw NslcdBindLozinka
tls_cacertfile /etc/ssl/certs/ldap-ca.crt
```

### /etc/nsswitch.conf

```
passwd:     files ldap
group:      files ldap
shadow:     files ldap
```

### /etc/pam.d/common-auth

```
auth    sufficient      pam_ldap.so
auth    required        pam_unix.so nullok_secure try_first_pass
```

```bash
# Testiraj da li sistem vidi LDAP korisnike
getent passwd darko
getent group admins

# Testiraj login (ne loguje se zaista, samo provjera)
su - darko -c "whoami"
```

---

## Nginx + LDAP autentifikacija

```
Klijent → Nginx → [auth_request] → ldap-auth servis → LDAP server
              ↓                           ↓ 200/401
         Backend app                (ako je autorizovan)
```

```nginx
server {
    listen 443 ssl http2;
    server_name intranet.firma.rs;

    location = /auth-ldap {
        internal;
        proxy_pass              http://127.0.0.1:8888;
        proxy_pass_request_body off;
        proxy_set_header        Content-Length "";
        proxy_set_header        X-Original-URI $request_uri;
        proxy_set_header        X-Ldap-URL     "ldaps://ldap.firma.rs";
        proxy_set_header        X-Ldap-Base    "ou=People,dc=firma,dc=rs";
        proxy_set_header        X-Ldap-BindDN  "cn=nginx-bind,dc=firma,dc=rs";
        proxy_set_header        X-Ldap-BindPW  "NginxBindLozinka";
        proxy_set_header        X-Ldap-Group   "cn=intranet-users,ou=Groups,dc=firma,dc=rs";
    }

    location / {
        auth_request  /auth-ldap;
        error_page 401 = @login;
        proxy_pass http://127.0.0.1:3000;
    }

    location @login {
        return 401;
        add_header WWW-Authenticate 'Basic realm="Firma Intranet"';
    }
}
```

---

## ACL — Access Control List

Definiše ko sme šta da radi sa podacima u LDAP-u.

```bash
# Postavi ACL — korisnici mogu menjati sopstvene podatke,
# admin može sve, bind korisnici mogu čitati
sudo ldapmodify -Y EXTERNAL -H ldapi:// << 'EOF'
dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcAccess
olcAccess: {0}to attrs=userPassword
    by self write
    by dn.exact="cn=admin,dc=firma,dc=rs" write
    by anonymous auth
    by * none
olcAccess: {1}to attrs=shadowLastChange
    by self write
    by * read
olcAccess: {2}to *
    by dn.exact="cn=admin,dc=firma,dc=rs" write
    by dn.exact="cn=app-reader,dc=firma,dc=rs" read
    by self read
    by * none
EOF
```

### Princip minimalnih privilegija za bind korisnike

```ldif
# Read-only bind korisnik za aplikacije
dn: cn=app-reader,dc=firma,dc=rs
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: app-reader
description: Read-only bind za aplikacije
userPassword: {SSHA}ReadOnlyHash...
```

---

## Integracije sa popularnim servisima

### Gitea / Gitab

```
Admin → Settings → Authentication Sources → Add LDAP
Host: ldap.firma.rs
Port: 636
Security: LDAPS
Bind DN: cn=gitea-bind,dc=firma,dc=rs
User Search Base: ou=People,dc=firma,dc=rs
User Filter: (&(objectClass=inetOrgPerson)(uid=%s))
Username attr: uid
Email attr: mail
```

### Jenkins

```
Manage Jenkins → Configure Global Security → LDAP
Server: ldaps://ldap.firma.rs
Root DN: dc=firma,dc=rs
User search base: ou=People
User search filter: uid={0}
Group search base: ou=Groups
Group membership: member={0}   (memberOf attribute)
Manager DN: cn=jenkins-bind,dc=firma,dc=rs
```

### Grafana

```ini
# /etc/grafana/grafana.ini
[auth.ldap]
enabled = true
config_file = /etc/grafana/ldap.toml
```

```toml
# /etc/grafana/ldap.toml
[[servers]]
host = "ldap.firma.rs"
port = 636
use_ssl = true
start_tls = false
ssl_skip_verify = false
bind_dn = "cn=grafana-bind,dc=firma,dc=rs"
bind_password = "GrafanaBindLozinka"
search_filter = "(uid=%s)"
search_base_dns = ["ou=People,dc=firma,dc=rs"]

[servers.attributes]
name = "givenName"
surname = "sn"
username = "uid"
member_of = "memberOf"
email = "mail"

[[servers.group_mappings]]
group_dn = "cn=admins,ou=Groups,dc=firma,dc=rs"
org_role = "Admin"

[[servers.group_mappings]]
group_dn = "cn=developers,ou=Groups,dc=firma,dc=rs"
org_role = "Viewer"
```

---

## Bezbednosne preporuke

```bash
# 1. UVEK koristiti LDAPS (port 636) ili STARTTLS za lozinke!
# Nikad plain LDAP (port 389) u produkciji

# 2. Proveri da li komuniciraš bezbedno
ldapsearch -x -H ldaps://ldap.firma.rs \
    -b "dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W "(objectClass=*)" dn

# 3. Zasebni bind korisnici za svaku aplikaciju
# Svaka aplikacija ima svog read-only korisnika:
# cn=nginx-bind, cn=jenkins-bind, cn=grafana-bind...

# 4. Nikad ne koristiti admin DN za aplikacije

# 5. Ograniči pristup LDAP porta na firewall-u
# Samo interni serveri smeju da pristupe LDAP-u
```

---

## Česte greške

| Greška | Uzrok | Rešenje |
|--------|-------|---------|
| `Invalid credentials (49)` | Pogrešan DN ili lozinka | Provjeri format DN-a i lozinku |
| `No such object (32)` | Base DN ne postoji | Provjeri da li ou/dc postoji |
| `Insufficient access (50)` | Bind korisnik nema prava | Dodaj ACL pravila |
| `Can't contact LDAP server` | Firewall ili slapd ne radi | `systemctl status slapd`, provjeri port 389/636 |
| `Constraint violation (19)` | Obavezni atribut nedostaje | Provjeri objectClass zahteve |
| `Already exists (68)` | Objekat već postoji | Koristi ldapmodify umesto ldapadd |
| `Operations error (1)` | Interna greška servera | Provjeri syslog/journalctl |

---

## Korisni alati

| Alat | Opis |
|------|------|
| `ldapsearch` | Pretraživanje direktorijuma |
| `ldapadd` | Dodavanje novih objekata |
| `ldapmodify` | Izmena postojećih objekata |
| `ldapdelete` | Brisanje objekata |
| `ldappasswd` | Promena lozinke |
| `slapcat` | Export cele baze u LDIF (offline) |
| `slapadd` | Import LDIF direktno (offline) |
| `slappasswd` | Generisanje hash lozinke |
| **Apache Directory Studio** | GUI alat (Java, cross-platform) |
| **phpLDAPadmin** | Web GUI za LDAP |
| **Ldap Account Manager** | Web GUI za upravljanje nalozima |
