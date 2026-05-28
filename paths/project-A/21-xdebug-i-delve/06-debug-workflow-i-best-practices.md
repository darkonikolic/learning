# 06 — Debug workflow i best practices

## Kompletan workflow: od bug reporta do fix-a

### Scenario: "Login ne radi"

```
Bug report: Korisnik ne može se ulogovati. 
Error: 500 Internal Server Error
```

---

### Korak 1: Reproduciraj lokalno

```bash
# Pokreni sve servise sa debug override
docker compose up --build

# Provjeri da je debug aktivan
docker exec php-service php -m | grep xdebug    # mora pokazati: xdebug
docker compose logs go-service | grep "API server listening"  # Delve mora slušati

# Pokušaj reprodukovat bug
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass"}' \
  -v
# Pogledaj HTTP status, response body, i logove
```

Ako se bug ne reprodukuje lokalno:
- Provjeri environment varijable (database URL, external API keys)
- Provjeri da koristiš iste podatke kao u produkciji
- Ako je K8s-specifičan bug → pređi na modul 05 (debug u K8s)

---

### Korak 2: Postavi breakpoint-e i prati request

PHP Login endpoint (Slim Framework):

```php
// services/php-service/src/Actions/Auth/LoginAction.php
class LoginAction
{
    public function __invoke(Request $request, Response $response): Response
    {
        $data = $request->getParsedBody();  // ← breakpoint ovdje (linija 15)
        
        $email = $data['email'] ?? null;
        $password = $data['password'] ?? null;
        
        // Prati: da li su email i password ispravno parsirani?
        // Ako $data je null → Content-Type header problem
        
        $result = $this->authService->authenticate($email, $password);  // ← i ovdje
        // Prati: šta vraća authService?
```

Go Login handler:

```go
// services/go-service/internal/handlers/auth.go
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
    var req LoginRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {  // ← breakpoint
        h.logger.Error("decode error", zap.Error(err))
        http.Error(w, "invalid request", http.StatusBadRequest)
        return
    }
    
    token, err := h.authService.Authenticate(r.Context(), req.Email, req.Password)  // ← i ovdje
    // Inspect: req.Email, req.Password — da li su primljeni ispravno?
```

---

### Korak 3: X-Request-ID propagation za praćenje kroz servise

Kada PHP poziva Go servis, moramo pratiti koji request je koji kroz logove i debugger.

```php
// services/php-service/src/Actions/Auth/LoginAction.php
class LoginAction
{
    public function __invoke(Request $request, Response $response): Response
    {
        // Prihvati postojeći ID (od load balancera/API gateway-a) ili generiši novi
        $requestId = $request->getHeaderLine('X-Request-ID');
        if (empty($requestId)) {
            $requestId = 'php-' . bin2hex(random_bytes(8));
        }
        
        $this->logger->info('login attempt', [
            'request_id' => $requestId,
            'email' => $data['email'] ?? 'missing',
            'ip' => $request->getServerParam('REMOTE_ADDR'),
        ]);
        
        // Proslijedi request ID ka Go servisu
        $goResponse = $this->httpClient->post('/api/auth/validate', [
            'headers' => [
                'X-Request-ID' => $requestId,
                'Content-Type' => 'application/json',
            ],
            'json' => ['email' => $email, 'password' => $password],
        ]);
        
        // Kopiraj request ID u response za client-side tracking
        return $response->withHeader('X-Request-ID', $requestId);
    }
}
```

```go
// services/go-service/internal/handlers/auth.go
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
    requestId := r.Header.Get("X-Request-ID")
    if requestId == "" {
        requestId = "go-" + generateRequestId()
    }
    
    // Ubaci request ID u context za logging kroz cijeli call stack
    ctx := context.WithValue(r.Context(), contextKeyRequestID, requestId)
    
    h.logger.Info("validate request received",
        zap.String("request_id", requestId),
        zap.String("path", r.URL.Path),
    )
    
    // Svi downstream pozivi koriste ctx koji nosi request ID
    token, err := h.authService.Authenticate(ctx, req.Email, req.Password)
    
    // Vraćanje request ID-a u response header
    w.Header().Set("X-Request-ID", requestId)
```

Koristi X-Request-ID za korelaciju logova:

```bash
# Pošalji request sa eksplicitnim request ID-om
curl -X POST http://localhost/api/auth/login \
  -H "X-Request-ID: debug-test-001" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass"}'

# Pretraži logove po tom ID-u
docker compose logs php-service | grep "debug-test-001"
docker compose logs go-service | grep "debug-test-001"
```

---

### Korak 4: Pronalaženje uzroka

Tipičan scenario: request stiže na PHP, PHP zove Go, Go vraća grešku, PHP prosljeđuje 500.

U debuggeru, na breakpointu u PHP akciji:
```
Variables panel:
  $goResponse: GuzzleHttp\Psr7\Response
    statusCode: 401  ← Go vraća 401, ne 500!
    body: {"error":"invalid credentials","request_id":"debug-test-001"}
```

