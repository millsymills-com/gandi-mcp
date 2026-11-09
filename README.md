<p align="center">
  <img src="docs/assets/logo.svg" alt="gandi-mcp logo" width="160">
</p>

# gandi-mcp

Production-grade Python MCP server for the [Gandi v5 API](https://api.gandi.net/docs/reference/).

## Status

**Stage: S3** (Complete). Under active development. See [CLAUDE.md](CLAUDE.md) for the architectural overview.

## Features

- **187 MCP tools** (79 read / 92 write / 16 purchase) covering Gandi Domains, LiveDNS, linked zones, DNS templates, Email, mailboxes, Simple Hosting, Certificates, comments, Billing, and Organization — full catalogue in [docs/tool-schema-matrix.md](docs/tool-schema-matrix.md)
- **Three-tier safety model**: readonly (default) → readwrite → readwrite + purchases, gated at both tool-visibility and handler-runtime layers
- **No-purchasing mode**: tools that spend money (domain registration, renewal, transfer-in, cert issuance, mailbox slots) are hidden by default even in readwrite mode
- **Bearer auth** with optional `sharing_id` scoping for reseller / multi-org accounts
- **Typed, linted, tested**: strict ty, ruff, pytest, bandit

## Quick Start

```bash
# Install from source
git clone https://github.com/millsymills-com/gandi-mcp.git
cd gandi-mcp
uv sync --extra dev

# Configure
cp .env.example .env
# Edit .env: set GANDI_TOKEN at minimum

# Run
uv run gandi-mcp
```

### Global install (system-wide CLI)

To install `gandi-mcp` as a global binary on `PATH` (useful when wiring it into Claude Code without a per-project checkout):

```bash
# From the cloned repo
uv tool install /absolute/path/to/gandi-mcp

# Refresh after pulling new commits
uv tool upgrade --reinstall gandi-mcp

# Verify it's on PATH (the entry point starts the stdio server; Ctrl-C to stop)
command -v gandi-mcp
```

## Configuration

See [.env.example](.env.example) for every option.

| Variable | Default | Description |
|---|---|---|
| `GANDI_TOKEN` | - | **Required.** Personal Access Token from https://admin.gandi.net/ |
| `GANDI_SHARING_ID` | - | Optional organization UUID to scope all requests to |
| `GANDI_STARTUP_PROBE` | `user_info` | Startup read: `user_info` or opt-in `livedns` |
| `GANDI_MODE` | `readonly` | `readonly` hides all write tools; `readwrite` exposes them |
| `GANDI_ALLOW_PURCHASES` | `false` | When `true` AND `GANDI_MODE=readwrite`, exposes tools that spend money |
| `GANDI_API_BASE_URL` | `https://api.gandi.net` | Override only for testing |
| `GANDI_REQUEST_TIMEOUT` | `30` | Request timeout in seconds |
| `GANDI_MAX_RETRIES` | `3` | Total request attempts including the first (1 = no retry) |

## Safety model

Three tiers, two orthogonal gates:

| Mode | Purchases | Tools visible |
|---|---|---|
| `readonly` (default) | n/a | Read tools only |
| `readwrite` | `false` (default) | Read + non-purchasing writes (DNS records, contacts, mailbox edits, cert revoke, `gandi_domain_delete`, …) |
| `readwrite` | `true` | Everything including `gandi_domain_register`, `gandi_domain_renew`, `gandi_domain_transfer_in`, `gandi_email_create_mailbox`, `gandi_email_create_slot`, `gandi_email_renew_mailbox`, `gandi_cert_issue`, `gandi_cert_renew` |

Defense-in-depth: every write tool *also* checks the mode at handler time, and every purchase tool *also* checks the purchase flag, so a stale tool list cached by an MCP client can't slip a write through.

## Codex and Claude Code integration

Use the local stdio transport. Install and review the checkout first, then run
`uv sync --frozen` there. Replace the absolute paths below with your checkout and
`uv` executable (`command -v uv`). These examples pin readonly mode and keep
purchases disabled. They explicitly select `user_info`; for a LiveDNS-scoped PAT,
change `GANDI_STARTUP_PROBE` to `livedns` in the chosen client configuration
before connecting. Keep your PAT in the launching process's environment or the
checkout's ignored `.env`; never commit real credentials to client configuration.

### Claude Code

Register a server for the current project in local scope:

```bash
claude mcp add --env GANDI_MODE=readonly GANDI_ALLOW_PURCHASES=false GANDI_STARTUP_PROBE=user_info --transport stdio --scope local gandi -- /absolute/path/to/uv --directory /absolute/path/to/gandi-mcp run --frozen gandi-mcp
```

`--scope user` makes the server available across projects. `--scope project`
writes a shared `.mcp.json` at the project root. Interactive terminal sessions
prompt for approval of project servers; noninteractive, SDK, and cloud sessions
can load them without that prompt. Review the configuration before launching
those sessions. `.claude/settings.json` is not the project MCP server
configuration file.
For a shared configuration, use environment references rather than literal PATs:

```json
{
  "mcpServers": {
    "gandi": {
      "type": "stdio",
      "command": "/absolute/path/to/uv",
      "args": ["--directory", "/absolute/path/to/gandi-mcp", "run", "--frozen", "gandi-mcp"],
      "env": {
        "GANDI_TOKEN": "${GANDI_TOKEN}",
        "GANDI_MODE": "readonly",
        "GANDI_ALLOW_PURCHASES": "false",
        "GANDI_STARTUP_PROBE": "user_info"
      }
    }
  }
}
```

Export `GANDI_TOKEN` before starting Claude Code when using this JSON form.
The registration command stores only the non-secret safety flags and probe choice; the PAT
is inherited from the launching shell or read from the checkout's ignored `.env`.
Inspect connection status with `claude mcp get gandi` and `/mcp`.

### Codex CLI / IDE

Add this table to `~/.codex/config.toml`, or `.codex/config.toml` in a trusted
project. Export the token before launching Codex; `env_vars` forwards it without
storing it in the TOML file.

```toml
[mcp_servers.gandi]
command = "/absolute/path/to/uv"
args = ["--directory", "/absolute/path/to/gandi-mcp", "run", "--frozen", "gandi-mcp"]
env_vars = ["GANDI_TOKEN", "GANDI_SHARING_ID"]

[mcp_servers.gandi.env]
GANDI_MODE = "readonly"
GANDI_ALLOW_PURCHASES = "false"
GANDI_STARTUP_PROBE = "user_info"
```

Inspect registration with `codex mcp get gandi`, then check connection and tool
availability with `/mcp` inside Codex. Registration alone does not test a server.

### Verification and limits

Confirm that initialization succeeds, read tools are listed, and write/purchase
tools are absent. Startup itself performs the selected authenticated read:

| `GANDI_STARTUP_PROBE` | Startup read | Optional separately authorized tool-call check |
|---|---|---|
| `user_info` (default) | `GET /v5/organization/user-info` | `gandi_org_get_user_info` |
| `livedns` | `GET /v5/livedns/domains?page=1&per_page=1` | `gandi_livedns_list_domains` |

Both modes apply the configured `GANDI_SHARING_ID`. Do not call the user-info
tool to verify a LiveDNS-only PAT, broaden its permissions, or switch probe modes
after a denial. The optional LiveDNS tool call returns the API's default page;
it does not use the startup probe's one-item limit. Authorize any additional live
read separately and inspect account/domain results privately. Initialization and
tool discovery alone do not establish a successful tool-call round trip.

Missing or rejected credentials can produce a healthy MCP connection with an
empty tool list; that is not a successful authenticated integration test. A
successful selected read establishes only its own access, not every product scope.

Configuration guidance was checked against [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp)
and [OpenAI MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
on 2026-11-05. Client runtime tests and live API tests must be recorded separately;
these examples do not assert compatibility with every client or protocol revision.

## Limitations

Gaps in Gandi's v5 REST API that this server cannot work around. Each requires manual action in the Gandi web UI:

- **Registrar transfer-lock toggle.** v5 reports `clientTransferProhibited` in `gandi_domain_get_domain` / `gandi_domain_get_status` responses but exposes no PATCH/PUT endpoint to set it. Unlock from `Domains → <domain> → Transfer lock` before initiating a registrar transfer-out.
- **Email subscription cancellation.** `gandi_email_refund_slot` only refunds an unused slot within the refund window. There is no v5 endpoint to stop a recurring email subscription. Cancel from `Billing → Subscriptions`.
- **Outbound transfer status / approval.** v5 does not surface outbound-transfer state. Gandi sends an FOA email; approve there.

## Development

```bash
# Lint and format
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Type check
uv run ty check src/gandi_mcp/

# Unit tests
uv run pytest tests/unit/ -v

# Full suite with coverage (matches CI gate: >=85% total, >=70% tools/*.py, >=90% core)
uv run pytest -m "not live" --cov=gandi_mcp --cov-report=term-missing --cov-report=json
uv run python scripts/check_coverage_thresholds.py

# Pre-commit hooks
uv run pre-commit install
```

## License

Apache-2.0. See [LICENSE](LICENSE).

### Startup authentication troubleshooting

By default, startup probes `GET /v5/organization/user-info`. A successful probe verifies
access to that endpoint, not permission for every product operation. All tools
remain disabled if the probe fails, including for HTTP 401 or 403. Startup
diagnostics retain a failure hint, exception type and available HTTP status;
they do not include upstream response bodies or exception text.

Gandi [PATs](https://docs.gandi.net/en/managing_an_organization/organizations/personal_access_token.html)
can restrict organizations and products. Its [bearer authentication](https://api.gandi.net/docs/organization/)
also uses 403 for expired or nonexistent tokens, so 403 alone does not prove
that a PAT is valid or merely lacks scope. Check the existing token's validity,
expiration and intended resource permissions in Gandi. Do not broaden permissions
or regenerate a token solely to satisfy this probe. For a PAT intended for LiveDNS, explicitly set
`GANDI_STARTUP_PROBE=livedns` to probe the documented
[`GET /v5/livedns/domains`](https://api.gandi.net/docs/livedns/) operation instead,
with `page=1`, `per_page=1` and the configured `GANDI_SHARING_ID`. An empty
HTTP 200 array is a successful read, not proof that a particular domain exists.
This choice does not grant permissions, change write/purchase gates, or validate
other product scopes. Other tools may still return permission errors.
The server never tries a different endpoint after failure or treats 403 as success.
This opt-in path has synthetic test coverage; a scoped live PAT has not been tested.
