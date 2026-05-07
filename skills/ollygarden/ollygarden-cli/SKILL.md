---
name: ollygarden-cli
description: Use the `ollygarden` CLI to query OllyGarden services, insights, analytics, organizations, and webhooks from the terminal. Use when the user asks to run ollygarden commands, list services or insights, set up or debug webhooks, manage auth contexts (multiple orgs or environments), or pipe OllyGarden data through jq. Triggers on "ollygarden cli", "og cli", "list my services", "fetch insights from cli", "ollygarden auth", "create a webhook", "ollygarden context", "ollygarden --json".
license: Apache-2.0
compatibility: Requires the `ollygarden` CLI binary on PATH and a valid OllyGarden API token.
metadata:
  ollygarden-namespace: ollygarden
  source-repo: https://github.com/ollygarden/ollygarden-cli
---

# OllyGarden CLI

Use the `ollygarden` CLI as the primary way to talk to the OllyGarden API.
Prefer it over raw `curl` calls — it handles auth, multi-context config,
pagination, and exit codes for you.

This skill is for **read, inspect, and configure** workflows. To *apply*
fixes from insights, hand off to the `ollygarden-insight-remediation` skill.

## 1. Verify the CLI

Before running anything else, check the binary and the active credential.

```bash
ollygarden version          # confirms the binary is on PATH
ollygarden auth status      # validates the token via /organization (exit 3 = not logged in)
```

If `auth status` exits non-zero, go to section 2. If `ollygarden` itself is
missing, install it:

```bash
curl -fsSL https://raw.githubusercontent.com/ollygarden/ollygarden-cli/main/install.sh | sh
```

## 2. Auth & contexts

Tokens live in a YAML config at `os.UserConfigDir()/ollygarden/config.yaml`
(mode `0600`). Multiple **contexts** coexist for different orgs or
environments (prod, internal, staging).

```bash
# Interactive login (hidden prompt) — saves under context "default"
ollygarden auth login

# Pipe a token from an env var or secret store
echo "$OLLYGARDEN_API_KEY" | ollygarden auth login --context prod

# Login pointed at a non-default API URL (e.g. internal env)
ollygarden auth login --context internal --api-url https://api.internal.ollygarden.cloud

# Switch the active context
ollygarden auth use-context prod
ollygarden auth list-contexts

# Per-invocation override without changing the active context
ollygarden --context internal services list
```

Get a token at <https://ollygarden.app/settings>.

**Precedence:** `OLLYGARDEN_API_KEY` env var beats saved contexts (so CI keeps
working). The `--context` flag beats `OLLYGARDEN_CONTEXT` beats the saved
`current-context`.

## 3. Mental model

Every command shares the same shape: `ollygarden <noun> <verb> [args] [flags]`.

**Global flags** that apply to every command:

| Flag | Purpose |
|---|---|
| `--api-url <url>` | Override base URL (or set `OLLYGARDEN_API_URL`) |
| `--context <name>` | Use a saved context for this invocation |
| `--json` | Print the full API envelope `{data, meta, links}` to stdout |
| `-q`, `--quiet` | Suppress non-essential output (success = exit 0, no stdout) |

**Pagination:** all `list` commands accept `--limit` (1-100, default 20-50)
and `--offset` (≥ 0). Default sort is most-recent-first where applicable.

**Output mode:** human-readable tables by default. Pass `--json` and pipe to
`jq` for programmatic use. **Always pass `--json` when scripting** — the
table format is for humans and may change.

**Exit codes:** `0` success, `1` general/network, `2` usage/validation,
`3` auth, `4` not found, `5` rate limited, `6` server. See
[references/recipes.md](references/recipes.md) for scripting patterns that
key off these.

## 4. Common tasks

The five things agents do most often. For anything beyond these, see
[references/commands.md](references/commands.md).

### List active critical insights across the org

```bash
ollygarden insights list --status active --impact Critical --limit 50
# scripted form:
ollygarden insights list --status active --impact Critical --json \
  | jq -r '.data[] | [.id, .insight_type.display_name, .detected_ts] | @tsv'
```

### Find a service by name and pull its insights

```bash
SVC_ID=$(ollygarden services search "checkout" --json \
  | jq -r '.data | sort_by(.last_seen_at) | reverse | .[0].id')

ollygarden services insights "$SVC_ID" --status active
```

`services search` covers free-text queries. Use `services grouped
--sort insights-first` to surface services with the most outstanding work.

### Read the AI-generated summary of a single insight

```bash
ollygarden insights summary <insight-id>
```

Use this before opening a remediation flow — it gives the agent a one-shot
explanation of what the insight means.

### Create and test a webhook

```bash
ollygarden webhooks create \
  --name alerts-prod \
  --url https://hooks.example.com/og \
  --min-severity Important \
  --enabled

# grab the new webhook id from the JSON envelope:
WH=$(ollygarden webhooks list --json | jq -r '.data[] | select(.name=="alerts-prod") | .id')

ollygarden webhooks test "$WH"
ollygarden webhooks deliveries list "$WH"   # debug what got sent
```

### Scope a one-off to a different org or environment

Don't `auth use-context`; just override per-invocation:

```bash
ollygarden --context internal services list
OLLYGARDEN_API_URL=https://api.staging.ollygarden.cloud ollygarden organization
```

## 5. Going further

- **Full per-command reference** (every flag, every arg, every example):
  [references/commands.md](references/commands.md). Read this when the user
  asks for a command or flag not covered above.
- **Compound recipes & jq pipelines** (multi-step workflows, scripting with
  exit codes, walking deliveries to debug a webhook):
  [references/recipes.md](references/recipes.md). Read this when the task
  requires more than one command.

For ad-hoc help on any command: `ollygarden <noun> <verb> --help`.

## 6. Troubleshooting

**`auth status` exits 3** — no credential or the token was rejected. Run
`ollygarden auth login` (or `--context <name>` if you use multiple contexts).

**Command exits 4 (not found)** — the resource ID is wrong or belongs to a
different org. Confirm the active context with `ollygarden auth status` and
check the ID by listing first.

**Command exits 2 (validation)** — flag value rejected client-side or by the
API. Re-read the command's `--help`; enum flags like `--impact`,
`--status`, `--signal-type`, `--min-severity` are case-sensitive.

**Command exits 5 (rate limited)** — back off. For batch work, lower
`--limit` and add a sleep between paginated calls.

**Token works in `auth status` but `services list` is empty** — you're
authenticated against a different org than expected. Run `ollygarden
organization` to confirm the active org's name and tier, or
`ollygarden auth list-contexts` to see what's saved.

**Need raw API access instead of the CLI** — see the
`ollygarden-insight-remediation` skill, which uses `curl` + `keys.json`
directly. That path is for codebase-level fixes; this CLI is the
recommended path for everything else.
