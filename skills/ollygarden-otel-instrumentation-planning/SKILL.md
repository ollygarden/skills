---
name: ollygarden-otel-instrumentation-planning
description: Plan Minimal Viable Instrumentation for a codebase. Use when starting instrumentation from scratch, assessing what to instrument in an existing application, or deciding what boundaries need manual vs auto instrumentation. Identifies application boundaries, classifies them as auto-instrumented or manual, selects signals, plans attributes with cardinality awareness, and produces an actionable instrumentation plan tied to SLOs/SLIs. Triggers on "what should I instrument", "add observability", "instrumentation plan", "MVI", or when scanning a codebase without existing instrumentation.
---

# Instrumentation Planning

This skill plans *what* to instrument and *why*, producing an actionable instrumentation plan
tied to SLOs/SLIs. It does not generate code. Implementation mechanics — semconv lookups,
SDK setup, language-specific instrumentation code — are handled by the
manual, auto-instrumentation, SDK setup, and language-specific setup skills.

## Philosophy

Instrumentation exists to understand runtime behavior when debugging production issues.
It is not documentation, not logging-for-the-sake-of-logging, and not a checkbox exercise.

OllyGarden's core beliefs:

- **The pipeline begins at instrumentation.** Quality at the source means less noise
  downstream. A bad span cannot be fixed by a clever query.
- **Instrument the unexpected, not the expected** — except for critical business milestones.
  A successful checkout matters; a health check returning 200 does not.
- **Every signal should answer one question: "Will this help debug a production issue?"**
  If the answer is no, leave it out. You can always add it later.
- **Minimal Viable Instrumentation (MVI)** is the goal. The minimum set that enables
  production debugging, not maximum coverage.

## Workflow

Follow these six steps in order. Each step builds on the previous one.

### Step 1: Assess the codebase

Scan the repository to understand what exists before planning anything new.

1. Search for OpenTelemetry imports, SDK initialization code, and tracer/meter/logger
   provider setup across all source files.
2. Search for existing spans (start span calls, `@WithSpan` annotations, middleware),
   existing metrics (counter, histogram, gauge creation), and structured log calls.
3. Classify the codebase:
   - **Greenfield**: no OTel imports, no SDK initialization, no existing spans or metrics.
   - **Brownfield**: some instrumentation exists. Note exactly what is already covered
     to avoid duplication.
4. Identify the application type (may be a hybrid):
   - **API service**: handles inbound HTTP/gRPC requests, responds synchronously.
   - **Batch processor**: runs on a schedule, processes data in bulk.
   - **Real-time system**: event-driven, streaming, or WebSocket-based.
   - **Background jobs**: async workers, queue consumers, cron tasks.
5. Note the languages, frameworks, and libraries in use — these determine which
   instrumentation libraries are available and what auto-instrumentation covers.
6. Identify business workflows from routes, handlers, jobs, consumers, and service calls:
   - user-visible outcome
   - entry point
   - critical dependencies
   - degraded states and fallbacks
   - business milestones that need positive confirmation

For brownfield codebases, list each existing instrumented boundary so that steps 2-6
can build on what is already in place rather than recreating it.

### Step 2: Map and classify application boundaries

List every runtime boundary, decide whether to include or exclude it, then classify
candidate boundaries as `auto`, `manual`, `auto + manual context`, or `excluded`.
**2.1 — Identify all boundaries:**

Scan for every boundary type present in the codebase:
- HTTP/gRPC handlers (inbound requests)
- Database calls (queries, transactions)
- Messaging (publish/subscribe, queue send/receive)
- RPC calls to other services (outbound HTTP, gRPC)
- Cache operations (Redis, Memcached, in-memory)
- External API calls (third-party services)
- File system or blob storage operations
- Background job dispatch and execution

**2.2 — Include or exclude:**

For each boundary, ask: "Will this help debug a production issue?"

- **Include**: business-critical operations, user-facing APIs, database operations,
  external service calls, message queue operations, cache interactions — anything where
  failure has user or business impact.
- **Exclude**: health checks (`/health`, `/healthz`, `/ready`, `/livez`), metrics endpoints
  (`/metrics`, `/debug/`), static asset handlers (`/static/`, `/assets/`, favicon),
  internal Kubernetes probes, admin/debug endpoints.

Read `references/boundary-prioritization.md` for the full inclusion/exclusion framework.

**2.3 — Classify each included boundary as `auto`, `manual`, `auto + manual context`, or `excluded`:**

For each included boundary, determine the instrumentation strategy. Consult the
companion skills as knowledge sources:

