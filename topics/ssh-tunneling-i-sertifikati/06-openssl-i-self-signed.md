# OpenSSL — Alati i self-signed sertifikati

## Šta je OpenSSL?

OpenSSL je open-source biblioteka i skup CLI alata za rad sa kriptografijom — generisanje ključeva, kreiranje sertifikata, konverziju formata, testiranje TLS konekcija.

```bash
# Provjera verzije
openssl version -a
```

---

## Generisanje privatnog ključa

```bash
# RSA 4096-bit ključ
openssl genrsa -out privatni.key 4096

# RSA ključ sa lozinkom (AES-256 šifrovan)
openssl genrsa -aes256 -out privatni_zasticen.key 4096

# EC (Elliptic Curve) ključ — moderniji, manji, brži
openssl ecparam -name prime256v1 -genkey -noout -out ec_privatni.key
# ili
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out ec_privatni.key

# Prikaži sadržaj ključa
openssl rsa -in privatni.key -text -noout
```

---

## CSR — Certificate Signing Request

CSR je zahtev za potpisivanje sertifikata — šalješ CA-u koji vraća potpisani sertifikat.

```bash
# Generiši CSR iz postojećeg ključa
openssl req -new \
    -key privatni.key \
    -out zahtev.csr \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Firma doo/OU=IT/CN=example.com"

# Generiši ključ i CSR odjednom
openssl req -new -newkey rsa:4096 -nodes \
    -keyout privatni.key \
    -out zahtev.csr \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Firma doo/CN=example.com"

# Prikaži sadržaj CSR-a
openssl req -in zahtev.csr -text -noout -verify
```

### CSR sa SAN (Subject Alternative Names)

Moderni sertifikati moraju imati SAN — bez toga browser prikazuje upozorenje.

```bash
# Kreiraj konfiguracioni fajl
cat > san.cnf << 'EOF'
[req]
default_bits       = 2048
prompt             = no
default_md         = sha256
req_extensions     = req_ext
distinguished_name = dn

[dn]
C=RS
ST=Serbia
L=Beograd
O=Firma doo
CN=example.com

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = example.com
DNS.2 = www.example.com
DNS.3 = api.example.com
IP.1  = 192.168.1.100
EOF

openssl req -new -key privatni.key -out zahtev_san.csr -config san.cnf
```

---

## Self-Signed sertifikat

Self-signed sertifikat je potpisan sopstvenim privatnim ključem — nema eksternog CA-a. Browser daje upozorenje, ali je koristan za:
- Lokalni razvoj
- Interni serverski saobraćaj
- Testiranje

```bash
# Generiši ključ + self-signed sertifikat u jednom koraku (365 dana)
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout privatni.key \
    -out sertifikat.crt \
    -days 365 \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Dev/CN=localhost"

# Self-signed sa SAN (Chrome zahteva SAN od 2017!)
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout privatni.key \
    -out sertifikat.crt \
    -days 365 \
    -extensions san \
    -config <(cat /etc/ssl/openssl.cnf \
        <(printf "\n[san]\nsubjectAltName=DNS:localhost,DNS:dev.local,IP:127.0.0.1"))
```

---

## Inspekcija sertifikata

```bash
# Prikaži kompletan sadržaj sertifikata
openssl x509 -in sertifikat.crt -text -noout

# Prikaži samo datum isteka
openssl x509 -in sertifikat.crt -noout -dates

# Prikaži subject (ko je sertifikat)
openssl x509 -in sertifikat.crt -noout -subject

# Prikaži issuer (ko je potpisao)
openssl x509 -in sertifikat.crt -noout -issuer

# Prikaži fingerprint
openssl x509 -in sertifikat.crt -noout -fingerprint -sha256

# Provjeri da li ključ odgovara sertifikatu (hash mora biti isti)
openssl x509 -noout -modulus -in sertifikat.crt | md5sum
openssl rsa  -noout -modulus -in privatni.key | md5sum
```

---

## Testiranje TLS konekcije

```bash
# Provjeri TLS konekciju i prikaži sertifikat
openssl s_client -connect example.com:443 -servername example.com

# Provjeri lanac sertifikata
openssl s_client -connect example.com:443 -showcerts

# Provjeri koji TLS protokoli su podržani
openssl s_client -connect example.com:443 -tls1_2
openssl s_client -connect example.com:443 -tls1_3

# Provjeri specifičnu cipher suite
openssl s_client -connect example.com:443 -cipher ECDHE-RSA-AES256-GCM-SHA384

# Brza provjera datuma isteka sa jednim outputom
echo | openssl s_client -servername example.com \
    -connect example.com:443 2>/dev/null \
    | openssl x509 -noout -dates
```

---

## Konverzija između formata

```bash
# PEM → DER (binarni)
openssl x509 -in sertifikat.pem -out sertifikat.der -outform DER

# DER → PEM
openssl x509 -in sertifikat.der -inform DER -out sertifikat.pem -outform PEM

# PEM → PKCS#12 (za Windows/Java — bundle ključ + sertifikat)
openssl pkcs12 -export \
    -out bundle.pfx \
    -inkey privatni.key \
    -in sertifikat.crt \
    -certfile chain.crt

# PKCS#12 → PEM
openssl pkcs12 -in bundle.pfx -out svi.pem -nodes

# Spoji više PEM fajlova
cat sertifikat.crt intermediate.crt root.crt > fullchain.pem
```

---

## Skripta za provjeru isteka sertifikata

```bash
#!/bin/bash
# check-cert-expiry.sh

DOMAIN="$1"
THRESHOLD=30  # upozori ako ističe za manje od 30 dana

EXPIRY=$(echo | openssl s_client -servername "$DOMAIN" \
    -connect "$DOMAIN:443" 2>/dev/null \
    | openssl x509 -noout -enddate \
    | sed 's/notAfter=//')

EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

echo "Sertifikat za $DOMAIN ističe za $DAYS_LEFT dana ($EXPIRY)"

if [ $DAYS_LEFT -lt $THRESHOLD ]; then
    echo "UPOZORENJE: Sertifikat ističe za manje od $THRESHOLD dana!"
    exit 1
fi
```

```bash
chmod +x check-cert-expiry.sh
./check-cert-expiry.sh example.com
```
