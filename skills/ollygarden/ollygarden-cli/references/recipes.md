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

```bash
# Just the count
ollygarden insights list --status active --impact Critical --json \
  | jq '.meta.total'

# Top 20 by detection time, with service name
ollygarden insights list --status active --impact Critical --limit 20 --json \
  | jq -r '.data[] | [.detected_ts, .service.name, .insight_type.display_name] | @tsv' \
  | column -t -s$'\t'
```

## Paginate through every page of a list

`list` commands cap `--limit` at 100. Walk the offset until `data` is
empty:

```bash
offset=0
while :; do
  page=$(ollygarden insights list --status active --limit 100 --offset "$offset" --json)
  rows=$(echo "$page" | jq '.data | length')
  [ "$rows" -eq 0 ] && break
  echo "$page" | jq -r '.data[] | .id'
  offset=$((offset + rows))
done
```

For very large pages, prefer narrowing with `--service-id`,
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
  | jq -r '.data[] | select(.status_code == null or .status_code >= 400)
                   | [.id, .status_code, .attempted_at] | @tsv'

# 4. Read the full record for one failure
ollygarden webhooks deliveries get "$WH" <delivery-id>
```

Common causes the delivery record reveals: TLS failures (no status_code),
4xx from the receiver (signature mismatch, bad path), or timeouts (slow
endpoint).

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

```bash
extract() {
  ollygarden services insights "$1" --status active --json \
    | jq -r '.data[].insight_type.id' | sort -u
}

diff <(extract "$SVC_A") <(extract "$SVC_B")
```

Lines prefixed `<` are only on A, `>` only on B.

## Useful jq one-liners

```bash
# Just the IDs from any list command
| jq -r '.data[].id'

# Count by impact
| jq '.data | group_by(.insight_type.impact)
            | map({impact: .[0].insight_type.impact, count: length})'

# CSV row per insight (id, service, impact, detected)
| jq -r '.data[] | [.id, .service.name, .insight_type.impact, .detected_ts] | @csv'

# Pull pagination meta to drive a loop
| jq '.meta | {limit, offset, total}'
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
  ollygarden --context "$ctx" insights list --status active --impact Critical --json \
    | jq -r '"\(.meta.total) critical insights"'
done
```

Don't `auth use-context` mid-script — the per-invocation `--context` flag
keeps each org's call hermetic and avoids mutating the user's saved
state.
