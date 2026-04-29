---
name: ollygarden-otel-instrumentation-planning
description: Plan Minimal Viable Instrumentation for a codebase. Use when starting instrumentation from scratch, assessing what to instrument in an existing application, or deciding what boundaries need manual vs auto instrumentation. Identifies application boundaries, classifies them as auto-instrumented or manual, selects signals, plans attributes with cardinality awareness, and produces an actionable instrumentation plan tied to SLOs/SLIs. Triggers on "what should I instrument", "add observability", "instrumentation plan", "MVI", or when scanning a codebase without existing instrumentation.
---

# Instrumentation Planning

This skill plans *what* to instrument and *why*, producing an actionable instrumentation plan
tied to SLOs/SLIs. It does not generate code. Implementation mechanics — semconv lookups,
SDK setup, language-specific instrumentation code — are handled by the
`ollygarden-otel-manual-instrumentation` skill.

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

For brownfield codebases, list each existing instrumented boundary so that steps 2-6
can build on what is already in place rather than recreating it.

### Step 2: Map and classify application boundaries

List every runtime boundary, decide whether to include or exclude it, then classify
included boundaries as auto-instrumented or manual.

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

**2.3 — Classify each included boundary as `auto` or `manual`:**

For each included boundary, determine the instrumentation strategy:

- **`auto`**: an instrumentation library or auto-instrumentation package covers this
  boundary type in the detected language/framework. The SDK setup phase configures it.
  The implement phase writes NO code for it.
- **`manual`**: no instrumentation library covers this specific operation. The implement
  phase must add hand-written span code.

Rule: if an auto-instrumentation library exists for the boundary type, classify it as
`auto`. Only classify as `manual` when no library covers the specific operation.

Read `references/boundary-prioritization.md` for a reference of which boundary types
are commonly auto-instrumented across languages.

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
4. If the codebase is brownfield, note which boundaries are already instrumented and
   whether the existing instrumentation is sufficient or needs changes.
5. Do not include implementation notes, recommended implementation order, context
   propagation strategy, or framework-specific advice. The plan specifies *what* to
   instrument, not *how* to implement it.

## Output Template

Produce the plan in the following structure:

````markdown
# Instrumentation Plan: {service-name}

## Application Profile
- **Type**: {API service | Batch processor | Real-time system | Background jobs}
- **Existing instrumentation**: {None | Partial — summary}
- **Languages/frameworks**: {e.g., TypeScript with NestJS, Go with net/http}
- **Package manager**: {npm | bun | yarn | pnpm | go | maven | gradle}

## Target SLOs

| SLO | Target | SLI | Derivable from spans? |
|-----|--------|-----|----------------------|
| Availability | 99.9% success | 5xx error rate at HTTP boundary | Yes |
| Latency | P99 < 500ms | Request duration at HTTP boundary | Yes |

## Auto-Instrumented Boundaries

These are handled by instrumentation libraries configured during SDK setup.
The implement phase MUST NOT write manual code for these.

| Boundary | Library | Covers |
|----------|---------|--------|
| {e.g., HTTP server requests} | {e.g., instrumentation-http, instrumentation-express} | {e.g., Inbound request spans with method, route, status} |

## Manual Boundaries

Each boundary below requires hand-written span code.

### {boundary-name}
- **File**: `{path/to/file}`
- **Function**: `{methodName()}`
- **Span name**: `{operation.name}`
- **Signal**: {Span | Span + Metric | Span + Event}
- **Attributes**: `{attribute.name}` ({LOW|MEDIUM|HIGH}), ...
- **On error**: Set span status to ERROR. Record exception via Logs API. Set `error.type`.
- **SLI coverage**: {which SLO this supports, or "Production debugging"}

### {next-boundary-name}
...

## Excluded Boundaries
- {boundary} — {one-line reason, e.g., "health check, no diagnostic value"}

## Gaps and Risks
- {Any SLI not covered by the plan}
- {Any cardinality risks flagged}
- {Any boundaries where signal choice is uncertain}
````

### What NOT to include in the plan

- **No implementation notes or framework advice.** The plan specifies boundaries and
  their instrumentation requirements. How to implement them is the job of the
  `ollygarden-otel-manual-instrumentation` skill.
- **No recommended implementation order.** Everything in the plan gets implemented.
- **No phased rollout or tier labels.** The plan is the MVI — the complete set of
  boundaries needed for production debugging. There are no "Phase 2" boundaries.
- **No context propagation strategy section.** Context propagation is an implementation
  concern handled by auto-instrumentation libraries and the SDK.
- **No free-form "Details" prose per boundary.** Use the structured fields above.
  If something doesn't fit in the fields, it probably doesn't belong in the plan.
