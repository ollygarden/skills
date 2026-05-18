# Cardinality Guide

Cardinality is the number of unique attribute value combinations a metric or span can
produce. High cardinality in metrics causes storage explosions and query timeouts.
The wrong attribute on the wrong signal is not a style issue — it's a production incident
waiting to happen.

---

## Cardinality Tiers

### LOW — fewer than 100 unique values

Always safe. Use freely on both spans and metrics.

Examples: HTTP methods (`GET`, `POST`, `DELETE`), HTTP status codes (`200`, `404`, `500`),
route templates (`/orders/{id}`, `/users/{id}/settings`), operation names
(`create_order`, `send_notification`), span kinds (`client`, `server`, `consumer`),
boolean flags (`cache.hit`, `retry.succeeded`).

These values are bounded by design. No matter how much traffic you handle, the set
of HTTP methods does not grow.

### MEDIUM — fewer than 1000 unique values

Acceptable for spans. Acceptable for metrics only if the dimension is bounded and stable.
Stable means: the set of values is defined by deployment or configuration, not by user
behavior or data volume.

Examples: Customer tiers (`free`, `pro`, `enterprise`), deployment environments
(`production`, `staging`, `canary`), geographic regions (`us-east-1`, `eu-west-1`),
service versions (`1.4.2`, `1.5.0`), database names (`orders`, `catalog`, `users`).

Before adding a MEDIUM cardinality attribute to a metric, ask: who controls the set of
values? If the answer is your engineering team or your infrastructure configuration,
it's probably safe. If the answer is your customers or your data, it's probably not.

### HIGH — unbounded

Never use in metric attributes. Ever. Not even temporarily.

Examples: User IDs, request IDs, session IDs, trace IDs, timestamps, raw URLs,
raw SQL text, free-form log messages, IP addresses, email addresses, order IDs,
product SKUs.

For spans: unbounded values are acceptable on the specific span where they provide
debugging value. `db.query.text` on a database span is appropriate — it tells you
exactly what query ran slowly. `user.id` on an HTTP server span is appropriate —
it tells you whose request failed.

The rule for spans: add the high-cardinality attribute to the span where it has
diagnostic value. Do not propagate it to parent spans. Do not use it as a metric
dimension under any circumstances.

---

## Attribute Planning Rules

When selecting attributes for each instrumented boundary, apply these rules.

**Prefer bounded values for metrics:**
- HTTP method, route template, status code
- Operation name, destination name
- Region, deployment environment
- Customer tier, database name

**Always exclude from metric attributes:**
- Raw user IDs, account IDs, order IDs — any entity identifier
- Full URLs (use route templates instead)
- Raw SQL text
- Free-form messages or descriptions
- Timestamps and time-derived values
- IP addresses and hostnames that scale with traffic

**For span attributes:**
Unbounded values are acceptable where they provide direct debugging value — on the
span that performed the operation in question. A database span can carry `db.query.text`.
An HTTP server span can carry `user.id`. A payment span can carry `payment.id`.

What you must not do: use these as metric dimensions, or propagate them to parent spans
that aggregate across many operations. The parent span for an entire HTTP request does
not need every `db.query.text` from every database call it made.

---

## UCUM Units

OllyGarden requires correct UCUM units on all metrics. Wrong units are bugs, not
formatting preferences.

| Metric type | Unit | Example |
|-------------|------|---------|
| Utilization (ratio) | `1` | CPU usage 0.0–1.0, connection pool fill |
| Counts | `{request}`, `{error}`, `{item}` | HTTP requests, failed operations, queue items |
| Duration | `s` | Request latency, job duration |
| Size | `By` | Payload size, memory usage |

**Unit annotation rules:**
- Curly braces denote annotations: `{request}` not `request` and not `requests`
- Singular form only: `{request}` not `{requests}`, `{error}` not `{errors}`
- Duration in seconds: `s` not `ms`. Use seconds. Histogram buckets handle the scale.
- Bytes non-prefixed: `By` not `MiBy`, not `KiBy`. Raw bytes, always.
- Dimensionless ratios: `1` not `percent`, not `%`, not `ratio`

---

## Naming Anti-Patterns

These are bugs. Fix them before shipping instrumentation.

**Service name in metric name:**
`myservice.http.server.request.duration` → `http.server.request.duration`

The service name is a resource attribute (`service.name`). It does not belong in the
metric name. Putting it there breaks cross-service aggregation and makes dashboards
impossible to template. The metric name describes the operation, not who owns it.

**Company or product name in metric name:**
`acmecorp.db.client.duration` → `db.client.operation.duration`

Same problem. Organizational names have no place in metric names. Use semantic convention
names where they exist.

**`_total` suffix:**
Never append `_total` to metric names, neither on Counters nor on UpDownCounters.

On Counters: `_total` is ambiguous between delta and cumulative temporality. Delta
backends receive increments — "total" is misleading. Let the backend or pipeline
handle suffix conventions.

On UpDownCounters: `_total` implies monotonic sum, which UpDownCounters are not.
A reader seeing `active_connections_total` expects a counter that never goes down.
That's wrong and dangerous.

**Wrong pluralization for UpDownCounters:**
`system.processes` → `system.process.count`

UpDownCounters represent current measurements of a quantity. Name them as measurements:
`system.process.count`, `db.client.connection.count`, `messaging.consumer.count`.
Pluralizing the noun (`processes`, `connections`) is ambiguous. Use `.count`.

**Wrong unit for annotated values:**
`"1"` (string one) instead of `{request}` for count annotations, or using `ms` instead
of `s` for duration.

---

## Cardinality Monitoring Targets

When reviewing an instrumentation plan, flag the following as requiring justification
before proceeding:

- Unique span names per service would exceed ~100. Span names drive trace search and
  aggregation. Too many names means spans are named too specifically — they encode
  variable data that should be in attributes.

- Unique attribute value combinations per metric would exceed ~1000. Estimate this by
  multiplying the cardinality of each attribute dimension. Three attributes with 10
  values each yields 1000 combinations — already at the limit.

- Any metric attribute uses an unbounded value. There are no exceptions. An unbounded
  metric attribute is a cardinality explosion, not a cardinality risk.

If a plan hits any of these conditions, the plan requires revision before implementation.
