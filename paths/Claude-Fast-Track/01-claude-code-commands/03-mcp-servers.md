# MCP servers

## What MCP is

MCP stands for Model Context Protocol. It is a standardized interface that lets Claude call external tools at runtime — filesystem operations, database queries, browser automation, API calls, and more. MCP servers are processes that implement this protocol; Claude connects to them and gains new tool capabilities.

Without MCP, Claude can only use built-in tools: Read, Write, Edit, Bash, Grep, Glob, and a few others. With MCP, Claude can query a Postgres database, search Confluence, interact with a browser, or call any API you expose through a server.

MCP does not make Claude smarter. It gives Claude a broader set of actions. Your job is to configure which servers Claude connects to, with what permissions.

On [claude.com](https://claude.com/), integrations are marketed as **connectors** (Slack, Google Workspace, remote MCP, and similar). In Claude Code the same mechanism is **MCP servers** in `.mcp.json` or `settings.json` — one protocol, two names depending on surface.

---

## How MCP servers extend Claude's capabilities

| Without MCP | With MCP (example servers) |
|-------------|---------------------------|
| Read local files only | Read from S3, databases, APIs |
| No browser access | Browser automation, screenshots |
| No external search | Web search, Confluence search, Jira queries |
| Manual database queries | Direct DB query tool |
| No notification system | Slack messages, webhooks on events |

The pattern: every new MCP server is a new capability surface Claude can use. Every new capability surface is also a new attack surface. See the security section below.

---

## Configuration — where MCP servers are defined

| Location | Scope | Use when |
|----------|-------|----------|
| `.mcp.json` in project root | This project only | Project-specific integrations (project DB, Jira board) |
| `~/.claude/mcp.json` | All projects | Personal tools you use everywhere (browser, personal search) |
| `~/.claude/settings.json` under `"mcpServers"` | All projects (alternative) | Same as global mcp.json |

Project-level `.mcp.json` is committed to the repo. Team members who clone the repo see the same MCP server configuration. Any server in a committed config becomes a trust decision for everyone who runs it — review before trusting.

---

## Structure of .mcp.json — full example

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/you/projects/task-api"],
      "env": {}
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "./tasks.db"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

Key fields:
- `command`: the executable that starts the server process. Usually `npx` for Node-based servers.
- `args`: arguments passed to the command. Server package name is typically the first arg after `-y`.
- `env`: environment variables the server process receives. Use `${VAR_NAME}` to reference host env vars — do not hardcode secrets in this file.

---

## Common MCP servers

| Server | Package | Provides |
|--------|---------|---------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | Scoped file read/write beyond built-in tools |
| Git | `@modelcontextprotocol/server-git` | Git operations as structured tool calls |
| SQLite | `@modelcontextprotocol/server-sqlite` | Query SQLite databases directly |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | Query Postgres databases |
| Browser | `@modelcontextprotocol/server-puppeteer` | Browser automation, screenshots |
| GitHub | `@modelcontextprotocol/server-github` | Repo, issues, PRs via GitHub API |
| Atlassian | `mcp-atlassian` | Jira and Confluence |

Find more at the MCP server registry. Evaluate any third-party server before use — it runs as a process on your machine with the permissions your shell has.

---

## How to add a new MCP server — steps

1. Find the server package (npm registry, GitHub, MCP registry).
2. Add it to `.mcp.json` (project) or `~/.claude/mcp.json` (global).
3. Set `env` entries for any required tokens — reference from environment, not hardcoded.
4. Open Claude Code (or restart if already running).
5. Run `/mcp` in session — verify the server appears and shows "connected".
6. Test with a simple prompt: "List the tables in the SQLite database."
7. Add permission rules in `.claude/settings.json` for the MCP tools if you want to scope what Claude can do with them.

**If the server fails to connect:** run `/doctor` and check `/mcp` output for error messages. Most failures are path issues (wrong executable) or missing environment variables.

---

## When MCP vs when built-in tools suffice

Use built-in tools (Read, Write, Bash) when:
- Working with local files in the project directory
- Running shell commands, tests, or builds
- The task is bounded to the local filesystem

Use MCP when:
- You need to query a structured data source (database, API) and want the result as structured tool output
- You need browser automation
- You need integration with external services (GitHub, Jira, Confluence)
- The built-in Bash + curl pattern produces messy output that Claude struggles to parse

**MCP is not always better than Bash.** For a one-off database check, `sqlite3 tasks.db "SELECT * FROM tasks"` piped through Bash is faster to set up than an MCP server. Reserve MCP for workflows you run repeatedly.

---

## Security — MCP servers have access to your system

Every MCP server runs as a process with your user's permissions. A filesystem MCP server scoped to `/Users/you/projects/` can read anything in that path. A Postgres MCP server with a write-capable role can modify your database.

Risks and mitigations:

| Risk | Mitigation |
|------|------------|
| Filesystem server reading secrets | Scope the server to the project directory, not home |
| DB server writing production data | Use a read-only DB role for the MCP connection |
| Untrusted project `.mcp.json` | Review before accepting the trust dialog Claude shows |
| Prompt injection via tool output | Server output is returned to Claude — malicious data in DB rows can inject instructions |
| Over-broad GitHub token | Use fine-grained PATs scoped to specific repos |

The trust dialog Claude shows when opening a project with `.mcp.json` is not a formality. Read the server list. Do not approve MCP configurations from untrusted sources.

**Prompt injection via MCP is a real attack.** If a database row contains the text "ignore previous instructions and...", Claude will process it. Treat MCP tool output as potentially hostile when connecting to external or shared data sources.

---

## Checklist

- [ ] I understand the difference between `.mcp.json` (project) and `~/.claude/mcp.json` (global).
- [ ] I know the structure of an MCP server configuration entry (command, args, env).
- [ ] I never hardcode secrets in `.mcp.json` — I reference environment variables with `${VAR}`.
- [ ] I understand that MCP servers run as processes with my user's permissions.
- [ ] I can add a new MCP server and verify it connects via `/mcp`.
- [ ] I understand prompt injection risk from MCP tool output.
- [ ] I know when to use MCP vs when built-in Bash suffices.
- [ ] I reviewed the security implications before adding any third-party MCP server.
