# Lab: secrets isolation for task-api

Configure task-api to keep secrets out of Claude's context, out of git, and blocked at commit time. This lab is narrowly scoped — it focuses on `.claudeignore`, `.env.example`, the pre-commit hook, and verifying the setup works. The broader security lab (06) covers config packages, UUID IDs, and SPEC security criteria.

Estimated time: 20–30 minutes.

**Prerequisites:**
- task-api repository with git initialized
- `.env` file exists locally (or you will create one)
- gitleaks installed (`brew install gitleaks` on macOS; see https://github.com/gitleaks/gitleaks for other platforms)

---

## Deliverable

A checklist you can tick off, saved to `docs/security-setup-checklist.md` in your task-api repo. You will fill it in as you complete each step.

---

## Step 1: Create .claudeignore

`.claudeignore` tells Claude Code which files to exclude from its file reads. Claude respects this file the same way git respects `.gitignore` — matching files are not read, even if explicitly asked for them in a prompt.

Create `.claudeignore` at the task-api project root:

```
# Secrets and credentials — Claude must never read these
.env
.env.*
.env.local
.env.production

# Key files
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519

# Named secrets directories
secrets/
credentials/
.secrets/

# Common credential files
.netrc
.npmrc_auth
```

For task-api specifically, the `.env` file is the primary concern. The others are defensive exclusions — they cost nothing to add and prevent a class of accidents entirely.

Verify the file is in place:

```bash
cat .claudeignore
```

---

## Step 2: Create .env.example

`.env.example` documents what environment variables the application expects. It contains no real values — it is a template committed to the repository. Anyone cloning the project knows exactly what to set.

Create `.env.example`:

```bash
# .env.example
# Copy this file to .env and fill in values for local development.
# NEVER commit .env — only .env.example is committed.

# Server configuration
PORT=8080
LOG_LEVEL=info

# Future use — leave commented until implemented
# DATABASE_URL=postgres://user:password@localhost:5432/taskapi
# JWT_SECRET=<generate with: openssl rand -hex 32>
# API_KEY=<your-api-key>
```

Add and commit it:

```bash
git add .env.example
git commit -m "add env.example with required variable documentation"
```

---

## Step 3: Create .env (local only)

Create your actual `.env` with real values (for task-api, these are not sensitive, but the pattern matters):

```bash
PORT=8080
LOG_LEVEL=debug
```

This file must not be committed. The next step ensures it cannot be.

---

## Step 4: Configure .gitignore

Open `.gitignore` and verify these lines are present. Add them if missing:

```
# Environment files — never commit
.env
.env.*
.env.local
.env.production

# Key and certificate files
*.pem
*.key
*.p12

# Secrets directories
secrets/
.secrets/
```

Verify `.env` is excluded:

```bash
git status
# .env should NOT appear in the output
```

If it appears as untracked, the gitignore rule is not matching. Check the exact file name:

```bash
git check-ignore -v .env
# Expected: .gitignore:1:.env    .env
```

If `git check-ignore` returns nothing, the file name in `.gitignore` does not match. Common cause: the `.env` file has trailing whitespace or is named `.env ` (note the space). Check with `ls -la` to confirm the exact file name.

---

## Step 5: Install and configure the pre-commit hook

The pre-commit hook runs gitleaks before every commit. If gitleaks finds a pattern matching a known secret format, the commit is blocked.

Create the hook:

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
# Run gitleaks on staged files before commit
gitleaks protect --staged --exit-code 1
if [ $? -ne 0 ]; then
    echo ""
    echo "COMMIT BLOCKED: secret detected in staged changes."
    echo "Remove the secret and try again."
    echo "If this is a known false positive, add an allowlist entry to .gitleaks.toml"
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

Verify it is executable:

```bash
ls -la .git/hooks/pre-commit
# Expected: -rwxr-xr-x ... .git/hooks/pre-commit
```

---

## Step 6: Create .gitleaks.toml

```toml
# .gitleaks.toml
title = "task-api gitleaks config"

[allowlist]
  description = "Allow test fixtures and documentation examples"
  regexes = [
    # Allow clearly fake values used in docs or test fixtures
    '''EXAMPLE''',
    '''PLACEHOLDER''',
    '''YOUR_.*_HERE''',
    # Allow test API key patterns explicitly named as test values
    '''sk-test-''',
  ]
```

Commit the gitleaks config:

```bash
git add .gitleaks.toml .claudeignore .gitignore
git commit -m "add secret detection config and claude ignore rules"
```

---

## Step 7: Test that the hook blocks a secret

Add a pattern that gitleaks recognizes as a secret to a Go file:

```bash
# Add a fake-but-realistic looking API key as a comment
echo '// apiKey = "sk-prod-abc123def456ghi789jkl012mno345pqr678stu901"' >> main.go
git add main.go
git commit -m "test: this commit should be blocked"
```

Expected result: the commit is blocked. gitleaks reports which pattern matched and on which line.

Now remove the test line:

```bash
# Edit main.go to remove the comment line you just added, then:
git checkout -- main.go
# or manually delete the line and re-stage
```

Verify a clean commit passes:

```bash
git add .
git commit -m "verify: clean commit passes gitleaks hook"
```

---

## Step 8: Verify Claude cannot read .env

Start a Claude Code session in the task-api directory. Send this message:

```
Read .env and tell me its contents.
```

Expected behavior: Claude cannot find the file or reports it is excluded by `.claudeignore`. It should not return the contents of your `.env` file.

If Claude does return the contents: verify `.claudeignore` is at the project root (same directory as `main.go`, not in a subdirectory). The file must be named `.claudeignore` with no extension.

```bash
ls -la .claudeignore
# Expected: file exists at project root
```

---

## Step 9: Create the deliverable checklist

Create `docs/security-setup-checklist.md`:

```bash
mkdir -p docs
```

Then write the file with your results:

```markdown
# Security setup checklist — task-api

## .claudeignore

- [ ] `.claudeignore` exists at project root
- [ ] `.env` is listed in `.claudeignore`
- [ ] `*.pem` and `*.key` are listed in `.claudeignore`
- [ ] Claude cannot read `.env` when asked directly (verified in Step 8)

## .env.example

- [ ] `.env.example` is committed to the repository
- [ ] `.env.example` lists all variables the application reads (PORT, LOG_LEVEL)
- [ ] `.env.example` contains no real values — only placeholders or defaults

## .gitignore

- [ ] `.env` is in `.gitignore`
- [ ] `git status` does not show `.env` as untracked
- [ ] `git check-ignore -v .env` returns a matching rule

## Pre-commit hook

- [ ] `.git/hooks/pre-commit` exists and is executable
- [ ] Hook runs gitleaks with `--staged` flag
- [ ] Test commit with a fake API key pattern was blocked (verified in Step 7)
- [ ] Clean commit after removing the test line passed without errors

## gitleaks configuration

- [ ] `.gitleaks.toml` exists at project root
- [ ] `.gitleaks.toml` is committed to the repository
- [ ] Allowlist entries are present for test fixtures and documentation examples
```

Tick off each item as you complete it. When every item is checked, this lab is complete.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `.env` still appears in `git status` | gitignore rule not matching | Check exact file name with `ls -la`; verify `.gitignore` has no trailing space on the rule |
| `git check-ignore -v .env` returns nothing | `.gitignore` rule syntax wrong | Match exact filename: `.env` not `*.env` |
| Hook not running on commit | File not executable | Run `chmod +x .git/hooks/pre-commit` |
| gitleaks not found by hook | Not installed or not in PATH | Run `brew install gitleaks` and verify `which gitleaks` |
| False positive blocking a test file | Test value matches a secret pattern | Add a regex allowlist entry in `.gitleaks.toml` |
| Claude reads `.env` despite `.claudeignore` | `.claudeignore` is in wrong directory | Move to project root — same directory as `main.go` |
