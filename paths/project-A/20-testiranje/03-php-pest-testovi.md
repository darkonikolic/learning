# 03 — PHP Pest testovi

## Zašto Pest umjesto PHPUnit

PHPUnit je standard od 2004. godine. Pest je moderna alternativa koja kompajlira na PHPUnit, ali nudi:

| | PHPUnit | Pest |
|--|---------|------|
| Test sintaksa | `class LoginTest extends TestCase { public function test_login() {} }` | `test('login works', fn() => ...)` |
| Dataset support | `@dataProvider` + zasebna metoda | `->with([...])` inline |
| Paralelno izvršavanje | Plugin (slow) | Ugrađeno (`--parallel`) |
| Assertion API | `$this->assertEquals()` | `expect()->toBe()` |
| Error messages | Verbose stack trace | Čitak diff output |

Pest je 100% kompatibilan s PHPUnit — može koristiti PHPUnit assertions, PHPUnit mocks, existing PHPUnit test cases. Migracija je inkrementalna.

Instalacija:
```bash
composer require pestphp/pest --dev --with-all-dependencies
./vendor/bin/pest --init  # kreira pest.php config
```

---

## Unit testovi za PHP proxy service

PHP service u ovoj arhitekturi je thin proxy: prima HTTP request, validira input, prosljeđuje Go servisu, vraća odgovor. Svaki od ovih koraka je testabilan u izolaciji.

### Proxy logika

```php
// tests/Unit/AuthProxyTest.php

use App\Services\AuthProxy;
use App\Services\HttpClient;
use GuzzleHttp\Psr7\Response;

test('proxies valid request to go service', function () {
    $mockClient = Mockery::mock(HttpClient::class);
    $mockClient
        ->shouldReceive('post')
        ->once()
        ->with('/api/auth/login', Mockery::on(function ($options) {
            return isset($options['json']['email'])
                && $options['json']['email'] === 'user@test.com';
        }))
        ->andReturn(new Response(200, [], '{"token":"jwt123","expires_in":3600}'));

    $proxy = new AuthProxy($mockClient);
    $response = $proxy->login('user@test.com', 'password');

    expect($response->getStatusCode())->toBe(200);

    $body = json_decode($response->getBody(), true);
    expect($body)->toHaveKey('token');
    expect($body['token'])->toBe('jwt123');
});

test('propagates 401 from go service', function () {
    $mockClient = Mockery::mock(HttpClient::class);
    $mockClient
        ->shouldReceive('post')
        ->once()
        ->andReturn(new Response(401, [], '{"error":"invalid_credentials"}'));

    $proxy = new AuthProxy($mockClient);
    $response = $proxy->login('user@test.com', 'wrongpass');

    expect($response->getStatusCode())->toBe(401);
});

test('propagates 503 when go service is down', function () {
    $mockClient = Mockery::mock(HttpClient::class);
    $mockClient
        ->shouldReceive('post')
        ->once()
        ->andThrow(new \GuzzleHttp\Exception\ConnectException(
            'Connection refused',
            new \GuzzleHttp\Psr7\Request('POST', '/api/auth/login')
        ));

    $proxy = new AuthProxy($mockClient);
    $response = $proxy->login('user@test.com', 'pass');

    expect($response->getStatusCode())->toBe(503);
});
```

`Mockery::once()` verificira da je metoda pozvana tačno jednom. Ako se ne pozove, test pada. Ovo testira da proxy zaista prosljeđuje request — nije samo provjera return vrijednosti.

### Timeout i retry ponašanje

```php
test('retries on timeout, max 2 attempts', function () {
    $mockClient = Mockery::mock(HttpClient::class);
    $mockClient
        ->shouldReceive('post')
        ->twice() // tačno 2 poziva
        ->andThrow(new \GuzzleHttp\Exception\RequestException(
            'Timeout',
            new \GuzzleHttp\Psr7\Request('POST', '/api/auth/login'),
            new Response(504)
        ));

    $proxy = new AuthProxy($mockClient, maxRetries: 2);
    $response = $proxy->login('user@test.com', 'pass');

    expect($response->getStatusCode())->toBe(504);
});
```

---

## Input validation — Pest datasets

Pest datasets su prvi-class citizen, ne afterthought.

```php
// Inline dataset
dataset('invalid_emails', [
    'empty string'    => [''],
    'no at sign'      => ['notanemail'],
    'no domain'       => ['user@'],
    'no tld'          => ['user@domain'],
    'spaces'          => ['user @test.com'],
    'too long'        => [str_repeat('x', 250) . '@test.com'],
    'sql injection'   => ["'; DROP TABLE users;--"],
    'xss attempt'     => ['<script>alert(1)</script>@test.com'],
]);

dataset('invalid_passwords', [
    'empty string'    => [''],
    'too short'       => ['abc'],        // ispod 8 znakova
    'too long'        => [str_repeat('x', 256)],
    'null byte'       => ["pass\x00word"],
]);

test('rejects invalid email', function (string $email) {
    $validator = new InputValidator();
    expect($validator->validateEmail($email))->toBeFalse();
})->with('invalid_emails');

test('rejects invalid password', function (string $password) {
    $validator = new InputValidator();
    expect($validator->validatePassword($password))->toBeFalse();
})->with('invalid_passwords');

// Combined dataset: sve kombinacije
test('rejects any combination of invalid input', function (string $email, string $password) {
    $validator = new InputValidator();
    expect($validator->validate($email, $password))->toBeFalse();
})->with([
    ['', 'password'],          // empty email
    ['notanemail', 'pass'],    // invalid format
    ['u@t.com', ''],           // empty password
    [str_repeat('x', 256), 'pass'],  // email too long
]);
```