- **`auto`**: an instrumentation library or auto-instrumentation package covers this
  boundary type in the detected language/framework and the generated span explains the
  production debugging question. The SDK setup/finalization phase configures it. The
  implement phase writes NO manual boundary span for it.
- **`manual`**: no instrumentation library covers this specific operation. The implement
  phase must add hand-written span code.
- **`auto + manual context`**: auto-instrumentation covers the technical boundary, but
  the trace would miss a business or degraded outcome unless code adds bounded context
  to the current span or emits a bounded event. The implement phase must not duplicate
  the auto span.
- **`excluded`**: the boundary or service exists but is intentionally omitted,
  suppressed, filtered, or downsampled because telemetry would be low-value, noisy,
  sensitive, or unrelated to business workflows.

Rules:
- If an auto-instrumentation library exists for a standard boundary type, prefer `auto`
  or `auto + manual context`; do not create duplicate manual spans.
- Use `manual` only when no auto library covers the specific operation or when the
  operation is a business milestone/workflow boundary rather than a standard technical
  boundary.
- Use `excluded` for health checks, metrics/debug/static endpoints, low-value platform
  traffic, DTO mapping, object conversion, validation helpers, utility functions, and
  other implementation details.

Read `references/boundary-prioritization.md` for a reference of which boundary types
are commonly auto-instrumented across languages.

Also apply the universal guidance from:
- `ollygarden-otel-auto-instrumentation` for auto-instrumentation scope, tuning,
  suppressions, duplication avoidance, sensitive capture risks, and volume/noise.
- `ollygarden-otel-manual-instrumentation` for manual boundary quality, signal choice,
  propagation, cardinality, and error ownership.

### Step 3: Select signals and plan error handling per boundary

For each included boundary, decide which telemetry signal(s) to use and how errors
should be handled.

**3.1 — Signal selection:**

Walk through each boundary and assign one or more signals:
- **Span**: for request-scoped work with duration, status, and parent-child context.
- **Metric**: for aggregated measurements (rates, distributions, gauges).
- **Log/Event**: for discrete occurrences that need full payload capture.

Read `references/signal-selection.md` for the signal decision tree and the error
handling guidance (the error golden rule).

Common signal combinations:
- HTTP handlers: span + request duration histogram.
- Database calls: span (for trace context) + optional latency histogram.
- Queue consumers: span (for distributed trace) + processing rate counter.

Apply the error golden rule from the reference: record errors on spans using status
and events, do not create separate error metrics that duplicate what span-derived
metrics already provide.

Also define the overall signal scope for SDK setup:
- traces: in scope or out of scope
- metrics: in scope, standard/SLO-only, or out of scope
- logs: in scope only when a redaction/export policy is stated
- baggage: in scope only when bounded allowlisted keys are stated

Do not leave signal scope implicit. SDK setup must be able to tell which providers,
exporters, propagators, and processors are allowed.

**3.2 — Error handling (manual boundaries only):**

For each `manual` boundary, specify in the plan:
1. **Set span status to ERROR on failure**: always yes when the operation fails from the
   caller's perspective. Do not set ERROR for handled errors or retries that succeed.
2. **What to record on error**: record the exception via the Logs API (not the deprecated
   `span.AddEvent()` or `span.RecordException()`). Set the `error.type` attribute.
3. Follow the error golden rule from `references/signal-selection.md`: either record the
   error OR return with context, never both.

This prevents the implement agent from guessing about error handling. Every manual
boundary in the plan must have an explicit "On error" specification.

### Step 4: Plan attributes and assess cardinality

For each instrumented boundary, define the attributes to capture and check cardinality.

1. List the proposed attributes for each boundary's signals.
2. Check OpenTelemetry semantic conventions first — always prefer standard attribute
   names (`http.request.method`, `db.system.name`, `messaging.system`) over custom ones.
   Only invent custom attributes when no semantic convention covers the concept.
3. Read `references/cardinality-guide.md` for cardinality tier definitions, UCUM unit
   conventions, and anti-patterns to avoid.
4. Classify each attribute's cardinality:
   - **LOW**: bounded set, known at deploy time (HTTP method, status code class, db system).
   - **MEDIUM**: bounded but larger set (HTTP route with parameterized paths, operation name).
   - **HIGH**: unbounded or very large set (user ID, request ID, full URL path, query text).
5. Flag any attribute in the HIGH cardinality tier. These are acceptable on spans
   (backends handle high-cardinality span attributes) but dangerous on metrics.
