# MCP configuration

MCP (Model Context Protocol) servers extend Claude with tools beyond its built-in capabilities. File access outside the project root, live documentation lookup, database queries, web browsing — these all come through MCP servers. Configuration is per-project in `.mcp.json` or per-user in `~/.claude.json`.

---

## .mcp.json structure

Project-scoped MCP servers live in `.mcp.json` at the project root. Commit this file to share server configuration with the team.

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "description": "Current documentation for libraries and frameworks"
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/you/Documents/references"
      ],
      "description": "Read access to reference documents outside project root"
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "./dev.db"],
      "description": "Read-only access to local dev SQLite database"
    }
  }
}
```

Each entry:
- Key: the server name (used in tool routing)
- `command`: the executable to run (usually `npx` or a local binary)
- `args`: arguments passed to the command
- `description`: human-readable note on what this server provides (not functional, documentation only)

---

## Adding a new MCP server: step-by-step

**Step 1: Find the server package.**

Most MCP servers are npm packages. The official list is at `modelcontextprotocol.io`. Check the package's README for the correct `command` and `args`.

**Step 2: Add the entry to `.mcp.json`.**

```json
{
  "mcpServers": {
    "new-server": {
      "command": "npx",
      "args": ["-y", "@vendor/mcp-server-name@latest"]
    }
  }
}
```

**Step 3: Restart the Claude Code session.**

MCP servers are initialized at session start. Changes to `.mcp.json` require a session restart to take effect. Close and reopen Claude Code.

**Step 4: Respond to the trust dialog.**

On first use of a project `.mcp.json`, Claude Code presents a trust dialog listing the servers and their permissions. Review it before accepting. You are granting the server access to your system at the level of its permissions.

**Step 5: Verify with `/mcp`.**

Run `/mcp` in Claude Code. The new server should appear in the list with status "connected". If it shows as errored, check the command and args in `.mcp.json`.

**Step 6: Smoke test.**

Send a message that requires a tool only this server exposes. If it responds correctly, the server is working.

---

## Common MCP servers reference

| Server | npm package | Use case | Security note |
|--------|------------|---------|--------------|
| context7 | `@upstash/context7-mcp` | Live library and framework docs | Network access — reads public docs |
| filesystem | `@modelcontextprotocol/server-filesystem` | Files outside project root | Scope paths tightly |
| sqlite | `@modelcontextprotocol/server-sqlite` | Local SQLite database queries | Use read-only mode for dev |
| postgres | `@modelcontextprotocol/server-postgres` | PostgreSQL queries | Use read-only credentials |
| github | `@modelcontextprotocol/server-github` | GitHub issues, PRs, repos | Requires GitHub token |
| fetch | `@modelcontextprotocol/server-fetch` | Fetch web content | Network access |
| puppeteer | `@modelcontextprotocol/server-puppeteer` | Browser automation | Full browser access |

For task-api development: context7 is useful for Go stdlib documentation when working with unfamiliar packages. Filesystem is useful if you keep reference documents in a separate directory.

---

## User-level vs project-level MCP

| Location | Scope | Use case |
|----------|-------|---------|
| `.mcp.json` in project | This project only | Project-specific servers (sqlite for this DB, github for this repo) |
| `~/.claude.json` | All projects on this machine | Personal tools you use everywhere (notes, personal filesystem) |

Add to `~/.claude.json` via `/mcp` in Claude Code UI, not by editing the file directly. The format is different from `.mcp.json` and managed by Claude Code.

For team tools: `.mcp.json` in the project, committed to git. Everyone on the team gets the same servers.

For personal tools: `~/.claude.json`, managed through the UI. Not committed.

---

## Security principles for MCP

**Principle 1: Scope filesystem paths as narrowly as possible.**

Wrong:
```json
"args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/you"]
```

This gives the server access to your entire home directory.

Right:
```json
"args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/you/Documents/task-api-references"]
```

This gives the server access only to the reference documents directory.

**Principle 2: Use read-only credentials for database servers.**

If you add a database MCP server, create a read-only database user for development. Never use admin or write credentials in an MCP server configuration.

**Principle 3: Review project .mcp.json before accepting the trust dialog.**

When you open a project with a `.mcp.json` you didn't write — a cloned repo, a colleague's project — read the file before clicking trust. Each server gets the permissions listed in its implementation.

**Principle 4: Network-accessing servers make network requests.**

context7, fetch, and github servers make outbound network requests. In air-gapped environments or when working with sensitive code, be aware that server interactions may send data to external services.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Server not in `/mcp` list after adding to .mcp.json | Session not restarted | Close and reopen Claude Code |
| Server shows as errored | Wrong command or args | Check npm package name and version, test `npx -y @package/name` manually |
| Tool not available in Claude | Trust dialog not accepted | Run `/mcp` and check server status, re-accept trust |
| Server connects but tools don't work | Missing authentication | Check server README for required environment variables (tokens, API keys) |
| filesystem server can't read a path | Path not in args list | Add path to args in .mcp.json, restart |
| npx hangs on first run | Package download slow | Wait — `npx -y` downloads the package on first run |

**Verifying a server is connected:**

```
/mcp
```

Expected output for a connected server:
```
context7: connected (5 tools)
  - resolve-library-id
  - get-library-docs
  [...]
```

If the server shows connected but a specific tool fails, the issue is in the tool's implementation or its permissions.

---

## .mcp.json for task-api

Minimal configuration for task-api development:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "description": "Go stdlib and library documentation"
    }
  }
}
```

context7 is useful when working with Go packages you don't know well (`net/http`, `encoding/json`, `sync`). Instead of Claude generating plausible-but-possibly-wrong API calls, context7 pulls current documentation.

Use in a prompt:
```
Use context7 to look up the correct signature for http.NewServeMux() in Go 1.22.
```

---

## Checklist

- [ ] `.mcp.json` exists if the project uses any MCP servers.
- [ ] Filesystem paths in MCP args are scoped to minimum necessary directories.
- [ ] Database MCP servers use read-only credentials.
- [ ] Trust dialog reviewed before accepting for unfamiliar projects.
- [ ] `/mcp` shows servers as connected after session restart.
- [ ] Smoke test confirms tools work as expected.
- [ ] Authentication tokens for MCP servers are in environment variables, not in .mcp.json.
- [ ] `.mcp.json` is committed to git for team-shared servers.
