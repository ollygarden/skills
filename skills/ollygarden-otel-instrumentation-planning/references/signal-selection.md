# Signal and error decisions

Choose signals from the question the telemetry must answer, not from a coverage checklist.

## Signal selection

| Needed answer | Candidate signal | Constraint |
|---|---|---|
| What happened across an operation, in what order, and where did it fail? | Span | Requires meaningful boundary and context. |
| What is the aggregate rate, distribution, utilization, or SLI state? | Metric | Prefer standard/span-derived metrics and bounded dimensions. |
| What bounded diagnostic fact occurred at a meaningful time? | Log/diagnostic record | Requires the plan's redaction/export policy. |
| No production or SLI question | Nothing | Exclude it. |

Multiple signals are justified only when they answer different questions. Do not prescribe metrics
for every HTTP handler or job when existing standard/span-derived telemetry already provides the
required SLI. Do not create a diagnostic record for final state that belongs as a bounded span
attribute.

## Error ownership

For every manual boundary, plan all four decisions:

1. Define failure from the caller's perspective.
2. Set span status to `Error` only when that owned operation failed.
3. Set a bounded `error.type` category according to current semantic conventions.
4. Name the single layer that records the exception or bounded diagnostic record.

Record once at the owning boundary. Returning or propagating an error is allowed; upstream layers
must not record it again. A retry or fallback that ultimately succeeds is not a failed parent
operation, though a bounded retry/fallback outcome may still aid diagnosis.

Expected conditions are not automatically errors. Classify validation failures, cache misses,
empty results, cancellations, and client responses from the application's contract rather than
from a universal status-code rule.

## Event/log API status

Status captured 2026-07-31: the accepted span-events-to-logs migration plan does not make every
released span-event API deprecated, and bridge support varies by language and version. Consult
`otel-span-events-to-logs-migration` before selecting a current API or claiming that a log record
also appears as a span event. Keep version-specific event names out of this plan.

## Static facts versus occurrences

Use a span attribute for bounded final state or outcome when its timing does not matter. Consider a
diagnostic record only when occurrence time matters and the logs policy permits it. Payloads, raw
messages, raw identifiers, and raw exception text remain prohibited by the plan's privacy contract.