6. Ensure every metric has only LOW or MEDIUM cardinality attributes. If a metric
   needs a HIGH cardinality dimension, move that dimension to a span attribute instead.
7. Review PII and sensitive data risks for each signal source. Explicitly forbid raw
   personal data, credentials, tokens, cookies, authorization headers, request/response
   bodies, message payloads, raw exception messages, raw IDs, timestamps, and other
   unbounded values unless the plan states a safe transformation such as redaction,
   aggregation, or hashing.

### Step 5: Define target SLOs/SLIs

Based on the application type from step 1, recommend SLOs and map them to the
planned instrumentation.

1. Read `references/slo-driven-planning.md` for the SLO-by-application-type mapping
   and SLI implementation requirements.
2. Recommend SLOs appropriate to the application type:
   - API services: availability (success rate), latency (p99 response time).
   - Batch processors: completion rate, processing duration, freshness.
   - Real-time systems: message processing latency, delivery success rate.
   - Background jobs: success rate, queue depth / age, execution duration.
3. Map each SLO to a concrete SLI definition — the specific metric, threshold, and
   time window that will measure the objective.
4. Map each SLI to the boundary and signal from steps 2-3 that will produce the
   required data. Verify the planned instrumentation actually covers each SLI.
5. Flag any recommended SLO that is not yet covered by the planned instrumentation.
   These are gaps that must be resolved before the plan is complete.
6. Important: recommend the metrics needed for SLIs, but do not add them to the plan
   unless the user explicitly requests it. SLI metrics may already be derivable from
   planned spans.

### Step 6: Produce the instrumentation plan

Assemble the final output using the template below.

1. Fill in every section of the template. Do not leave placeholders or TBDs.
2. List auto-instrumented boundaries in the auto table. List manual boundaries as
   individual sections with all required fields.
3. Include the gaps and risks section — be honest about what the plan does not cover,
   what cardinality risks exist, and where signal choices are uncertain.
4. Include SDK setup constraints derived from the plan. The SDK/setup phase needs these
   constraints to avoid enabling extra services, signals, exporters, propagators, or
   auto-instrumentation beyond the MVI.
5. If the codebase is brownfield, note which boundaries are already instrumented and
   whether the existing instrumentation is sufficient or needs changes.
6. Do not include framework-specific code snippets or language-specific wiring. The plan
   specifies observability decisions and SDK constraints. Language-specific mechanics are
   handled by setup skills.

## Output Template

Produce the plan in the following structure:

````markdown
# Instrumentation Plan: {service-name}

## Application Profile
- **Type**: {API service | Batch processor | Real-time system | Background jobs}
- **Existing instrumentation**: {None | Partial — summary}
- **Languages/frameworks**: {e.g., TypeScript with NestJS, Go with net/http}
- **Package manager**: {npm | bun | yarn | pnpm | go | maven | gradle}

## Business Workflows

| Workflow | User outcome | Entry point | Critical dependencies | Degraded states | Trace expectation |
|----------|--------------|-------------|-----------------------|-----------------|-------------------|
| {workflow.name} | {what the user/business expects} | {route/job/consumer} | {services/dependencies} | {fallbacks/retries/partial success} | {what should be understandable from the trace} |

## Target SLOs

| SLO | Target | SLI | Derivable from spans? |
|-----|--------|-----|----------------------|
| Availability | 99.9% success | 5xx error rate at HTTP boundary | Yes |
| Latency | P99 < 500ms | Request duration at HTTP boundary | Yes |

## Services In Scope

| Service | Include? | Role | Reason | SDK strategy | Signals |
|---------|----------|------|--------|--------------|---------|
| {service-name} | {yes/no/low-priority} | {business/control-plane/worker} | {why this service does or does not help production debugging} | {agent/library/manual/none} | {traces/metrics/logs/none} |

## Signal Scope

| Signal | Enabled? | Scope | Reason | Guardrails |
|--------|----------|-------|--------|------------|
| Traces | {yes/no} | {services/boundaries} | {debugging value} | {sampling and suppression constraints} |
| Metrics | {yes/no/standard-only/SLO-only} | {services/boundaries} | {SLI/dashboard value} | {low-cardinality dimensions only} |
| Logs | {yes/no} | {services/events} | {diagnostic value} | {redaction/export policy, or "do not configure logger provider"} |
| Baggage | {yes/no} | {allowlisted keys or "none"} | {why values must propagate} | {bounded, non-sensitive values only} |

## Auto-Instrumented Boundaries

These are handled by instrumentation libraries configured during SDK setup.
The implement phase MUST NOT write manual spans for these. If manual context is needed,
list the target as `auto + manual context` and specify the context separately.

