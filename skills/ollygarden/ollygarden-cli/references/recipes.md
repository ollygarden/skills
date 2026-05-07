# `ollygarden` Recipes

Compound workflows that combine multiple commands. For single-command
help, see [commands.md](commands.md).

## Table of Contents

- [Search a service then fetch its active insights](#search-a-service-then-fetch-its-active-insights)
- [Triage critical insights org-wide](#triage-critical-insights-org-wide)
- [Paginate through every page of a list](#paginate-through-every-page-of-a-list)
- [Debug a webhook that isn't firing](#debug-a-webhook-that-isnt-firing)
- [Promote a webhook config across environments](#promote-a-webhook-config-across-environments)
- [Diff active insights between two services](#diff-active-insights-between-two-services)
- [Useful jq one-liners](#useful-jq-one-liners)
- [Scripting with exit codes](#scripting-with-exit-codes)
- [Running against multiple orgs in one script](#running-against-multiple-orgs-in-one-script)

## Search a service then fetch its active insights

```bash
SVC_ID=$(ollygarden services search "$1" --json \
  | jq -r '.data | sort_by(.last_seen_at) | reverse | .[0].id')

[ -z "$SVC_ID" ] && { echo "no match" >&2; exit 4; }

ollygarden services insights "$SVC_ID" --status active --json \
  | jq -r '.data[] | [.insight_type.impact, .insight_type.display_name, .id] | @tsv'
```

Picks the most recently seen match — useful when many envs report the
same service name.

## Triage critical insights org-wide

`insights list` does **not** echo a `meta.total` — paginate or count
client-side. Service info is flat on each item: `service_name`,
`service_id`, `service_version`, `service_environment`.

```bash
# Top 20 by detection time, with service name
ollygarden insights list --status active --impact Critical --limit 20 --json \
  | jq -r '.data[] | [.detected_ts, .service_name, .insight_type.display_name] | @tsv' \
  | column -t -s$'\t'

# Count: walk pages until has_more is false
total=0; offset=0
while :; do
  page=$(ollygarden insights list --status active --impact Critical --limit 100 --offset "$offset" --json)
  rows=$(echo "$page" | jq '.data | length')
  total=$((total + rows))
  [ "$(echo "$page" | jq -r '.meta.has_more')" = "true" ] || break
  offset=$((offset + rows))
done
echo "$total critical insights"
```

## Paginate through every page of a list

`list` commands cap `--limit` at 100. Walk via `meta.has_more`:

```bash
offset=0
while :; do
  page=$(ollygarden insights list --status active --limit 100 --offset "$offset" --json)
  echo "$page" | jq -r '.data[] | .id'
  [ "$(echo "$page" | jq -r '.meta.has_more')" = "true" ] || break
  offset=$((offset + $(echo "$page" | jq '.data | length')))
done
```

`meta.has_more` is the canonical end-of-stream indicator. `meta.total`
is present on `services search`, `webhooks list`, and `webhooks
deliveries list` — but **not** on `insights list`.

For very large datasets, prefer narrowing with `--service-id`,
`--signal-type`, `--date-from` over walking the whole org.

## Debug a webhook that isn't firing

```bash
WH=$1   # webhook id

# 1. Confirm config
ollygarden webhooks get "$WH"

# 2. Send a synthetic delivery
ollygarden webhooks test "$WH"

# 3. Walk recent deliveries, show only the failures
ollygarden webhooks deliveries list "$WH" --json \
  | jq -r '.data[] | select(.status != "success")
                   | [.id, .status, .http_status_code, .created_at, .error_message] | @tsv'

# 4. Read the full record for one failure
ollygarden webhooks deliveries get "$WH" <delivery-id>
```

Delivery items expose `status` (`success`/`failure`/etc.),
`http_status_code` (nullable on TLS/network failures), `attempt_number`,
`error_message`, `created_at`, and `completed_at`. Common causes a
failed record reveals: TLS errors (null `http_status_code` + populated
`error_message`), 4xx from the receiver (signature mismatch, bad path),
or timeouts (slow endpoint, large `completed_at - created_at` delta).

## Promote a webhook config across environments

```bash
# Capture the prod config
ollygarden --context prod webhooks list --json \
  | jq '.data[] | select(.name=="alerts-prod")' > /tmp/wh.json

# Recreate it in staging
ollygarden --context staging webhooks create \
  --name "$(jq -r .name /tmp/wh.json)" \
  --url "$(jq -r .url /tmp/wh.json | sed 's/prod/staging/')" \
  --min-severity "$(jq -r .min_severity /tmp/wh.json)" \
  --enabled
```

The CLI doesn't ship a native `clone`; `jq` + flags is the idiom.

## Diff active insights between two services

When `services` is a stable service ID (one specific version):

```bash
extract() {
  ollygarden services insights "$1" --status active --json \
    | jq -r '.data[].insight_type.display_name' | sort -u
}

diff <(extract "$SVC_A") <(extract "$SVC_B")
```

When you want to diff by service **name** across all of its versions
(typical when the same service has many version rows in `services
list`), filter `insights list` instead — `service_name` is flat on each
item:

```bash
extract_by_name() {
  ollygarden insights list --status active --limit 100 --json \
    | jq -r --arg svc "$1" '.data[] | select(.service_name == $svc) | .insight_type.display_name' \
    | sort -u
}

diff <(extract_by_name nameplate) <(extract_by_name dibber)
```

Lines prefixed `<` are only on the first service, `>` only on the second.

## Useful jq one-liners

```bash
# Just the IDs from any list command
| jq -r '.data[].id'

# Count by impact
| jq '.data | group_by(.insight_type.impact)
            | map({impact: .[0].insight_type.impact, count: length})'

# CSV row per insight (id, service, impact, detected)
| jq -r '.data[] | [.id, .service_name, .insight_type.impact, .detected_ts] | @csv'

# Pull pagination meta to drive a loop (has_more is universal; total only on
# services search, webhooks list, webhooks deliveries list)
| jq '.meta | {has_more, total, timestamp}'
```

## Scripting with exit codes

The CLI uses HTTP-aligned exit codes. Branch on them rather than parsing
stderr:

```bash
if ollygarden services get "$ID" >/tmp/svc.json 2>/dev/null; then
  jq . /tmp/svc.json
else
  case $? in
    3) echo "auth error — run: ollygarden auth login" >&2 ;;
    4) echo "service $ID not found in active org" >&2 ;;
    5) echo "rate limited — backing off 30s" >&2; sleep 30 ;;
    6) echo "server error — retry later" >&2 ;;
    *) echo "unexpected failure" >&2 ;;
  esac
  exit 1
fi
```

Pair with `-q` when you only care about the exit code (e.g. health checks):

```bash
ollygarden auth status -q --no-probe || ollygarden auth login
```

## Running against multiple orgs in one script

```bash
for ctx in $(ollygarden auth list-contexts --json | jq -r '.data[].name'); do
  echo "=== $ctx ==="
  ollygarden --context "$ctx" insights list --status active --impact Critical --limit 100 --json \
    | jq -r '"\(.data | length) critical insights on this page (has_more=\(.meta.has_more))"'
done
```

Don't `auth use-context` mid-script — the per-invocation `--context` flag
keeps each org's call hermetic and avoids mutating the user's saved
state.
