---
name: insight-remediation
description: "Fetch active OllyGarden service insights from the Olive API and apply remediation fixes to the current codebase. Use when the user asks to get insights, fix insight, address insight, or remediate insight for the current service. Retrieves insights grouped by impact, then applies fixes strictly following the API-provided remediation_instructions."
---

# Insight Remediation

Fetch and fix OllyGarden service insights by following the remediation instructions
provided by the Olive API. This skill empowers coding agents to automatically obtain
insights for the current service and apply the prescribed fixes.

## Setup

### API keys configuration

Keys are stored in `~/.config/ollygarden/keys.json` as a map of organization ID to API key.
The directory and file must be locked down to the current user:

```bash
mkdir -p ~/.config/ollygarden
chmod 700 ~/.config/ollygarden
# keys.json is owner-read/write only
chmod 600 ~/.config/ollygarden/keys.json
```

Ensure `~/.config/ollygarden/` is in the global gitignore to prevent accidental commits:

```bash
echo '.config/ollygarden/' >> ~/.config/git/ignore
```

Example `keys.json`:

```json
{
  "org_2yZuIR5qtYvNPeWqbwSfKrkr6Kc": "og_sk_S2xHkp_...",
  "org_3aBcDeF7ghIjKlMnOpQrStUvWxY": "og_sk_Xz9Qw1_..."
}
```

To obtain the organization ID for a new key, call any service endpoint and read the
`organization_id` field from the response, or call `GET /api/v1/services` and take
`data[0].organization_id`.

### Key resolution (in order)

1. If the user specifies an organization ID, use that org's key from `keys.json`.
2. Check `$OLLYGARDEN_API_KEY` env var (used as fallback / single-org shortcut).
3. Read `keys.json` — if it has exactly one entry, use it automatically; if multiple, ask the user which org.
4. If no key is found, ask the user for the API key. Then call the API to discover the
   org ID, and persist both to `keys.json`.

```bash
# Read a specific org key
KEY=$(jq -r '.["org_2yZuIR5qtYvNPeWqbwSfKrkr6Kc"]' ~/.config/ollygarden/keys.json 2>/dev/null)

# Fallback to env var
KEY="${KEY:-$OLLYGARDEN_API_KEY}"

# When adding a new key, discover the org ID automatically:
mkdir -p ~/.config/ollygarden && chmod 700 ~/.config/ollygarden
FILE=~/.config/ollygarden/keys.json
[ -f "$FILE" ] || echo '{}' > "$FILE"
NEW_KEY="og_sk_..."
ORG_ID=$(curl -s -H "Authorization: Bearer $NEW_KEY" \
  "https://api.ollygarden.cloud/api/v1/services" | jq -r '.data[0].organization_id')
jq --arg org "$ORG_ID" --arg key "$NEW_KEY" '. + {($org): $key}' "$FILE" > "$FILE.tmp" && mv "$FILE.tmp" "$FILE"
chmod 600 "$FILE"
```

**API docs**: See `references/api.md` for full endpoint reference. For anything beyond
that, fetch `https://api.ollygarden.cloud/llms.txt`.

## Workflow

### 1. Fetch insights for the current service

Infer the service name from the current repo directory name or `go.mod` module path.
Resolve the API key for the target organization (see key resolution above).

```bash
# Resolve key for the target org
KEY=$(jq -r '.["org_2yZuIR5qtYvNPeWqbwSfKrkr6Kc"]' ~/.config/ollygarden/keys.json 2>/dev/null)
KEY="${KEY:-$OLLYGARDEN_API_KEY}"

# Search all versions of the service
curl -s -H "Authorization: Bearer $KEY" \
  "https://api.ollygarden.cloud/api/v1/services/search?q={service-name}" | jq .

# Pick the entry with the most recent last_seen_at, then fetch its insights
curl -s -H "Authorization: Bearer $KEY" \
  "https://api.ollygarden.cloud/api/v1/services/{id}/insights" | jq .
```

### 2. Present insights to the user

List all active insights grouped by impact (Critical > Important > Normal). For each show:
- `insight_type.display_name` and `insight_type.impact`
- `detected_ts` and key `attributes`
- A one-line summary of what's wrong

### 3. Fix an insight

**CRITICAL RULE**: Always fix using the `remediation_instructions` field from the API
response — not general best practices or prior knowledge. Read those instructions first,
then act on them.

Steps:
1. Quote the full `remediation_instructions` to the user before starting work.
2. Apply fixes in the order the instructions describe.
3. After fixing, run the project's linter and tests to verify nothing is broken.

See `references/api.md` for full endpoint reference.
