# settings.json and permissions

Settings control what Claude does without asking, what it must ask before doing, and what it is never allowed to do. A well-configured settings.json is the difference between a productive session and a session spent answering permission prompts.

The default behavior prompts for most operations. That is safe but slow. Configure allow and deny deliberately: allow the low-risk operations you use constantly, deny the high-impact operations that need human judgment, and leave everything else as a prompt.

---

## Where settings.json lives

| File | Scope | Committed? |
|------|-------|-----------|
| `~/.claude/settings.json` | User — all projects on this machine | No — personal |
| `.claude/settings.json` | Project — this repo only | Yes — team policy |
| `.claude/settings.local.json` | Personal project override | No — gitignored |

Precedence: managed policy > command-line flags > local > project > user.

Arrays (allow lists, deny lists) merge across levels — they do not replace. A project `allow` adds to your user `allow`. It does not override it.

What to commit: `.claude/settings.json` with team policy. What not to commit: `.claude/settings.local.json` (personal tokens, local paths, personal shortcuts).

---

## Full annotated settings.json for task-api

```json
{
  "permissions": {
    "allow": [
      "Bash(go build ./...)",
      "Bash(go test ./...)",
      "Bash(go test -race ./...)",
      "Bash(go test -v ./...)",
      "Bash(go vet ./...)",
      "Bash(go fmt ./...)",
      "Bash(go run .)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git log --oneline *)",
      "Bash(ls *)",
      "Bash(find . *)",
      "Bash(cat *)",
      "Read(./**)"
    ],
    "deny": [
      "Bash(git push *)",
      "Bash(git push --force *)",
      "Bash(rm -rf *)",
      "Bash(git reset --hard *)",
      "Bash(curl -X POST *)",
      "Bash(curl -X DELETE *)",
      "Bash(curl -X PATCH *)",
      "Read(.env)",
      "Read(.env.*)",
      "Read(./secrets/**)"
    ]
  },
  "env": {
    "PORT": "8080",
    "LOG_LEVEL": "debug"
  },
  "defaultMode": "default"
}
```

---

## Permission syntax

Pattern format: `"Tool(command-pattern)"`.

| Part | Meaning |
|------|---------|
| `Tool` | The Claude tool name: Bash, Read, Edit, Write, WebFetch |
| `command-pattern` | What to match — supports `*` as wildcard |

Examples:
- `"Bash(go test *)"` — allows `go test ./...`, `go test -v ./...`, `go test -race ./...`
- `"Bash(git diff *)"` — allows `git diff HEAD`, `git diff main`, `git diff -- file.go`
- `"Bash(git push *)"` — in deny: blocks all forms of git push including `--force`
- `"Read(./**)"` — allows reading any file in the project

The wildcard `*` matches the rest of the command argument. `Bash(git push *)` matches `git push origin main` and `git push --force`. Use this in deny to block all variants.

---

## Allow list: design principles

Allow operations that are:
- **Read-only:** no side effects, no state change
- **Idempotent:** safe to run multiple times
- **Local:** affect only this machine's working directory
- **Reversible:** if they go wrong, easily undone

For Go projects, allow: build, test, vet, fmt, run, and git read operations. These are low-risk and frequently needed.

```json
"allow": [
  "Bash(go build ./...)",
  "Bash(go test ./...)",
  "Bash(go vet ./...)",
  "Bash(go fmt ./...)",
  "Bash(git status)",
  "Bash(git diff *)",
  "Bash(git log *)",
  "Read(./**)"
]
```

These operations run without prompting. Claude can build, test, and read code without interrupting you.

**Allow list by project type:**

| Project type | Add to allow |
|-------------|-------------|
| Go | go build, go test, go vet, go fmt, go run |
| Node.js | npm test, npm run lint, npm run build |
| Python | pytest, flake8, black --check |
| Any | git status, git diff, git log, ls, find, cat |
| Infrastructure | terraform plan, terraform validate |

---

## Deny list: design principles

Deny operations that are:
- **Irreversible:** cannot be undone without effort
- **External:** reach outside the local working directory
- **High blast radius:** affect many users or systems
- **Secret-touching:** would bring secrets into context

```json
"deny": [
  "Bash(git push *)",
  "Bash(git push --force *)",
  "Bash(rm -rf *)",
  "Bash(git reset --hard *)",
  "Read(.env)",
  "Read(.env.*)"
]
```

Deny rules are absolute. They override allow rules. They override user instructions. If something is in deny, it does not run.

