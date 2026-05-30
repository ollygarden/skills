---
name: ollygarden-otel-auto-instrumentation
description: Universal OpenTelemetry auto-instrumentation planning and review guidance. Use when deciding whether agent/library instrumentation is sufficient, when tuning auto-instrumented boundaries, when avoiding duplicate manual spans, or when reviewing auto instrumentation for noise, PII, volume, and business value.
---

# OpenTelemetry Auto-Instrumentation

Use this skill when planning, implementing, or reviewing auto-instrumentation.
It is universal guidance. Language-specific setup skills decide how a runtime enables
the chosen auto-instrumentation; this skill decides whether it should be enabled,
constrained, supplemented, or excluded.

## Non-Negotiable Rules

- Auto-instrumentation availability is not approval to export everything. Include
  only services and boundaries that help debug production issues or explain critical
  business workflows.
- Auto-instrumented boundaries still need scope, signal, privacy, volume, and noise
  decisions before SDK setup writes final configuration.
- Prefer auto spans for standard boundaries such as HTTP, database, messaging, RPC,
  and cache. Do not add manual spans around those same operations unless the manual
  work adds business context without duplicating the auto span.
- Use `auto + manual context` when an auto span exists but the trace would otherwise
  miss a degraded state, fallback, retry outcome, or business milestone. Annotate the
  owning/current span or emit a bounded event instead of wrapping the auto boundary in
  another span.
- Exclude or suppress low-value expected traffic such as health checks, readiness and
  liveness probes, metrics/debug endpoints, static assets, and internal platform probes.
- Do not enable capture of request bodies, response bodies, message payloads, cookies,
  authorization headers, API keys, tokens, credentials, or other sensitive headers.
- Prefer route templates and stable operation names. Avoid raw full URLs, path values
  containing IDs, unsanitized SQL values, message payloads, request IDs, timestamps,
  usernames, emails, and other unbounded values.
- Logs and baggage are not implied by auto-instrumentation. Logs need an explicit
  redaction/export policy. Baggage needs explicitly bounded allowlisted keys.
- Production sampling must be intentional. Unconditional `always_on` for production
  requires an explicit plan rationale or an explicitly documented downstream sampling
  control.

## Decision Workflow

For each detected service and boundary:

1. Identify the business workflow or operational incident this telemetry explains.
2. Decide whether the service is in scope, out of scope, or lower priority.
3. Decide whether the boundary is `auto`, `manual`, `auto + manual context`, or `excluded`.
4. Identify auto-instrumentation tuning required before export:
   - endpoint suppressions
   - service suppressions
   - signal scope
   - sampling policy
   - body/header/payload capture policy
   - SQL or statement sanitization expectations
   - propagation policy
5. Record PII, cardinality, volume, and noise risks in the instrumentation plan.
6. If the auto span already answers the production-debugging question, do not add
   manual instrumentation.

## Common Decisions

### Auto

Use `auto` when a standard instrumentation library or agent covers the boundary and
the default span explains the production question.

Examples:
- inbound HTTP route latency and status
- outbound HTTP dependency latency
- JDBC or ORM query latency with sanitized statement metadata
- Kafka or queue produce/consume trace continuity

### Auto + Manual Context

Use `auto + manual context` when the auto span exists but misses a meaningful business
or degraded outcome.

Examples:
- HTTP request returns 200 with partial data after a fallback
- retries eventually succeed but should be visible as degradation
- a cache miss triggers a slow downstream dependency call
- a message is consumed successfully but routed to a dead-letter path

The manual work should usually annotate the current span or emit a bounded event. Do
not create a duplicate child span around the auto-instrumented HTTP, DB, RPC, messaging,
or cache call.

### Manual

Use `manual` when no auto instrumentation covers the operation and the operation is a
meaningful runtime boundary or critical business milestone.

Examples:
- third-party SDK call not covered by HTTP/RPC instrumentation
- custom workflow step that owns a user-visible outcome
- fallback path that does not cross a separately auto-instrumented boundary

### Excluded

Use `excluded` when telemetry would add cost or cognitive load without improving
runtime understanding.

Examples:
- health/readiness/liveness checks
- metrics/debug/static endpoints
- DTO mapping, object conversion, validation helpers, utility functions
- high-volume platform/control-plane services unless there is a concrete incident use case

## Plan Output Expectations

When used during instrumentation planning, record for every auto-instrumented service
or boundary:

- service name and whether it is in scope
- boundary type
- decision: `auto`, `auto + manual context`, or `excluded`
- business or operational rationale
- required suppressions or tuning
- sensitive data capture risks
- volume/noise risk
- whether SDK setup must enable, disable, or avoid any signal/propagator/exporter

For every `auto + manual context` decision, also record the exact manual context that
must be added and what must not be duplicated.

## Verification Checklist

- [ ] Auto-instrumented services match the plan scope.
- [ ] Auto-instrumented boundaries match the plan decisions.
- [ ] Excluded endpoints/services are suppressed, filtered, downsampled, or explicitly accepted.
- [ ] Manual spans do not duplicate auto HTTP, DB, RPC, messaging, or cache spans.
- [ ] Logs are not exported unless the plan includes a redaction/export policy.
- [ ] Baggage is not enabled unless the plan includes bounded allowlisted keys.
- [ ] Sampling matches the plan and does not accidentally use production `always_on`.
- [ ] No sensitive headers, bodies, message payloads, raw IDs, raw SQL values, or unbounded values are captured.
- [ ] The resulting trace explains the listed business workflows without excessive nesting.
