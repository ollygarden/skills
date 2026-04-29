# Signal Selection

For each boundary identified in the instrumentation plan, select the right signal.
The wrong signal type creates noise. The right signal type makes incidents debuggable
in two minutes. This document is the decision guide.

---

## Signal Decision Tree

For each boundary, ask: what do I need to know about it in production?

**Span** — When you need to trace a request or operation flow through the system.
Spans require parent-child context. They answer "what happened, in what order, how long
did each step take, and which step failed?"

Use spans for:
- HTTP request handling (incoming and outgoing)
- Database calls (SQL, NoSQL, ORM)
- Outgoing service calls (REST, gRPC, message publishing)
- Message processing (consuming from a queue or topic)

**Metric** — When you need to measure rates, latency distributions, utilization, or
saturation. Metrics are what you alert on and put in dashboards. They answer
"is this system healthy right now, and what does normal look like?"

Use metrics for:
- Request counts and error rates
- Duration histograms (p50, p95, p99 latency)
- Queue depths and consumer lag
- Resource utilization (connection pool usage, thread counts)
- Anything that feeds an SLO

**Log/event (via Logs API)** — When you need to record a discrete diagnostic fact
with a timestamp. Events are point-in-time occurrences that aren't spans and aren't
aggregations. They answer "exactly what happened at this moment?"

Use events for:
- Retry attempts (what was attempted, why it failed, which attempt number)
- Fallback activations (primary failed, using secondary)
- Cache misses that trigger downstream calls
- Circuit breaker state changes (open, half-open, closed)
- Authorization denials (who, what resource, why denied)

**Nothing** — If the telemetry won't help debug a production issue, don't emit it.
No signal is better than noisy signal. This is a valid and often correct choice.

Skip telemetry for:
- Cache hits (emit a metric counter at most)
- Successful fast-path operations with no variance
- Internal function calls with no I/O

---

## When to Combine Signals

Some boundaries warrant multiple signals. Don't choose one when two serve different
purposes. Don't add two when one is enough.

**HTTP handlers — span + metrics:**
The span provides trace context and per-request detail. The metrics provide dashboards
and alerting. You need both. The span alone doesn't power your error-rate alert.
The metric alone doesn't tell you which specific request failed and why.

**Database calls — span only (usually):**
Spans capture per-query latency and errors. Add metrics only if you need aggregated
latency dashboards beyond what span-derived metrics already provide. If your observability
platform derives metrics from spans, adding separate database metrics is duplication.

**Background jobs — span + metrics:**
The span traces the job execution (what it processed, what failed). The metrics track
operational health: items processed per run, run duration, failure rate. Both are needed
because jobs run outside request context — you need aggregate visibility and trace detail.

**Message consumers — span + event:**
The span covers the processing of each message. Emit a log event (via Logs API) for
retries, dead-letter routing, or deserialization failures. These are discrete facts with
timestamps that don't belong as span attributes because they describe what happened
_before_ the span succeeded or failed.

---

## The Error Handling Golden Rule

Either record the error OR return the error with context. Never both.
Double-recording creates noise. Missing context creates unsolvable incidents.

**Pattern 1 — Exception in a span you own:**
Set span status to `Error`. Record the exception via the Logs API. Rethrow or handle.
Do this when your code creates the span and the exception means the operation failed.

**Pattern 2 — Error that is handled:**
Do NOT set span status to `Error`. Add attributes describing the outcome
(`fallback.used = true`, `cache.miss = true`, `retry.succeeded = true`).
A handled error is not a span error — the operation completed, just not via the
primary path.

**Pattern 3 — Retried operation that eventually succeeds:**
Record retry attempts via the Logs API (attempt number, error reason, delay).
Do NOT set span status to `Error`. The operation succeeded. The span should reflect
the final outcome, not the intermediate failures.

**Wrong patterns — never do these:**
- Recording the same exception on multiple spans as it propagates up the call stack
- Recording handled exceptions as span errors (the span succeeded from the caller's view)
- Setting span status to `Error` for retried operations that ultimately succeeded
- Setting span status to `Error` and also logging the same exception redundantly in the
  calling layer

---

## Span Status Rule

For every manual boundary, the instrumentation plan must specify that the implement
agent sets span status to `Error` on failure. This is separate from recording the
exception or setting `error.type` — both are needed.

Missing span status is the most common error handling bug. Without it, spans appear
successful in trace backends despite the operation failing. Dashboards, alerts, and
error rate SLIs all depend on span status being set correctly.

The planning step must include an explicit "On error" specification for each manual
boundary. This removes ambiguity and prevents the implement agent from guessing.

**Required error handling for every manual boundary:**

1. **Set span status to ERROR** when the operation fails from the caller's perspective.
2. **Record the exception** via the Logs API (not deprecated `span.AddEvent()` or
   `span.RecordException()`).
3. **Set the `error.type` attribute** to the exception class name or error category.

Do NOT set span status to ERROR for:
- Handled errors where the operation still succeeds (retries, fallbacks)
- Expected conditions (cache misses, empty query results)
- Validation failures that return a normal error response to the caller

---

## Span Event API Deprecation

Do not use `span.AddEvent()` or `span.RecordException()`. These APIs are deprecated.
Use the Logs API to emit events. The SDK's event-to-span-event bridge converts log-based
events to span events for backward compatibility — you get both without calling deprecated
APIs.

For domain-specific exceptions, use the semantic convention event names introduced in
OTel semantic conventions v1.40.0:
- `db.client.operation.exception` — database call exceptions
- `rpc.client.call.exception` — RPC call exceptions
- `http.server.request.exception` — HTTP server request exceptions

These names replace the generic `exception` event name and carry richer semantic meaning
for your observability tooling.

---

## Details That Don't Need Timestamps

Not every detail about an operation needs a timestamped event. If the information
describes the state or outcome at span completion — not a point-in-time occurrence
during the span — record it as a span attribute.

Use span attributes (not events) for:
- Processing outcomes: `item.status = "completed"`, `order.state = "fulfilled"`
- Computed results: `batch.processed = 42`, `records.updated = 7`
- Final state: `retry.count = 3`, `cache.hit = false`, `fallback.used = true`
- Identifiers: `order.id`, `user.id`, `request.id`

Events have timestamps because timing matters. If the timing doesn't matter — if
you're recording what the span produced rather than what happened during it — use
an attribute.

---

## Decision Matrix

Quick reference when you're unsure which signal to use:

| Question | Signal |
|----------|--------|
| Does this happen at a point in time within a transaction? | Emit event via Logs API |
| Is this an application lifecycle event (startup, shutdown, config load)? | Emit log via Logs API |
| Is this debug information about what the span processed or produced? | Span attribute |
| Is this something you'd alert on or put in a dashboard? | Metric |
| Does the timing of this detail not matter — only its final value? | Span attribute |
| Would this telemetry not help diagnose a production incident? | Nothing |

When in doubt, ask: "If I'm paged at 2am, which format helps me understand the problem
faster?" A span attribute I can read inline in the trace. An event I have to expand and
filter. A metric I have to correlate to a trace. Span attributes win for static facts.
Events win for timestamped occurrences. Metrics win for aggregated health.
