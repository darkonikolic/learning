# 17 — Swagger API Dokumentacija

## Zašto API docs nisu opcija

Bez dokumentacije frontend tim mora čitati Go kod ili pitati backend dev za svaki endpoint.
Swagger riješava:

- Frontend radi nezavisno od backenda
- QA testira endpointove direktno iz browsera
- Novi devovi onboard za sat, ne dan
- API kontrakt je vidljiv — promjena endpointa = promjena docs-a (i CI to prati)

---

## swaggo/swag za Go

```bash
# Instalacija alata (jednom, lokalno):
go install github.com/swaggo/swag/cmd/swag@latest

# Ili kroz Docker (bez lokalnog Go toolchain-a):
docker run --rm \
  -v "$(pwd)/services/go-service:/app" \
  -w /app \
  golang:1.22 \
  sh -c "go install github.com/swaggo/swag/cmd/swag@latest && swag init -g cmd/main.go -o docs/"
```
> **Podman:** `podman run --rm -v "$(pwd)/services/go-service:/app" -w /app golang:1.22 sh -c "go install github.com/swaggo/swag/cmd/swag@latest && swag init -g cmd/main.go -o docs/"`

```bash
# Zavisnosti u go-service:
go get github.com/swaggo/swag
go get github.com/swaggo/http-swagger
go get github.com/swaggo/files
```

---

## Globalne anotacije (main.go)

```go
// cmd/main.go

// @title           Project-A API
// @version         1.0
// @description     Backend API za Project-A (Vue+PHP+Go stack)
// @contact.name    Backend Team
// @contact.email   backend@firma.com

// @host            api.firma.com
// @BasePath        /api

// @securityDefinitions.apikey BearerAuth
// @in              header
// @name            Authorization
// @description     JWT token — format: "Bearer {token}"

// @schemes         https
// @produce         json
// @consumes        json
package main

import (
    _ "project-a/docs" // Auto-generated swagger docs — NE BRISI ovaj import

    "github.com/swaggo/http-swagger"
    "github.com/swaggo/files"
)

func setupRouter(env string) http.Handler {
    mux := http.NewServeMux()

    // Swagger UI — samo za non-production environmente
    if env != "production" {
        mux.Handle("/swagger/", httpSwagger.Handler(
            httpSwagger.URL("/swagger/doc.json"),
            httpSwagger.DeepLinking(true),
        ))
        // http://localhost:8080/swagger/ — interaktivni UI
        // http://localhost:8080/swagger/doc.json — raw JSON spec
    }

    // ... ostali routevi
    return mux
}
```

---

## Anotacije za Auth endpointove

```go
// handlers/auth.go

// Login godoc
// @Summary      Prijava korisnika
// @Description  Autentifikacija emailom i lozinkom. Vraća JWT access token.
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        request  body      LoginRequest   true  "Email i lozinka"
// @Success      200      {object}  LoginResponse
// @Failure      400      {object}  ErrorResponse  "Neispravan JSON ili nedostaju polja"
// @Failure      401      {object}  ErrorResponse  "Pogrešni kredencijali"
// @Failure      403      {object}  ErrorResponse  "Email nije verificiran"
// @Failure      429      {object}  ErrorResponse  "Previše pokušaja — pričekaj"
// @Router       /auth/login [post]
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
    // ...
}

// Register godoc
// @Summary      Registracija novog korisnika
// @Description  Kreira korisnika i šalje verification email.
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        request  body      RegisterRequest  true  "Podaci za registraciju"
// @Success      201      {object}  RegisterResponse
// @Failure      400      {object}  ValidationErrorResponse  "Validacijska greška"
// @Failure      409      {object}  ErrorResponse            "Email već postoji"
// @Router       /auth/register [post]
func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
    // ...
}

// RefreshToken godoc
// @Summary      Refresh JWT tokena
// @Description  Zamijeni refresh token za novi access token.
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        request  body      RefreshRequest   true  "Refresh token"
// @Success      200      {object}  LoginResponse
// @Failure      401      {object}  ErrorResponse    "Refresh token nevažeći ili istekao"
// @Router       /auth/refresh [post]
func (h *AuthHandler) RefreshToken(w http.ResponseWriter, r *http.Request) {
    // ...
}
```

---

## Anotacije za zaštićene endpointove

