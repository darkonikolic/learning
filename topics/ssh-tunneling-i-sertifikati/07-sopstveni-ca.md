# Sopstveni CA — Interna sertifikaciona ustanova

## Zašto sopstveni CA?

| Scenario | Rešenje |
|----------|---------|
| Javni web sajt | Let's Encrypt (besplatan, automatski) |
| Interni servisi, dev okruženje | **Sopstveni CA** |
| Mašina-mašina komunikacija | **Sopstveni CA** |
| LDAPS, interni Nginx, Kubernetes | **Sopstveni CA** |

Sopstveni CA omogućava da **svi interni serveri i klijenti** veruju tvojim sertifikatima — bez browser upozorenja, bez troška.

---

## Kreiranje Root CA

```bash
mkdir -p ~/myCA/{certs,private,newcerts}
cd ~/myCA
touch index.txt
echo 1000 > serial

# Generiši privatni ključ Root CA (čuvaj ga BEZBEDNO, sa lozinkom!)
openssl genrsa -aes256 -out private/ca.key 4096
chmod 400 private/ca.key

# Kreiraj Root CA sertifikat (10 godina)
openssl req -new -x509 -days 3650 \
    -key private/ca.key \
    -out certs/ca.crt \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Firma doo CA/CN=Firma Root CA"

# Provjeri
openssl x509 -in certs/ca.crt -text -noout | grep -E "Subject|Issuer|Not"
```

---

## Potpisivanje sertifikata za server

```bash
# 1. Server generiše privatni ključ i CSR
openssl req -new -newkey rsa:2048 -nodes \
    -keyout server.key \
    -out server.csr \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Firma doo/CN=api.firma.rs"

# 2. Kreiraj ekstenzije fajl sa SAN
cat > server-ext.cnf << 'EOF'
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = api.firma.rs
DNS.2 = www.api.firma.rs
IP.1  = 10.0.0.50
EOF

# 3. CA potpisuje sertifikat (2 godine)
openssl x509 -req -days 730 \
    -in server.csr \
    -CA certs/ca.crt \
    -CAkey private/ca.key \
    -CAcreateserial \
    -out server.crt \
    -extfile server-ext.cnf

# 4. Provjeri
openssl verify -CAfile certs/ca.crt server.crt
openssl x509 -in server.crt -text -noout | grep -E "Subject|DNS|IP"
```

---

## Distribucija CA sertifikata klijentima

Da bi svi klijenti verovali tvojim sertifikatima, moraju instalirati tvoj Root CA sertifikat.

```bash
# Ubuntu/Debian
sudo cp ~/myCA/certs/ca.crt /usr/local/share/ca-certificates/firma-root-ca.crt
sudo update-ca-certificates
# Provjeri: ls /etc/ssl/certs/ | grep firma

# CentOS/RHEL
sudo cp ~/myCA/certs/ca.crt /etc/pki/ca-trust/source/anchors/firma-root-ca.crt
sudo update-ca-trust extract
# Provjeri: trust list | grep Firma

# Provjeri da li curl veruje sertifikatu
curl https://api.firma.rs   # ne sme dati SSL grešku
```

### Windows (Group Policy)

1. `certmgr.msc` → Trusted Root Certification Authorities → Import
2. Ili PowerShell:
```powershell
Import-Certificate -FilePath "firma-root-ca.crt" `
    -CertStoreLocation "Cert:\LocalMachine\Root"
```

---

## Intermediate CA (preporučena produkciona praksa)

Root CA privatni ključ se čuva offline. Za svakodnevno potpisivanje koristi Intermediate CA.

```bash
# Generiši Intermediate CA ključ i CSR
openssl genrsa -aes256 -out private/intermediate.key 4096
openssl req -new \
    -key private/intermediate.key \
    -out intermediate.csr \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Firma doo/CN=Firma Intermediate CA"

# Root CA potpisuje Intermediate CA sertifikat
cat > intermediate-ext.cnf << 'EOF'
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,digitalSignature,cRLSign,keyCertSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
EOF

openssl x509 -req -days 1825 \
    -in intermediate.csr \
    -CA certs/ca.crt \
    -CAkey private/ca.key \
    -CAcreateserial \
    -out certs/intermediate.crt \
    -extfile intermediate-ext.cnf

# Fullchain (šalje se klijentima)
cat certs/intermediate.crt certs/ca.crt > certs/fullchain-ca.crt
```

---

## Bash skripta za brzo kreiranje sertifikata

```bash
#!/bin/bash
# new-cert.sh <domen> [IP]

DOMAIN="$1"
IP="${2:-}"
CA_DIR="$HOME/myCA"
DAYS=730

[ -z "$DOMAIN" ] && { echo "Upotreba: $0 <domen> [IP]"; exit 1; }

# Ključ i CSR
openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$DOMAIN.key" \
    -out "$DOMAIN.csr" \
    -subj "/C=RS/O=Firma doo/CN=$DOMAIN"

# SAN ekstenzije
EXT="subjectAltName=DNS:$DOMAIN"
[ -n "$IP" ] && EXT="$EXT,IP:$IP"

# Potpiši
openssl x509 -req -days $DAYS \
    -in "$DOMAIN.csr" \
    -CA "$CA_DIR/certs/ca.crt" \
    -CAkey "$CA_DIR/private/ca.key" \
    -CAcreateserial \
    -out "$DOMAIN.crt" \
    -extfile <(echo "$EXT")

openssl verify -CAfile "$CA_DIR/certs/ca.crt" "$DOMAIN.crt"
echo "Kreiran sertifikat: $DOMAIN.crt i $DOMAIN.key"
```

```bash
chmod +x new-cert.sh
./new-cert.sh api.firma.rs 10.0.0.50
./new-cert.sh db.firma.rs
```

---

## Primena u Nginx-u

```nginx
server {
    listen 443 ssl http2;
    server_name api.firma.rs;

    ssl_certificate     /etc/nginx/certs/api.firma.rs.crt;
    ssl_certificate_key /etc/nginx/certs/api.firma.rs.key;
    ssl_trusted_certificate /etc/nginx/certs/firma-root-ca.crt;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_session_cache   shared:SSL:10m;
}
```
