# OllyGarden Olive API Reference

Base URL: `https://api.ollygarden.cloud`
Auth: `Authorization: Bearer <OLLYGARDEN_API_KEY>`
Rate limit: 60 req/min

## Services

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/services` | List all services with scores |
| GET | `/api/v1/services/search?q={name}` | Search by name — returns all versions |
| GET | `/api/v1/services/{id}` | Single service detail |
| GET | `/api/v1/services/{id}/insights` | Paginated insights for a service |

**Picking the latest version**: sort results by `last_seen_at` descending, take the first entry.

## Insights

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/insights` | All insights (supports `?service_id=`, `?status=`, `?impact=`) |
| GET | `/api/v1/insights/{id}` | Single insight with full details |

### Insight object fields

| Field | Description |
|-------|-------------|
| `insight_type.display_name` | Human-readable name |
| `insight_type.impact` | `Critical`, `Important`, or `Normal` |
| `insight_type.remediation_instructions` | **Always follow these when fixing** |
| `status` | `active`, `resolved`, etc. |
| `attributes` | Signal-specific evidence (counts, messages, span names, etc.) |
| `detected_ts` | When the issue was first detected |
| `trace_id` | Trace ID for deeper investigation (if present) |

## Other endpoints

- `GET /api/v1/organization` — org details and subscription info
- `GET /api/v1/analytics/services` — usage and cost analytics
- `GET/POST /api/v1/webhooks` — webhook management
