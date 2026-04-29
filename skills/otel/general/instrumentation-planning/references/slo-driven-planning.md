# SLO-Driven Planning

Don't add metrics unless they support an SLI. This is OllyGarden's strongest opinion
on instrumentation. Metric sprawl — dashboards full of data nobody acts on — happens
when engineers instrument "just in case." Every metric in the plan must trace back to
an SLI. If it doesn't, don't add it.

---

## SLO Patterns by Application Type

Starting point for SLO design. Adapt to your actual user commitments.

| Application Type  | SLO                    | Target                                 | Notes                                        |
|-------------------|------------------------|----------------------------------------|----------------------------------------------|
| API services      | Availability           | 99.9% success rate                     | 4xx are not availability issues — only 5xx   |
| API services      | Latency                | P99 < 500ms                            | Measured at HTTP handler boundary            |
| Batch processing  | Completeness           | 100% of items processed                | Flag partial runs as SLO breaches            |
| Batch processing  | Timeliness             | 95% completed within SLA window        | Measure wall-clock time from trigger to done |
| Real-time systems | Latency                | P99 < 100ms                            | Measure at the processing boundary           |
| Real-time systems | Throughput             | Process X events/second                | X is defined by the downstream SLA           |
| Background jobs   | Success rate           | 99.9% eventual success with retries    | Final outcome after retries, not per-attempt |
| Background jobs   | Processing time        | P95 within expected duration           | Alert when jobs run longer than the SLA      |

These are defaults. Override them when the product has different commitments.

---

## SLI Implementation Requirements

For each SLI in the plan, verify these before finalizing the instrumentation:

**Metric at the right boundary.** The SLI must be measurable at the user-facing
boundary, not at an internal component. Measuring database latency doesn't tell you
whether the user experienced a slow response. Measure at the HTTP handler or the
entry point of the job.

**Attributes that distinguish critical from non-critical operations.** Not every
endpoint contributes equally to the SLO. An SLI covering `/healthz` and `/checkout`
equally is not useful. Add attributes so you can segment — `operation.critical = true`,
or a more specific `transaction.type` attribute.

**Error classification separating user errors from system errors.** Availability SLIs
require this. A 400 is the user's fault. A 500 is yours. If your metric doesn't carry
`http.response.status_code` or an equivalent error-type attribute, you cannot compute
availability — you can only compute total error rate, which is wrong.

**Business context attributes that identify transaction types.** When SLOs differ by
transaction type (checkout vs. browse, priority job vs. bulk job), the metric must
carry the attribute that enables segmentation. Aggregate-only metrics prevent per-type
SLO calculation.

**Aggregation level matches user experience.** Measure at the boundary the user crosses.
Aggregating across internal hops inflates success rates and hides latency. If a user
request touches three internal services, the SLI lives at the outermost one.

---

## Common SLI-to-Metric Mapping

Concrete mappings for the most common SLIs:

**Availability SLI → `http.server.request.duration` histogram**
Requires `http.response.status_code` attribute. Calculate:
`(total requests - 5xx requests) / total requests`
The histogram already exists in any OTel-instrumented HTTP server. Do not add a
separate counter for this.

**Latency SLI → `http.server.request.duration` histogram**
Read P95/P99 from the distribution. Same histogram as availability — one instrument
serves both SLIs. Bucket boundaries must cover your target (if P99 target is 500ms,
ensure a bucket at 500ms exists in the histogram configuration).

**Data freshness SLI → custom gauge or histogram**
`processing_timestamp - event_timestamp` in seconds. This SLI has no standard metric.
Record it as a histogram per message type or data class. There is no built-in for this —
it must be added explicitly, and only if freshness is an SLO commitment.

**Error budget SLI → error rate counter per transaction type**
Classify by user error vs. system error. Use `error.type` or `http.response.status_code`
to separate the two. Sum system errors over the error budget window to track burn rate.

---

## Gap Analysis Guidance

When producing the instrumentation plan, flag the following as gaps:

**Missing SLO coverage.** For each recommended SLO in the table above that matches
the application type, check whether the plan includes a supporting SLI. If not, call
it out explicitly — don't silently skip it. The user may have a reason to exclude it,
but that's their call, not the planner's.

**SLI requiring an unplanned metric.** If an SLI depends on a metric not produced by
the planned instrumentation, flag it. State which metric is missing and at which
boundary it belongs.

**Missing error classification.** If the plan instruments an HTTP boundary or a
job execution boundary without attributes that distinguish user errors from system
errors, flag the availability SLI as uncalculable. A metric without error classification
can tell you "something failed" but not whether you broke your SLO.

---

## Important Constraint

Do NOT add metrics unless explicitly requested by the user or required by an SLI.
Recommend which metrics would support SLIs, but let the user decide whether to
implement them.

When a gap analysis surfaces missing metrics, present them as recommendations with
the SLI they enable — not as additions to the plan. The user owns the decision. This
prevents over-instrumentation as much as it prevents metric sprawl from enthusiasm.