```go
// handlers/user.go

// GetProfile godoc
// @Summary      Profil trenutnog korisnika
// @Description  Vraća podatke o prijavljenom korisniku (iz JWT-a).
// @Tags         users
// @Produce      json
// @Security     BearerAuth
// @Success      200  {object}  UserProfileResponse
// @Failure      401  {object}  ErrorResponse  "Nevažeći ili istekli token"
// @Router       /users/me [get]
func (h *UserHandler) GetProfile(w http.ResponseWriter, r *http.Request) {
    // ...
}

// UpdateProfile godoc
// @Summary      Ažuriranje profila
// @Tags         users
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        request  body      UpdateProfileRequest  true  "Podaci za ažuriranje"
// @Success      200      {object}  UserProfileResponse
// @Failure      400      {object}  ValidationErrorResponse
// @Failure      401      {object}  ErrorResponse
// @Router       /users/me [put]
func (h *UserHandler) UpdateProfile(w http.ResponseWriter, r *http.Request) {
    // ...
}
```

---

## Request/Response modeli sa primjerima

```go
// models/auth_api.go
// (Odvojen fajl od domain modela — API kontrakt se ne mijenja s DB shemom)

// LoginRequest predstavlja tijelo zahtjeva za prijavu.
type LoginRequest struct {
    Email    string `json:"email"    example:"korisnik@firma.com" validate:"required,email"`
    Password string `json:"password" example:"MojaLozinka123!"     validate:"required,min=8"`
}

// LoginResponse vraća JWT tokene nakon uspješne prijave.
type LoginResponse struct {
    AccessToken  string `json:"access_token"  example:"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."`
    RefreshToken string `json:"refresh_token" example:"dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."`
    ExpiresIn    int    `json:"expires_in"    example:"900"` // sekunde (15 minuta)
    TokenType    string `json:"token_type"    example:"Bearer"`
}

// RegisterRequest sadrži podatke za kreiranje novog korisnika.
type RegisterRequest struct {
    Email     string `json:"email"      example:"novi@firma.com"  validate:"required,email"`
    Password  string `json:"password"   example:"MojaLozinka123!" validate:"required,min=8"`
    FirstName string `json:"first_name" example:"Marko"           validate:"required,max=100"`
    LastName  string `json:"last_name"  example:"Marković"        validate:"required,max=100"`
}

// RegisterResponse vraća potvrdu registracije.
type RegisterResponse struct {
    Message string `json:"message" example:"Registracija uspješna. Provjeri email za verifikaciju."`
    UserID  int64  `json:"user_id" example:"42"`
}

// RefreshRequest sadrži refresh token za obnovu sesije.
type RefreshRequest struct {
    RefreshToken string `json:"refresh_token" example:"dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..." validate:"required"`
}

// UserProfileResponse vraća javne podatke korisnika.
type UserProfileResponse struct {
    ID        int64  `json:"id"         example:"42"`
    Email     string `json:"email"      example:"korisnik@firma.com"`
    FirstName string `json:"first_name" example:"Marko"`
    LastName  string `json:"last_name"  example:"Marković"`
    CreatedAt string `json:"created_at" example:"2025-01-15T10:30:00Z"`
}

// UpdateProfileRequest sadrži polja koja korisnik može mijenjati.
type UpdateProfileRequest struct {
    FirstName string `json:"first_name" example:"Marko"     validate:"omitempty,max=100"`
    LastName  string `json:"last_name"  example:"Marković"  validate:"omitempty,max=100"`
}

// ErrorResponse je standardni format greške za sve endpointove.
type ErrorResponse struct {
    Error   string `json:"error"   example:"invalid_credentials"`
    Message string `json:"message" example:"Email ili lozinka su pogrešni."`
}

// ValidationErrorResponse vraća detalje o validacijskim greškama po poljima.
type ValidationErrorResponse struct {
    Error  string            `json:"error"  example:"validation_failed"`
    Fields map[string]string `json:"fields" example:"{\"email\":\"Neispravan format emaila.\"}"`
}
```

---

## Makefile targeti

