# SLO-driven planning

SLOs are product commitments, not OpenTelemetry defaults. Use repository or user-provided targets.
When none exist, propose relevant SLO categories and mark their targets as unconfirmed.

## Candidate categories

| Application type | Candidate user-facing concerns |
|---|---|
| API | availability, latency, correctness |
| Batch | completion, timeliness, freshness |
| Real-time | processing latency, delivery success, sustained throughput |
| Background worker | eventual success, queue age, execution time |

For hybrids, evaluate each user-visible workflow at its outer boundary. Do not force the service
into one application type.

## SLI contract

For every confirmed or proposed SLO, state:

- target and window, or `unconfirmed`;
- the user-facing measurement boundary;
- the exact existing or proposed signal;
- the bounded dimensions needed to distinguish meaningful operation classes;
- how expected/user-caused outcomes differ from system failures;
- whether the SLI is already calculable.

Do not assume that a recommended metric is enabled merely because an instrumentation library
supports it. Verify provider and instrumentation configuration.

## Metric policy

Prefer an existing standard metric or a metric derived from spans. Avoid a separate error counter
when the operation metric already has a suitable error classification. If a confirmed SLI cannot be
calculated, identify the missing metric and boundary as a plan gap. Adding that custom metric to
implementation scope requires user authorization.

Do not copy fixed example targets such as 99.9% availability or a particular percentile latency
into the plan as commitments. If useful, present them only as clearly labeled examples for the user
to confirm.

## Gap checks

Flag:

- an SLO with no measurable boundary or window;
- a metric assumed rather than verified;
- missing outcome/error classification;
- dimensions whose cross-product exceeds the stated series budget;
- an internal measurement substituted for the user's experience;
- a custom metric recommendation presented as authorized implementation.