Za razliku od PHPUnit `@dataProvider`, dataset je definisan inline ili u zasebnom fajlu koji se referencira po imenu. Čitljivost u test outputu — svaki row dobiva ime:

```
✓ rejects invalid email > empty string
✓ rejects invalid email > no at sign
✗ rejects invalid email > sql injection  ← odmah vidiš koji case pada
```

---

## Session handling

```php
test('creates session on successful login', function () {
    $sessionStore = new InMemorySessionStore();
    $handler = new SessionHandler($sessionStore);

    $handler->create('user-123', ['email' => 'u@t.com']);

    expect($sessionStore->has('user-123'))->toBeTrue();
    expect($sessionStore->get('user-123'))->toMatchArray([
        'email' => 'u@t.com',
    ]);
});

test('session expires after ttl', function () {
    $sessionStore = new InMemorySessionStore();
    $handler = new SessionHandler($sessionStore, ttl: 1); // 1 sekunda

    $handler->create('user-123', ['email' => 'u@t.com']);
    sleep(2);

    expect($sessionStore->has('user-123'))->toBeFalse();
});

test('destroys session on logout', function () {
    $sessionStore = new InMemorySessionStore();
    $handler = new SessionHandler($sessionStore);

    $handler->create('user-123', ['email' => 'u@t.com']);
    $handler->destroy('user-123');

    expect($sessionStore->has('user-123'))->toBeFalse();
});
```

`InMemorySessionStore` je test double koji implementira isti interface kao Redis session store. Brzo, bez I/O, determinirano. Za session TTL test — `sleep(2)` je jedina opcija za provjeru vremenskog ponašanja u unit testu (u integration testu koristiš Redis TTL direktno).

---

## PHP u Dockerfile multi-stage buildu

```dockerfile
# Stage 1: Composer dependencies
FROM composer:2.7 AS composer-deps
WORKDIR /app
COPY composer.json composer.lock .
RUN composer install --no-dev --no-scripts --prefer-dist --optimize-autoloader

# Stage 2: Test dependencies (uključuje dev)
FROM php:8.3-fpm-alpine AS test-deps
RUN apk add --no-cache $PHPIZE_DEPS \
    && pecl install xdebug \
    && docker-php-ext-enable xdebug
COPY --from=composer /usr/bin/composer /usr/bin/composer
WORKDIR /app
COPY composer.json composer.lock .
RUN composer install --with-all-dependencies  # uključuje dev dependencies
COPY . .

# Stage 3: Test
FROM test-deps AS test
RUN ./vendor/bin/pest --ci \
    --log-junit=junit.xml \
    --coverage-cobertura=coverage.xml \
    --min=70  # fail ako coverage < 70%

# Stage 4: Production (bez dev dependencies, bez test alata)
FROM php:8.3-fpm-alpine AS production
WORKDIR /app
COPY --from=composer-deps /app/vendor /app/vendor
COPY . .
# Ukloni test fajlove iz production image-a
RUN rm -rf tests/ phpunit.xml pest.php
```

Ključna razlika: `composer-deps` stage koristi `--no-dev` (production vendor). `test-deps` stage koristi sve dependencije. Production image nikad ne sadrži Pest, Mockery, ili bilo šta test-related.

Xdebug je potreban za coverage reporting. Bez Xdebug ili PCOV extensiona, `--coverage` flag ne radi.

---

## GitLab JUnit artifact

```yaml
test:php:
  stage: test
  image: php:8.3-fpm-alpine
  before_script:
    - apk add --no-cache $PHPIZE_DEPS
    - pecl install xdebug && docker-php-ext-enable xdebug
    - curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
    - composer install --with-all-dependencies
  script:
    - ./vendor/bin/pest --ci --log-junit=junit.xml --coverage-cobertura=coverage.xml --min=70
  artifacts:
    when: always  # sačuvaj artifact čak i ako test padne — trebaš junit.xml za failure report
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 1 week
```

`when: always` je bitan za JUnit artifact. Defaultno, GitLab ne sačuva artifacts ako job padne. Ali ti trebaš junit.xml upravo kad test padne — da GitLab može pokazati koji testovi su pali u MR UI.

Pest `--ci` flag: non-interactive output, no progress spinner, exits 1 na failure.

---

## Pest konfiguracija (pest.php)

```php
<?php
// pest.php — u root projekta

uses(Tests\TestCase::class)->in('tests/Unit', 'tests/Integration');

// Globalni after each: čisti Mockery
afterEach(function () {
    Mockery::close();
});

// Custom helper funkcija dostupna u svim testovima
function createTestUser(string $email = 'test@example.com'): array {
    return ['id' => 'user-' . uniqid(), 'email' => $email];
}
```

`Mockery::close()` u `afterEach` verificira da su sva `shouldReceive` expectations bila zadovoljena. Bez toga, mock koji nikad nije pozvan ne pada test — tiha greška.