```makefile
# services/go-service/Makefile

.PHONY: swagger swagger-check swagger-serve

## swagger: Generiši Swagger docs iz anotacija u kodu
swagger:
	docker run --rm \
	  -v "$(shell pwd):/app" \
	  -w /app \
	  golang:1.22 \
	  sh -c "go install github.com/swaggo/swag/cmd/swag@latest && \
	         swag init -g cmd/main.go -o docs/ --parseDependency --parseInternal"
	@echo "Swagger docs generirani. Pokreni servis i idi na: http://localhost:8080/swagger/"

## swagger-check: Provjeri da su Swagger docs ažurirani (za CI)
swagger-check:
	docker run --rm \
	  -v "$(shell pwd):/app" \
	  -w /app \
	  golang:1.22 \
	  sh -c "go install github.com/swaggo/swag/cmd/swag@latest && \
	         swag init -g cmd/main.go -o /tmp/swagger-check/ --parseDependency --parseInternal && \
	         diff -r /tmp/swagger-check/ docs/ || \
	         (echo 'Swagger docs su zastarjeli. Pokreni: make swagger i commitaj docs/' && exit 1)"

## swagger-serve: Pokreni lokalno za pregled bez pokretanja cijelog servisa
swagger-serve:
	docker run --rm -p 8081:8080 \
	  -e SWAGGER_JSON=/docs/swagger.json \
	  -v "$(shell pwd)/docs:/docs" \
	  swaggerapi/swagger-ui
	@echo "Swagger UI dostupan na: http://localhost:8081"
```
> **Podman:** zamijeni `docker run` sa `podman run` u svim Makefile targetima (`swagger`, `swagger-check`, `swagger-serve`)

---

## GitLab CI integracija

```yaml
# .gitlab-ci.yml

lint:swagger:
  stage: validate
  image: golang:1.22
  script:
    - cd services/go-service
    - go install github.com/swaggo/swag/cmd/swag@latest
    - swag init -g cmd/main.go -o /tmp/swagger-check/ --parseDependency --parseInternal
    - |
      diff -r /tmp/swagger-check/ docs/ || {
        echo "GREŠKA: Swagger docs su zastarjeli."
        echo "Pokreni 'make swagger' i commitaj promjene u docs/ folder."
        exit 1
      }
  rules:
    - changes:
        - services/go-service/**/*.go
```

```yaml
# Ako swagger nije generiran nikad — ovo ga generiše u CI i commituje:
# (Alternativni pristup — manje striktan od diff-a)
generate:swagger:
  stage: prepare
  image: golang:1.22
  script:
    - cd services/go-service
    - go install github.com/swaggo/swag/cmd/swag@latest
    - swag init -g cmd/main.go -o docs/ --parseDependency --parseInternal
  artifacts:
    paths:
      - services/go-service/docs/
    expire_in: 1 hour
  rules:
    - changes:
        - services/go-service/**/*.go
```

---

## Helm: Swagger dostupnost po environmentu

```yaml
# helm/project-a/templates/ingress.yaml

{{- if ne .Values.environment "production" }}
# Swagger UI dostupan na non-prod environmentima:
# Dev:     https://api.dev.firma.com/swagger/
# Staging: https://api.staging.firma.com/swagger/
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "project-a.fullname" . }}-swagger
  annotations:
    nginx.ingress.kubernetes.io/auth-type:   basic
    nginx.ingress.kubernetes.io/auth-secret: swagger-basic-auth
    nginx.ingress.kubernetes.io/auth-realm:  "Swagger UI — Autorizacija potrebna"
spec:
  rules:
    - host: {{ .Values.ingress.apiHost }}
      http:
        paths:
          - path: /swagger
            pathType: Prefix
            backend:
              service:
                name: {{ include "project-a.fullname" . }}-go
                port:
                  number: 8080
{{- end }}
```

```bash
# Kreiranje basic auth za Swagger pristup (ne ostavljaj javno otvoreno):
htpasswd -bc /tmp/swagger-auth dev SuperTajnaLozinka
kubectl create secret generic swagger-basic-auth \
  --from-file=auth=/tmp/swagger-auth \
  --namespace=project-a-dev
```

---

## Workflow: Dodavanje novog endpointa

```
1. Napiši handler funkciju
2. Dodaj swag anotacije iznad funkcije
3. Definiši Request/Response struct s `example` tagovima
4. Pokreni: make swagger
5. Commitaj: git add handlers/foo.go models/foo_api.go docs/
6. CI provjeri da su docs ažurirani
```

---

## Checklist

- [ ] `swag init` generiše docs bez errora (`make swagger`)
- [ ] `_ "project-a/docs"` import postoji u `main.go`
- [ ] Swagger UI otvara se na `http://localhost:8080/swagger/` u dev
- [ ] Swagger UI **nije** dostupan u production (`APP_ENV=production`)
- [ ] CI job `lint:swagger` pada ako su docs zastarjeli
- [ ] Svi Request/Response structs imaju `example` tagove
- [ ] Auth endpointovi imaju ispravne `@Failure 401` i `@Failure 429` anotacije
- [ ] `docs/` folder je commitovan u git
