# LDAP — Instalacija OpenLDAP

## Instalacija na Ubuntu/Debian

```bash
sudo apt update
sudo apt install slapd ldap-utils

# Tokom instalacije: slapd pita samo za admin lozinku
# Za kompletnu konfiguraciju pokreni:
sudo dpkg-reconfigure slapd
```

### Odgovori na pitanja dpkg-reconfigure slapd

```
Omit OpenLDAP server configuration? → No
DNS domain name → firma.rs
Organization name → Firma doo
Administrator password → [snažna lozinka]
Confirm password → [ista lozinka]
Database backend → MDB
Remove database when slapd is purged? → No
Move old database? → Yes
```

## Instalacija na CentOS/RHEL

```bash
sudo dnf install openldap-servers openldap-clients

# Postavi admin lozinku
sudo slappasswd -s "AdminLozinka123!" > /tmp/admin_hash.txt
cat /tmp/admin_hash.txt
# Primer: {SSHA}7qP+VZXZ8/h0DL8ue5o/HaWxq4gqYsRs

# Konfiguriši root DN i lozinku
sudo ldapmodify -Y EXTERNAL -H ldapi:// << 'EOF'
dn: olcDatabase={2}hdb,cn=config
changetype: modify
replace: olcSuffix
olcSuffix: dc=firma,dc=rs
-
replace: olcRootDN
olcRootDN: cn=admin,dc=firma,dc=rs
-
replace: olcRootPW
olcRootPW: {SSHA}7qP+VZXZ8/h0DL8ue5o/HaWxq4gqYsRs
EOF

sudo systemctl enable --now slapd
```

## Provjera instalacije

```bash
# Status servisa
sudo systemctl status slapd

# Provjeri sluša li na portu 389
ss -tlnp | grep ':389'

# Test konekcije i listanje root objekta
ldapsearch -x -H ldap://localhost \
    -b "dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W \
    "(objectClass=*)" dn

# Provjeri konfiguraciju slapd-a
sudo ldapsearch -Y EXTERNAL -H ldapi:// -b "cn=config" "(cn=config)" dn
```

## Konfiguracija TLS/LDAPS

```bash
# Generiši self-signed sertifikat (za produkciju koristiti CA ili Let's Encrypt)
sudo mkdir -p /etc/ldap/certs
sudo openssl req -new -x509 -nodes -days 3650 \
    -out /etc/ldap/certs/ldap.crt \
    -keyout /etc/ldap/certs/ldap.key \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Firma/CN=ldap.firma.rs"

sudo chown openldap:openldap /etc/ldap/certs/ldap.*
sudo chmod 640 /etc/ldap/certs/ldap.key
```

```bash
# Primeni TLS konfiguraciju
sudo ldapmodify -Y EXTERNAL -H ldapi:// << 'EOF'
dn: cn=config
changetype: modify
add: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/ldap/certs/ldap.crt
-
add: olcTLSCertificateFile
olcTLSCertificateFile: /etc/ldap/certs/ldap.crt
-
add: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/ldap/certs/ldap.key
EOF
```

```bash
# Omogući LDAPS port 636
sudo nano /etc/default/slapd
# Promeni:
# SLAPD_SERVICES="ldap:/// ldapi:/// ldaps:///"

sudo systemctl restart slapd

# Provjeri LDAPS
ldapsearch -x -H ldaps://localhost \
    -b "dc=firma,dc=rs" \
    -D "cn=admin,dc=firma,dc=rs" \
    -W "(objectClass=*)" dn
```

## Konfiguracija /etc/ldap/ldap.conf (klijent)

```bash
# /etc/ldap/ldap.conf — podrazumevane vrednosti za ldap* komande
BASE    dc=firma,dc=rs
URI     ldaps://ldap.firma.rs
TLS_CACERT  /etc/ldap/certs/ldap.crt

# Nakon ovoga ne treba pisati -H i -b u svakoj komandi:
ldapsearch -x -D "cn=admin,dc=firma,dc=rs" -W "(uid=darko)"
```

## Logovi slapd-a

```bash
# Sistemski log
sudo tail -f /var/log/syslog | grep slapd
# ili
sudo journalctl -u slapd -f

# Povećaj nivo logovanja (za debug)
sudo ldapmodify -Y EXTERNAL -H ldapi:// << 'EOF'
dn: cn=config
changetype: modify
replace: olcLogLevel
olcLogLevel: stats
EOF
# Nivoi: none, stats, filter, config, acl, sync, ...
```

## Firewall podešavanje

```bash
# UFW
sudo ufw allow 389/tcp   # LDAP (samo za internu mrežu!)
sudo ufw allow 636/tcp   # LDAPS

# firewalld
sudo firewall-cmd --permanent --add-service=ldap
sudo firewall-cmd --permanent --add-service=ldaps
sudo firewall-cmd --reload

# Preporučeno: dozvoliti samo sa internih IP-ova
sudo ufw allow from 10.0.0.0/8 to any port 636
sudo ufw deny 636/tcp
```
