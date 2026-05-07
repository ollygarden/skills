# `ollygarden` Command Reference

Complete surface area of the `ollygarden` CLI. Every command supports the
[global flags](#global-flags). All `list` commands paginate via
`--limit` / `--offset`.

## Table of Contents

- [Global flags](#global-flags)
- [JSON envelope](#json-envelope)
- [`auth`](#auth) — login, logout, status, list-contexts, use-context
- [`analytics`](#analytics) — services
- [`insights`](#insights) — list, get, summary
- [`organization`](#organization)
- [`services`](#services) — list, get, search, grouped, insights, versions
- [`webhooks`](#webhooks) — list, get, create, update, delete, test, deliveries

## Global flags

Available on every command:

| Flag | Description |
|---|---|
| `--api-url <url>` | Override base URL (default `https://api.ollygarden.cloud`). Env: `OLLYGARDEN_API_URL`. |
| `--context <name>` | Use a saved auth context for this invocation only. Env: `OLLYGARDEN_CONTEXT`. |
| `--json` | Emit the full API response envelope to stdout. No transformation. |
| `-q`, `--quiet` | Suppress non-essential output. Errors still print to stderr. |
| `-h`, `--help` | Per-command help. Authoritative source for new flags. |

`OLLYGARDEN_API_KEY` (env var) overrides any saved context.

## JSON envelope

When you pass `--json`, the CLI prints the full API envelope:

```json
{
  "data":  [ /* … */ ],
  "meta":  { "total": 123, "limit": 50, "offset": 0 },
  "links": { "next": "…", "prev": "…" }
}
```

For `get`-style commands `data` is a single object, not an array. Errors
go to stderr as `{"error": …, "meta": …}` and the process exits non-zero.

---

## `auth`

Manage credentials stored on disk. Config lives at
`os.UserConfigDir()/ollygarden/config.yaml` (mode `0600`); override with
`OLLYGARDEN_CONFIG`.

### `auth login [flags]`

Save an API key to a named context. Token sources, in priority order:
`--token-file PATH`, then stdin (when piped), then interactive TTY prompt.
The token is validated before being written.

| Flag | Description |
|---|---|
| `--token-file <path>` | Read the token from a file. |
| `--no-activate` | Save the context without setting it as `current-context`. |
| `--context <name>` (global) | Save under this context name (default `default`). |

```bash
ollygarden auth login --context prod
echo "$OG_TOKEN" | ollygarden auth login --context ci --no-activate
```

### `auth status [flags]`

Print the active credential's source, URL, and a masked key. By default
makes one `GET /api/v1/organization` call to confirm the token still works.

| Flag | Description |
|---|---|
| `--no-probe` | Skip the network call, do an offline check only. |

Exit codes: `0` logged in (and probe succeeded), `3` no credential or
`401`.

### `auth list-contexts`

Print every saved context name. No keys are shown.

### `auth use-context <name>`

Set `current-context` to a saved context.

### `auth logout [flags]`

Remove credentials.

| Flag | Description |
|---|---|
| `--context <name>` | Remove a specific context. |
| `--all` | Remove every context. Requires `--confirm` in non-TTY mode. |
| `--confirm` | Bypass confirmation prompt. |

When the last context is removed, the config file is deleted.

---

## `analytics`

### `analytics services [flags]`

Per-service analytics roll-up.

| Flag | Description |
|---|---|
| `--limit <n>` | 1-100, default 50. |

```bash
ollygarden analytics services --json | jq '.data[] | {name, signal_volume_24h}'
```

---

## `insights`

### `insights list [flags]`

List insights across all services in the active org.

| Flag | Description |
|---|---|
| `--status <list>` | Comma-separated: `active`, `archived`, `muted`. |
| `--impact <list>` | Comma-separated: `Critical`, `Important`, `Normal`, `Low`. **Case-sensitive.** |
| `--service-id <uuid>` | Restrict to one service. |
| `--signal-type <type>` | `trace`, `metric`, or `log`. |
| `--date-from <rfc3339>` | Lower bound on `detected_ts`. |
| `--date-to <rfc3339>` | Upper bound on `detected_ts`. |
| `--sort <field>` | Prefix `+`/`-` for asc/desc. Fields: `detected_ts`, `created_at`, `updated_at`, `impact`, `signal_type`. Default `-detected_ts`. |
| `--limit <n>` | 1-100, default 20. |
| `--offset <n>` | ≥ 0. |

```bash
ollygarden insights list --status active --impact Critical,Important --limit 100
```

### `insights get <insight-id>`

Show full details for a single insight, including `attributes` and
`remediation_instructions`.

### `insights summary <insight-id>`

Print the AI-generated summary of one insight. Useful as a one-shot
explainer before deciding whether to remediate.

---

## `organization`

### `organization [flags]`

Single-endpoint command (no `get` verb). Shows the active org's tier,
features, and overall instrumentation score.

```bash
ollygarden organization --json | jq '{name, tier, score}'
```

Use this as a quick "which org am I authed against" check.

---

## `services`

### `services list [flags]`

All services in the active org.

| Flag | Description |
|---|---|
| `--limit <n>` | 1-100, default 50. |
| `--offset <n>` | ≥ 0. |

### `services get <service-id>`

Full details for one service.

### `services search [query] [flags]`

Free-text search. The query is positional **or** `--query`.

| Flag | Description |
|---|---|
| `--query <text>` | Search text (alternative to positional arg). |
| `--environment <env>` | Filter by environment. |
| `--namespace <ns>` | Filter by namespace. |
| `--limit <n>` | 1-100, default 20. |
| `--offset <n>` | ≥ 0. |

```bash
ollygarden services search "checkout" --environment production
```

### `services grouped [flags]`

Services grouped by name. Most useful for orgs that run the same service
across many environments/versions.

| Flag | Description |
|---|---|
| `--sort <order>` | `insights-first` (default), `name-asc`, `name-desc`, `created-asc`, `created-desc`. |
| `--limit <n>` | 1-100, default 50. |
| `--offset <n>` | ≥ 0. |

### `services insights <service-id> [flags]`

Insights filtered to one service.

| Flag | Description |
|---|---|
| `--status <list>` | Comma-separated: `active`, `archived`, `muted`. Default `active`. |
| `--limit <n>` | 1-100, default 50. |
| `--offset <n>` | ≥ 0. |

### `services versions <service-id> [flags]`

Related versions of a service (e.g. canary vs stable rollout).

| Flag | Description |
|---|---|
| `--limit <n>` | 1-50, default 20. |

---

## `webhooks`

### `webhooks list [flags]`

| Flag | Description |
|---|---|
| `--limit <n>` | 1-100, default 50. |
| `--offset <n>` | ≥ 0. |

### `webhooks get <webhook-id>`

Full details for one webhook.

### `webhooks create [flags]`

| Flag | Description |
|---|---|
| `--name <string>` | **Required.** |
| `--url <https-url>` | **Required.** Must be HTTPS. |
| `--min-severity <level>` | `Low`, `Normal`, `Important`, `Critical`. Default `Low`. |
| `--event-type <id>` | Insight type ID. Repeatable. |
| `--environment <env>` | Repeatable. |
| `--enabled` | Enable on create (default off). |

```bash
ollygarden webhooks create \
  --name alerts-prod \
  --url https://hooks.example.com/og \
  --min-severity Important \
  --event-type cardinality.high \
  --environment production \
  --enabled
```

### `webhooks update <webhook-id> [flags]`

Same flags as `create` but all are optional. `--enabled` toggles state.

### `webhooks delete <webhook-id> [flags]`

| Flag | Description |
|---|---|
| `--confirm` | Skip the interactive confirmation. |

### `webhooks test <webhook-id>`

Send a synthetic delivery to the configured URL. Inspect what happened
with `webhooks deliveries list <id>` afterwards.

### `webhooks deliveries list <webhook-id> [flags]`

| Flag | Description |
|---|---|
| `--limit <n>` | 1-100, default 50. |
| `--offset <n>` | ≥ 0. |

### `webhooks deliveries get <webhook-id> <delivery-id>`

Full delivery record: status code, response body, retry count, latency.
The thing to read when a webhook isn't reaching its endpoint.
