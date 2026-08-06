---
name: ollygarden-otel-instrumentation-planning
description: Plan Minimal Viable Instrumentation for a codebase. Use when starting instrumentation from scratch, assessing what to instrument in an existing application, or deciding what boundaries need manual vs auto instrumentation. Identifies application boundaries, classifies them as auto-instrumented or manual, selects signals, plans attributes with cardinality awareness, and produces an actionable instrumentation plan tied to SLOs/SLIs. Triggers on "what should I instrument", "add observability", "instrumentation plan", "MVI", or when scanning a codebase without existing instrumentation.
---

# Instrumentation planning

Plan what to instrument and why; do not generate implementation code. Delegate current semantic
conventions and SDK mechanics to the relevant upstream `otel-*` skill, then use OllyGarden setup
skills for implementation.

The objective is Minimal Viable Instrumentation (MVI): the smallest set of telemetry that makes
production failures understandable. Preserve critical business milestones, but exclude telemetry
that cannot answer a production-debugging or stated SLI question.

## Protected rules

- Never duplicate a boundary span already produced by auto-instrumentation.
- Logs require an explicit redaction and export policy. Otherwise keep logs out of SDK scope.
- Baggage requires bounded, non-sensitive allowlisted keys. Otherwise disable it.
- Raw personal data, credentials, tokens, cookies, authorization headers, bodies, message
  payloads, identifiers, SQL values, and exception messages are outside MVI. A separately approved
  data policy may allow a specific sanitized value; hashing alone neither anonymizes it nor reduces
  cardinality.
- Do not recommend production `always_on` sampling without estimated volume/cost and explicit user
  approval; diagnostic importance alone is insufficient justification.
- Produce decisions and constraints, not framework wiring, code snippets, or implementation phases.

## Workflow

Follow these six steps in order.

### 1. Assess the codebase

Scan all services before proposing telemetry:

1. Inventory OTel imports, SDK/provider setup, exporters, propagators, auto-instrumentation,
   manual spans, metrics, and structured logs.
2. Classify each service as greenfield or brownfield and record existing coverage.
3. Identify application types, including hybrids: API, batch, real-time, and background worker.
4. Trace business workflows from their user-visible outcome through entry points, dependencies,
   degraded states, fallbacks, and critical success milestones.
5. Record languages, frameworks, libraries, and package managers. Use current upstream skills to
   verify coverage; do not infer it from a universal library list.

### 2. Decide boundaries

Inventory technical boundaries (HTTP/RPC, database, messaging, cache, external API, storage, job
dispatch/execution) and business workflow or milestone boundaries. For each, choose exactly one:

- `auto`: current instrumentation covers the operation and its debugging question.
- `manual`: no current instrumentation covers the operation, or it is a justified business
  workflow/milestone span.
- `auto + manual context`: the technical span exists, but bounded business or degraded-outcome
  context must be added to the current span. Do not create another boundary span.
- `excluded`: low-value, noisy, sensitive, or unrelated to a production/SLO question.

Use [boundary-prioritization.md](references/boundary-prioritization.md) for edge cases. Apply
`ollygarden-otel-auto-instrumentation` and `ollygarden-otel-manual-instrumentation` as supporting
opinions. Typical exclusions include health/readiness, metrics/debug, static assets, probes, and
internal helpers; inspect the application before treating any pattern as absolute.

### 3. Choose signals and error ownership

For every included boundary, choose only the signals needed for its debugging or SLI question.
Define overall SDK scope for traces, metrics, logs, and baggage; never leave provider/exporter scope
implicit.

Prefer standard or span-derived metrics. If an SLI needs a missing custom metric, record it as a
recommendation and plan gap unless the user has authorized adding it to implementation scope.

For every manual boundary, state:

- when the operation is considered failed and whether span status becomes `Error`;
- the bounded `error.type` category;
- which layer records the exception or diagnostic record.

Record a failure once at the boundary that owns the failed operation. Propagation is allowed;
upstream layers must not record it again. A handled retry or fallback that ultimately succeeds is
not a failed parent operation. See [signal-selection.md](references/signal-selection.md). For
current event/log API status, use `otel-span-events-to-logs-migration`.

### 4. Plan attributes and cost

Use `otel-semantic-conventions` for current names, units, and signal requirements. For each
proposed attribute, record:

- whether its values are bounded;
- its estimated metric-series cross-product;
- its privacy/sensitivity risk;
- the investigation or SLI question it answers.

Metric dimensions must be bounded and remain within the stated series budget. Span attributes do
not receive a blanket exemption: unbounded values still carry privacy, storage, and backend-cost
risk. Apply the protected raw-data rule above.

### 5. Map SLOs and SLIs

Use the user's product commitments; do not silently turn example targets into commitments. Map
each confirmed or proposed SLO to a concrete SLI, user-facing boundary, signal, classification,
threshold, and window. Mark targets as unconfirmed when the repository does not define them.

Verify that planned or existing telemetry can calculate each SLI. Keep missing custom metrics as
explicit gaps unless their implementation is authorized. Use
[slo-driven-planning.md](references/slo-driven-planning.md) for the decision rules.

### 6. Render and verify

Render the result with [plan-template.md](references/plan-template.md). Fill every applicable
field, remove inapplicable rows, and leave no placeholders or TBDs.

Before returning the plan, verify:

- business workflows are understandable from the proposed traces;
- existing brownfield coverage is inventoried and not duplicated;
- SDK scope enables only planned services and signals;
- logs, baggage, sampling, suppression, privacy, propagation, volume, and cost decisions are
  explicit;
- every manual boundary has failure and recording ownership;
- every SLI maps to available telemetry or an explicit gap;
- the output contains no implementation code or phased backlog.