| Service | Boundary | Decision | Library/agent | Covers | Tuning / suppressions | Sensitive data risks | Volume/noise risk |
|---------|----------|----------|---------------|--------|----------------------|----------------------|-------------------|
| {service} | {e.g., HTTP server requests} | {auto/auto + manual context/excluded} | {e.g., Java agent} | {method, route, status} | {health suppression, header/body capture disabled, etc.} | {headers, path IDs, payloads, etc.} | {low/medium/high plus rationale} |

## Manual Boundaries

Each boundary below requires hand-written span code.

### {boundary-name}
- **File**: `{path/to/file}`
- **Function**: `{methodName()}`
- **Strategy**: {manual | auto + manual context}
- **Create new span**: {yes/no}
- **Signal**: {Span | current-span attributes | Metric | Log/Event | Nothing}
- **Attributes**: `{attribute.name}` ({LOW|MEDIUM|HIGH}, PII risk: {none/low/medium/high}, reason: ...)
- **Events/logs**: {none, or exact event name and bounded fields}
- **On error**: {set status behavior, exception/error category behavior, handled-error behavior}
- **Do not record**: {raw IDs, raw messages, payloads, headers, etc.}
- **SLI coverage**: {which SLO this supports, or "Production debugging"}

### {next-boundary-name}
...

## PII And Sensitive Data Policy

| Source | Risk | Decision |
|--------|------|----------|
| {source, e.g., HTTP path params, headers, Kafka payloads, exception messages} | {PII/security/business/cardinality risk} | {remove/redact/hash/aggregate/route-template-only/do not capture} |

## Noise, Volume, And Cost Risks

| Source | Risk | Decision |
|--------|------|----------|
| {source, e.g., health checks, high-volume consumer, control-plane service} | {why it creates cost/noise} | {exclude/downsample/suppress/keep with rationale} |

## Propagation Policy

- **Trace context**: {required/not applicable, boundaries}
- **Baggage**: {disabled, or allowlisted keys with rationale}
- **Messaging propagation**: {required/not applicable, destination headers/properties at a conceptual level}

## SDK Setup Constraints

- **Services to configure**: {list}
- **Services not to configure or lower priority**: {list with rationale}
- **Allowed signals**: {traces/metrics/logs}
- **Disallowed signals**: {logs, baggage, etc. with rationale}
- **Sampling**: {parent-based ratio, collector tail sampling dependency, non-production always_on, or unresolved}
- **Required suppressions**: {health/readiness/metrics/debug/static/control-plane/noisy auto-instrumentations}
- **Sensitive capture restrictions**: {headers, bodies, payloads, raw SQL, raw exception messages}
- **Required env vars**: {endpoint, service version, environment, sampling ratio, etc.}

## Excluded Boundaries
- {boundary} — {one-line reason, e.g., "health check, no diagnostic value"}

## Gaps and Risks
- {Any SLI not covered by the plan}
- {Any cardinality risks flagged}
- {Any boundaries where signal choice is uncertain}
- {Any SDK setup constraint that is unresolved}
- {Any PII/noise/volume risk that implementation must preserve}

## Verification Checklist
- [ ] Business workflows above are understandable from the resulting traces.
- [ ] SDK setup configures only the services and signals allowed by this plan.
- [ ] Logs are not exported unless this plan includes a redaction/export policy.
- [ ] Baggage is not enabled unless this plan includes bounded allowlisted keys.
- [ ] Sampling follows the plan and does not use production `always_on` unless explicitly justified.
- [ ] Health/readiness/metrics/debug/static endpoints are suppressed, filtered, downsampled, or explicitly accepted.
- [ ] Manual spans do not duplicate auto-instrumented HTTP, DB, RPC, messaging, or cache spans.
- [ ] No PII, credentials, payloads, raw IDs, raw exception messages, or unbounded values are recorded.
- [ ] Custom attributes have stated cardinality and investigation value.
````

### What NOT to include in the plan

- **No language-specific code snippets or framework wiring.** The plan specifies
  observability decisions and SDK constraints. How to wire those decisions in a
  language is the job of the setup and implementation skills.
- **No recommended implementation order.** Everything in the plan gets implemented.
- **No phased rollout or tier labels.** The plan is the MVI — the complete set of
  boundaries needed for production debugging. There are no "Phase 2" boundaries.
- **No free-form "Details" prose per boundary.** Use the structured fields above.
  If something doesn't fit in the fields, it probably doesn't belong in the plan.