This is intentional. "Deny" means "never" — not "ask me first." Use "deny" for operations where even being asked is not an acceptable interface. Use allow/ask for everything else.

**Deny list by risk category:**

| Risk category | What to deny |
|--------------|-------------|
| Irreversible git operations | git push, git reset --hard, git push --force |
| Destructive filesystem | rm -rf |
| Secrets | Read(.env), Read(.env.*), Read(./secrets/**) |
| External mutations | curl POST, curl DELETE, curl PATCH to non-localhost |
| Database operations | Any direct DB command (psql, mysql with mutations) |
| Infrastructure changes | terraform apply, kubectl delete |

---

## Environment variables

```json
"env": {
  "PORT": "8080",
  "LOG_LEVEL": "debug",
  "TASK_API_DB_URL": "postgres://localhost/taskdb_dev"
}
```

Environment variables in settings.json are injected into Claude's shell environment. Use for:
- Non-sensitive project configuration
- Ports and local URLs Claude needs when running commands
- Development-mode flags

Do not use for:
- API keys, tokens, passwords (use `.claude/settings.local.json` or shell environment)
- Secrets of any kind (settings.json is committed to git)

If your project needs secrets, keep them in your shell environment (`export SECRET=value` in .zshrc) or in `.claude/settings.local.json` (gitignored). Reference the variable name in settings.json comments if needed: `"// ANTHROPIC_API_KEY must be set in shell environment"`.

---

## Principle of least privilege

The minimum permission set for task-api development:

1. **Read everything in the project.** Claude needs to read code to help with it.
2. **Run build and tests.** Claude needs feedback on whether changes work.
3. **Read git state.** Claude needs status and diff to understand what changed.
4. **Nothing else without asking.** Commits, pushes, file deletions — always prompt.

Everything not in allow or deny triggers a prompt. The prompt workflow:

| Prompt response | Effect |
|----------------|--------|
| Yes, once | Allows this specific invocation |
| Yes, always allow | Adds to allow in settings.local.json |
| No | Denies this invocation |
| Always deny | Adds to deny in settings.local.json |

"Yes, always allow" is a settings.local.json write. Review what you're allowing before saying yes. The `/fewer-permission-prompts` skill can analyze your session transcripts and suggest rules to add — use it after several sessions to tune the allow list efficiently.

---

## User vs project settings: which file wins

| Situation | File | Notes |
|-----------|------|-------|
| Team must block git push | `.claude/settings.json` (committed) | Applies to everyone |
| Personal dev shortcuts | `~/.claude/settings.json` | Only your machine |
| Local tokens or secrets | `.claude/settings.local.json` | Gitignored |
| Override a project deny for your machine | `.claude/settings.local.json` | Be deliberate — document why |

If project settings deny git push but you need to allow it on your machine for a specific reason, add the allow to settings.local.json. The local file wins. Note why in CLAUDE.local.md.

---

## Adding permissions without editing JSON manually

Using the `update-config` skill:
```
/update-config Allow "Bash(go test ./...)" to run without prompting for this project.
```

Or describe it naturally:
```
Allow go test and go build to run without permission prompts for task-api.
```

Claude edits `.claude/settings.json` with the correct structure. Review the diff before accepting.

To see current merged permissions:
```
/config
```

To audit permission prompts from past sessions and generate allow rules:
```
/fewer-permission-prompts
```

---

## Verification

After writing settings.json, verify it works as intended:

1. Run `go build ./...` — should run without a permission prompt.
2. Run `go test ./...` — should run without a permission prompt.
3. Ask Claude to run `git push` — should be denied without prompting.
4. Ask Claude to read `.env` — should be denied.
5. Ask Claude to run `rm -rf ./tmp` — should be denied.

If a denied operation prompts instead of denying silently, check the deny rule syntax. The pattern must match exactly.

---

## Checklist

- [ ] `.claude/settings.json` exists in the project root.
- [ ] Allow list covers daily workflow: build, test, vet, fmt, git read commands.
- [ ] Deny list covers irreversible operations: git push, rm -rf, secret files.
- [ ] No secrets or personal tokens in `.claude/settings.json`.
- [ ] `.claude/settings.local.json` is in `.gitignore`.
- [ ] Verified: go build and go test run without prompts.
- [ ] Verified: git push is denied.
- [ ] Verified: .env reading is denied.
- [ ] `defaultMode` is set to "default" unless there is a reason to change it.