Ah — problem nije 500 od Go-a, problem je PHP prosljeđuje 401 kao 500. Grešaka u error handling-u.

```php
// Buggy kod:
$result = $this->callGoService($requestId, $email, $password);
return $response->withJson($result);  // ← baca exception ako $result nije array

// Fix:
$goResponse = $this->callGoService($requestId, $email, $password);
if ($goResponse['status'] !== 200) {
    return $response
        ->withStatus($goResponse['status'])
        ->withJson(['error' => $goResponse['error']]);
}
```

---

### Korak 5: Napiši test koji reprodukuje bug

**Uvijek napiši test PRIJE fix-a.** Test mora failovati sa bugom, prolaziti nakon fix-a.

```php
// tests/Actions/Auth/LoginActionTest.php
class LoginActionTest extends TestCase
{
    public function testLoginReturns401WhenCredentialsInvalid(): void
    {
        // Mock Go service da vraća 401
        $mockGoClient = $this->createMock(GoAuthClient::class);
        $mockGoClient->expects($this->once())
            ->method('validate')
            ->willReturn(['status' => 401, 'error' => 'invalid credentials']);
        
        $response = $this->app->handle(
            (new ServerRequest('POST', '/api/auth/login'))
                ->withParsedBody(['email' => 'test@test.com', 'password' => 'wrong'])
        );
        
        // Mora biti 401, ne 500!
        $this->assertSame(401, $response->getStatusCode());
        $body = json_decode((string) $response->getBody(), true);
        $this->assertArrayHasKey('error', $body);
    }
}
```

```bash
# Pokreni test — mora failovati (bug postoji)
docker exec php-service ./vendor/bin/phpunit tests/Actions/Auth/LoginActionTest.php
# FAIL: Expected status 401, got 500

# Sad fiksuj kod

# Pokreni test ponovo — mora proći
docker exec php-service ./vendor/bin/phpunit tests/Actions/Auth/LoginActionTest.php
# OK (1 test, 1 assertion)
```

---

### Korak 6: Commit i pipeline

```bash
git add services/php-service/src/Actions/Auth/LoginAction.php
git add tests/Actions/Auth/LoginActionTest.php
git commit -m "fix: return correct HTTP status from Go service response

LoginAction was swallowing 401 responses from Go auth service
and returning 500 instead. Added proper status code propagation
and regression test.

Fixes #123"
```

Pipeline mora:
1. Pokrenuti PHPUnit testove
2. Pokrenuti Go testove (`go test ./...`)
3. Build production image (bez Xdebug, bez Delve)
4. Verifikacija da debug alati nisu u prod image-u

---

## Debug vs logging: kada koji pristup

### Koristi debugger (Xdebug/Delve) kada:

- Bug je nereprodukabilan testom — trebaš vidjet živi sistem
- Kompleksna logika sa puno branching-a (business rules, state machines)
- Neočekivani podaci u runtime koji ne možeš predvidjet u testu
- Lokalni razvoj, brza iteracija
- Istraživanje novog koda koji ne razumiješ

### Koristi logging kada:

- Poznati error paths — logiraj svaki exception sa kontekstom
- Produkcija — debugger nije opcija
- Distributed systems — request prolazi kroz 5 servisa, debugger ne skalira
- Asinkroni kod — debugger ne radi dobro sa goroutine-ama i event loops-ovima
- Reprodukcija produkcijskog bug-a retrospektivno

```go
// Dobar logging primjer — dovoljno konteksta za post-mortem
logger.Error("payment failed",
    zap.String("request_id", requestId),
    zap.String("user_id", userID),
    zap.String("payment_provider", "stripe"),
    zap.String("stripe_error_code", stripeErr.Code),
    zap.Duration("duration", time.Since(start)),
    zap.String("order_id", orderID),
)
```

### Koristi pprof (Go) kada:

- Performance problem — endpoint spor bez vidljive logičke greške
- Memory leak — heap raste kroz vrijeme
- Goroutine leak — broj goroutine-a raste bez ograničenja
- CPU spike — ne znaš koji kod je skup

---

## NIKAD ne commit-ovati debug artefakte

### `.gitignore`

```gitignore
# Xdebug output
/profiles/
*.cachegrind
cachegrind.out.*
xdebug.log
xdebug_*.log
/tmp/xdebug*

# Delve debug binary-ji (Go generira ovo u projektnom direktoriju)
__debug_bin
__debug_bin*
*.debug

# pprof output
*.prof
cpu.prof
heap.prof
goroutine.prof

# Editor debug state
.vscode/.debug_*
```

### Pre-commit hook

```bash
# .git/hooks/pre-commit (ili via lefthook/husky)

# Provjeri da nema Cachegrind fajlova staged za commit
if git diff --cached --name-only | grep -q "cachegrind.out"; then
  echo "ERROR: Cachegrind profiling file staged for commit!"
  echo "Remove with: git restore --staged"
  exit 1
fi

# Provjeri da xdebug.ini nije u production Dockerfile-u
if git diff --cached -- "docker/php/Dockerfile" | grep -q "xdebug.ini"; then
  echo "WARNING: xdebug.ini referenced in Dockerfile. Is this intentional?"
fi
```

