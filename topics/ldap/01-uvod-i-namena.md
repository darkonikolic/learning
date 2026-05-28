# LDAP — Uvod i namena

## Šta je LDAP?

**LDAP** (Lightweight Directory Access Protocol) je protokol za pristup **direktorijumskim servisima** — bazama podataka optimizovanim za čitanje, koje čuvaju informacije o korisnicima, grupama, računarima i resursima u organizaciji.

Zamislite LDAP direktorijum kao **telefonski imenik za IT sisteme** — brzo pretraživanje, retko menjanje.

## Direktorijum vs Relaciona baza

| | Relaciona baza (SQL) | LDAP direktorijum |
|-|---------------------|-------------------|
| Optimizovan za | Čitanje i pisanje | Uglavnom čitanje |
| Struktura | Tabele (redovi/kolone) | Stablo (hijerarhija) |
| Protokol | SQL | LDAP (port 389/636) |
| Transakcije | Da | Ne |
| Skalabilnost čitanja | Dobra | Odlična |
| Upotreba | Poslovni podaci | Identiteti, autentifikacija |
| Primeri | PostgreSQL, MySQL | OpenLDAP, Active Directory |

## Kako se LDAP koristi u organizaciji?

```
Korisnik se loguje na bilo koji sistem:

  ┌──────────────────────────────────────────────────┐
  │  Linux server / VPN / WiFi / Web app / Email...  │
  └──────────────────┬───────────────────────────────┘
                     │ "Da li je darko/Lozinka123 ispravno?"
                     ▼
          ┌─────────────────────┐
          │    LDAP Server      │
          │  (OpenLDAP / AD)    │
          │                     │
          │  darko:             │
          │    lozinka: ✓       │
          │    grupe: [admins]  │
          │    email: d@f.rs    │
          └─────────────────────┘
                     │ "Da, i on je u grupi admins"
                     ▼
          ┌─────────────────────┐
          │   Pristup odobren   │
          └─────────────────────┘
```

**Jedan nalog — svi sistemi.** Ovo je suština centralizovane autentifikacije.

## Tipični slučajevi upotrebe

| Slučaj | Objašnjenje |
|--------|-------------|
| **Single Sign-On (SSO)** | Jedno korisničko ime/lozinka za sve servise |
| **Linux PAM autentifikacija** | Login na Linux servere |
| **VPN autentifikacija** | OpenVPN, FortiGate, Cisco ASA |
| **WiFi (802.1X / RADIUS)** | Autentifikacija za bežičnu mrežu |
| **Email** | Postfix, Dovecot — provera korisnika i lozinke |
| **Web aplikacije** | Jenkins, Gitlab, Grafana, Jira, Confluence |
| **Adresari** | Outlook Global Address List |

## OpenLDAP vs Active Directory

Active Directory (Microsoft) je implementacija LDAP protokola sa dodatnim funkcijama.

| Osobina | OpenLDAP | Active Directory |
|---------|----------|-----------------|
| Cena | Besplatno | Windows Server licenca |
| OS | Linux/Unix | Windows Server |
| LDAP kompatibilan | Da (standard) | Da (prošireni LDAP) |
| Kerberos | Opciono | Ugrađeno |
| Group Policy | Ne | Da |
| DNS integracija | Ručno | Automatski |
| GUI alati | phpLDAPadmin, Ldap Account Manager | Active Directory Users and Computers |
| Tipično okruženje | Startup, Linux/open-source shop | Enterprise, Microsoft okruženje |

## Portovi

| Port | Protokol | Opis |
|------|----------|------|
| 389 | LDAP | Nešifrovan — NE koristiti za lozinke! |
| 636 | LDAPS | SSL/TLS šifrovano — preporučeno |
| 389 | STARTTLS | Počinje nešifrovano, ugrađuje TLS |
