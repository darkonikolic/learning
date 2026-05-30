# 07 — Vežba: gRPC

Podešavaš AI okvir za gRPC servise (proto kontrakt higijena, buf lint/breaking check) i verifikuješ da svaki RPC poziv radi ispravno sa korektnim error kodovima.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Dodajemo buf lint i buf breaking check u CI za zaštitu proto kontrakta od nekompatibilnih promena. Testiramo svaki RPC poziv sa `grpcurl` — uspešan odgovor, not-found, invalid-argument. Verifikujemo da streaming RPC streama ispravno.

**Pretpostavke za potvrdu:**
- gRPC server je pokrenut lokalno i ima server reflection uključenu
- `buf` je dostupan kao Docker slika ili instaliran
- `grpcurl` je instaliran lokalno
- Proto fajlovi su u verzionisanoj strukturi (paket verzionisan, npr. `v1`)

**Van opsega:**
- TLS konfiguracija za produkcioni gRPC (to je infrastruktura, poseban task)
- gRPC-Web ili transkodovanje na HTTP/JSON
- Multi-language generated stubs (samo Go u ovoj vežbi)

**Prompt za diskusiju:**
```
Evo .proto fajla za [servis]. Hoću da dodam novo polje bez kvarenja postojećih klijenata.
Objasni pravila proto kompatibilnosti (šta sme, šta ne sme), kako buf breaking to štiti u CI-ju
i šta znači rezervisati uklonjena polja. Koji error kodovi (codes.NotFound, codes.InvalidArgument)
su ispravni za koji slučaj u ovom servisu?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Proto kontrakt zaštićen buf-om u CI; svaki RPC verifikovan grpcurl-om; error kodovi ispravni.

**Fajlovi koji se diraju:**
- `proto/` — izmene proto fajlova (ako testiramo novu poruku/polje)
- `.gitlab-ci.yml` — buf lint + buf breaking faza
- `buf.yaml` / `buf.gen.yaml` — buf konfiguracija

**Fajlovi koji se NE diraju:**
- Generisani `*_pb.go` fajlovi — generiše se automatski, ne editovati ručno
- `internal/` aplikacioni kod — samo ako RPC implementacija ima bug (poseban task)

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/proto-checks.mdc`
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/proto-checks.md`

Sadržaj pravila (isti za oba alata):
```
- Nikad ne menjaj broj ili tip postojećeg polja; uklonjena polja idu u `reserved`.
- CI pokreće `buf lint` + `buf breaking` against main grane; breaking promena blokira merge.
- Verzionisanje paketa (v1, v2) za nekompatibilne promene API-ja.
- Generisani stubs se ne edituju ručno — uvek regenerisati iz proto izvora.
- gRPC error kodovi moraju biti semantički ispravni (NotFound, InvalidArgument, itd.), ne samo generic Internal.
```

**Acceptance criteria:**
- [ ] `buf lint` prolazi bez grešaka
- [ ] `buf breaking` ne prijavljuje nenamerne breaking promene (namerne su dokumentovane)
- [ ] `grpcurl` poziv za svaki RPC vraća očekivani odgovor
- [ ] `grpcurl` za nepostojeći resurs vraća `codes.NotFound` (ne `codes.Internal`)
- [ ] `grpcurl` za neispravan argument vraća `codes.InvalidArgument`
- [ ] Streaming RPC streama ispravno (vidljivo više odgovora)
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Pokrenuti buf lint i buf breaking lokalno
2. Verifikovati svaki RPC poziv grpcurl-om (success, not-found, invalid-argument)
3. Testirati streaming RPC
4. Dodati buf u CI ako još nije

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno — posebno oko error kodova u ovom servisu?
```

---

## 3. Egzekucija

> **Cursor:** koristiš relevantnog agenta
> **Claude Code:** direktno u terminalu

```bash
# Buf lint — proveri proto stilska pravila
docker run --rm -v "$PWD":/work -w /work bufbuild/buf lint

# Buf breaking — proveri da nema breaking promena u odnosu na main
docker run --rm -v "$PWD":/work -w /work bufbuild/buf breaking \
  --against '.git#branch=main'

# Regeneriši stubs posle proto promena
docker run --rm -v "$PWD":/work -w /work bufbuild/buf generate

# gRPC server reflection — proveri koje servise server nudi
grpcurl -plaintext localhost:9090 list

# Pozovi RPC — success slučaj
grpcurl -plaintext -d '{"id":1}' localhost:9090 pkg.v1.OrderService/GetOrder

# Not found slučaj (id ne postoji)
grpcurl -plaintext -d '{"id":99999}' localhost:9090 pkg.v1.OrderService/GetOrder

# Invalid argument slučaj (id = 0 ili negativan)
grpcurl -plaintext -d '{"id":0}' localhost:9090 pkg.v1.OrderService/GetOrder

# Streaming RPC (ako postoji)
grpcurl -plaintext -d '{"filter":"active"}' localhost:9090 pkg.v1.OrderService/ListOrders
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- buf lint čist
- buf breaking bez nenamerne breaking promene
- grpcurl za success vraća očekivani odgovor
- grpcurl za not-found vraća codes.NotFound
- grpcurl za invalid-argument vraća codes.InvalidArgument
- Streaming RPC streama ispravno

Evo outputa buf i grpcurl komandi:
[ovde lepiš stvarni output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali i koji je ispravni error kod / proto popravak?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `grpcurl -plaintext localhost:9090 list` | Ispisani su svi servisi koje server nudi (reflection radi) |
| 2 | `grpcurl -plaintext -d '{"id":1}' localhost:9090 pkg.v1.OrderService/GetOrder` | Validan JSON odgovor sa svim očekivanim poljima |
| 3 | `grpcurl -plaintext -d '{"id":99999}' localhost:9090 pkg.v1.OrderService/GetOrder` | Error `code: NOT_FOUND` sa smislenom porukom, ne `INTERNAL` |
| 4 | `grpcurl -plaintext -d '{"id":0}' localhost:9090 pkg.v1.OrderService/GetOrder` | Error `code: INVALID_ARGUMENT` sa opisom koji argument je neispravan |
| 5 | Ručno promeni broj polja u `.proto` i pokreni `buf breaking` | buf prijavljuje breaking promenu i izlazi sa exit code != 0 |
| 6 | Ako postoji streaming RPC: pokreni `grpcurl` stream poziv | Primljeno više odgovora pre zatvaranja streama |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/grpc-tooling.md` ili `CLAUDE.md`

```
## [datum] — gRPC sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