---

## CI provjera: debug alati nisu u prod image-u

### GitLab CI job

```yaml
# .gitlab-ci.yml

verify:no-debug-in-production:
  stage: verify
  image: docker:24-cli
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    # Provjeri PHP image — Xdebug ne smije biti aktivan
    - |
      docker pull $CI_REGISTRY_IMAGE/php-service:$CI_COMMIT_SHA
      
      XDEBUG_RESULT=$(docker run --rm $CI_REGISTRY_IMAGE/php-service:$CI_COMMIT_SHA \
        php -m | grep -c "^xdebug$" || true)
      
      if [ "$XDEBUG_RESULT" -gt "0" ]; then
        echo "FAIL: Xdebug is loaded in production PHP image!"
        echo "  Image: $CI_REGISTRY_IMAGE/php-service:$CI_COMMIT_SHA"
        echo "  Fix: Ensure production Dockerfile target doesn't include xdebug.ini"
        exit 1
      fi
      echo "OK: Xdebug not loaded in PHP production image"
    
    # Provjeri Go image — ne smije imati Delve binary
    - |
      docker pull $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA
      
      DLV_RESULT=$(docker run --rm $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA \
        sh -c "[ -f /dlv ] && echo FOUND || echo NOT_FOUND")
      
      if [ "$DLV_RESULT" = "FOUND" ]; then
        echo "FAIL: Delve binary found in production Go image!"
        exit 1
      fi
      echo "OK: Delve not present in Go production image"
    
    # Provjeri Go binary — ne smije biti debug build
    - |
      # Debug build je veći od 20MB zbog DWARF simbola
      GO_BINARY_SIZE=$(docker run --rm $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA \
        sh -c "wc -c < /app/server")
      
      if [ "$GO_BINARY_SIZE" -gt 20971520 ]; then
        echo "WARNING: Go binary unusually large ($GO_BINARY_SIZE bytes)"
        echo "  May be a debug build. Verify with: file /app/server"
      fi

  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH =~ /^release\//
```

### Lokalna verifikacija prije push-a

```bash
#!/usr/bin/env bash
# scripts/verify-prod-image.sh

set -euo pipefail

echo "Building production images..."
docker compose -f docker-compose.yml build

echo ""
echo "=== PHP Image Verification ==="
PHP_IMAGE=$(docker compose -f docker-compose.yml config | grep "image:" | head -1 | awk '{print $2}')
docker build --target production -t verify-php-prod ./docker/php/
docker run --rm verify-php-prod php -m | grep -v "^xdebug$" > /dev/null && \
  echo "PASS: Xdebug not loaded" || \
  echo "FAIL: Xdebug IS loaded in production image!"

echo ""
echo "=== Go Image Verification ==="
docker build -f docker/go/Dockerfile -t verify-go-prod ./services/go-service/
docker run --rm verify-go-prod sh -c "[ -f /dlv ] && echo 'FAIL: Delve found!' || echo 'PASS: Delve not present'"
docker run --rm verify-go-prod file /app/server | grep -q "not stripped" && \
  echo "WARNING: Binary not stripped (debug build?)" || \
  echo "PASS: Binary stripped"

echo ""
echo "Cleanup..."
docker rmi verify-php-prod verify-go-prod 2>/dev/null || true
```

---

## Checklist: setup novog projekta za debugging

```
[ ] docker-compose.yml — base konfiguracija, bez debug
[ ] docker-compose.override.yml — debug override, commit-ovan
[ ] docker/php/Dockerfile — multi-stage: base, debug, production
[ ] docker/php/xdebug.ini — Xdebug 3 konfiguracija
[ ] docker/go/Dockerfile.debug — Delve + debug build flagovi
[ ] .vscode/launch.json — PHP + Go konfiguracije + compounds
[ ] .vscode/extensions.json — preporuke za kolege
[ ] .gitignore — debug artefakti izuzeti
[ ] CI job — verify:no-debug-in-production
[ ] scripts/verify-prod-image.sh — lokalna verifikacija
[ ] README.md — upute za debug setup za novog developera
```

---

## Dijagnostički cheat sheet

```bash
# PHP: da li Xdebug radi?
docker exec php-service php -i | grep "xdebug.mode"

# PHP: zašto se Xdebug ne konektuje?
docker exec php-service bash -c \
  "echo 'xdebug.log_level=7' >> /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini && kill -USR2 1"
docker exec php-service tail -f /tmp/xdebug.log

# Go: da li Delve sluša?
nc -z localhost 40000 && echo "OK" || echo "FAIL"

# Go: da li binary ima debug simbole?
docker exec go-service file /app/server | grep -c "not stripped"

# Oba: koji su portovi dostupni na hostu?
lsof -i :9003 -i :40000

# Compose: koji targets se grade?
docker compose config | grep -E "target:|dockerfile:"
```
