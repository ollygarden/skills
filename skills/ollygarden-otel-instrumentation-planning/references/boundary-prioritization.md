# Boundary prioritization

Use this reference after inventorying the codebase. Coverage varies by language, framework,
library, and version; verify it with the relevant upstream `otel-*` skill.

## Decision sequence

| Question | Decision |
|---|---|
| Does the boundary answer a production-debugging or confirmed SLI question? | If no, `excluded`. |
| Does current instrumentation cover the operation and useful outcome? | If yes, `auto`. |
| Is the technical span sufficient but missing bounded business/degraded context? | `auto + manual context`; update the current span. |
| Is this an uncovered technical boundary or justified business workflow/milestone? | `manual`. |

Do not infer `manual` merely because application code calls a third-party SDK. Underlying HTTP,
RPC, cloud, or library instrumentation may already cover the operation. Conversely, the existence
of a library does not prove that it is enabled or that its span answers the debugging question.

## Candidate boundaries

Inventory, rather than automatically include:

- inbound and outbound HTTP or RPC;
- database and cache operations;
- message publish, receive, processing, retry, and dead-letter routing;
- external APIs and storage;
- background-job dispatch and execution;
- business workflows and critical success milestones.

Technical boundaries describe handoffs between systems. Business workflow spans may describe a
coherent in-process operation when its outcome cannot be understood from child technical spans.
Keep both categories explicit.

## Common exclusions

Usually exclude or suppress:

- health, readiness, liveness, metrics, debug, and static-asset endpoints;
- platform probes and low-value control-plane traffic;
- DTO mapping, validation helpers, constructors, utilities, and loop iterations;
- duplicate manual spans around auto-instrumented database, HTTP, RPC, messaging, or cache calls;
- telemetry whose only purpose is documenting normal internal execution.

These are defaults, not universal facts. Retain an endpoint or operation when it has a concrete
business, production-debugging, or SLI role and document the volume/privacy tradeoff.

## Unexpected outcomes and milestones

Add bounded context for retries, fallbacks, circuit-breaker changes, rate limiting, partial results,
and degraded responses. Do not add separate spans for every occurrence when the current boundary
span can carry the outcome safely.

Critical milestones such as a completed payment or accepted order may justify positive confirmation.
Prefer a business span only when the milestone has meaningful duration or child work; otherwise use
a bounded attribute or diagnostic record under the plan's signal and privacy policies.
