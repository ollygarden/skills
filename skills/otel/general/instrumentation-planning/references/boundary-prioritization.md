# Instrumentation Boundary Prioritization

Instrumentation exists to understand runtime behavior when debugging production issues.
That's the only job. Every span, every attribute, every event — ask: "Will this help
me diagnose a production incident?" If the answer is no, don't add it.

The pipeline begins at instrumentation. Quality at the source means less noise downstream.
A well-instrumented service produces traces you can read in two minutes. A
poorly-instrumented one produces traces you spend two hours filtering.

---

## Include or Exclude

Not all code deserves spans. For each boundary in the codebase, decide: include or exclude.

**Include** — boundaries where failure has user or business impact:

- Business-critical operations: payments, orders, auth, user registration
- Revenue-impacting endpoints: checkout, billing, subscription management
- User-facing APIs: search, catalog, authentication flows
- Database operations: SQL queries, NoSQL reads/writes, ORM calls
- External API calls: Stripe, Twilio, SendGrid, any third-party provider
- Message queue operations: publishing, consuming, dead-letter routing
- Cache interactions: Redis, Memcached (miss rates and latency drive many incidents)
- Background jobs with SLAs: delayed jobs compound; you need visibility
- Data pipelines and ETL jobs: failures cause silent data corruption

**Exclude** — boundaries with no diagnostic value:

- Health checks: `/health`, `/healthz`, `/readiness`, `/liveness`, `/ready`, `/livez`
- Metrics and debug endpoints: `/metrics`, `/pprof`, `/debug`
- Static asset handlers: `/static/`, `/assets/`, favicon, CSS, JS, images
- Internal Kubernetes probes
- Admin/debug endpoints (unless they affect production behavior)

---

## Auto-Instrumentation Coverage

After deciding which boundaries to include, classify each as `auto` or `manual`.

**`auto`** means an instrumentation library covers this boundary type. The SDK setup
phase configures it. The implement phase writes NO code for it.

**`manual`** means no instrumentation library covers this specific operation. The
implement phase must add hand-written span code.

Rule: if an auto-instrumentation library exists for the boundary type, classify it
as `auto`. Only classify as `manual` when no library covers the specific operation.

### Commonly auto-instrumented boundary types

These are covered by instrumentation libraries in most major languages (Node.js, Go,
Java, Python, .NET, Ruby). Always verify that the specific library exists for the
detected language and framework before classifying as auto.

| Boundary type | Typical libraries | What they cover |
|--------------|-------------------|-----------------|
| HTTP server requests | instrumentation-http, instrumentation-express, instrumentation-nestjs-core, otelhttp | Inbound request spans with method, route, status code |
| HTTP client requests | instrumentation-http, instrumentation-undici, otelhttp | Outbound HTTP spans with URL, method, status code |
| SQL databases | instrumentation-pg, instrumentation-mysql2, otelsql | Query spans with db.system, db.statement |
| MongoDB | instrumentation-mongoose, instrumentation-mongodb, otelmongo | Operation spans with db.system, db.operation |
| Redis | instrumentation-redis, instrumentation-ioredis, otelredis | Command spans with db.system, db.statement |
| gRPC | instrumentation-grpc, otelgrpc | RPC spans with rpc.system, rpc.method |
| Message queues | instrumentation-amqplib, instrumentation-kafkajs | Publish/consume spans with messaging.system |

### Never auto-instrumented — always manual

These boundary types have no auto-instrumentation libraries. They always require
hand-written span code:

- **Third-party SDK calls**: OAuth token verification (Google, Apple, Facebook SDKs),
  payment processing (Stripe SDK), notification services (Twilio, SendGrid SDKs)
- **Custom business logic**: order processing workflows, user onboarding flows,
  data transformation pipelines
- **Email sending**: SMTP via nodemailer, SendGrid API, SES
- **File/blob storage**: S3 operations, GCS operations (unless a specific library exists)
- **Custom RPC protocols**: non-gRPC inter-service communication

---

## Instrument the Unexpected

The goal is not to trace every code path — it's to trace deviations from the happy path.
Errors, retries, degraded behavior, resource exhaustion: these are the signals that matter.

**DO instrument:**

- Errors and exceptions — always, with full context
- Retries and fallbacks — how many times, why, what triggered the fallback
- Cache misses — not hits, misses (they drive downstream load)
- Slow queries — queries that exceed a threshold, not every query
- Circuit breaker state changes — open, half-open, closed transitions
- Rate limit hits — who hit the limit and why
- Degraded responses — when you returned partial data or a cached stale response

**DON'T instrument:**

- Every validation that passes — you don't need a span for "input was valid"
- Cache hits — count these in metrics, they don't need trace context
- Fast queries — a 1ms database call adds span overhead for no value
- Normal state transitions — internal state machines don't need spans
- Internal processing steps — intermediate transformations inside a single operation

**The exception — critical business milestones:**

Always instrument these even on the happy path. They have business and audit value.
Positive confirmation that these succeeded matters as much as knowing when they fail.

- Payment captured
- Order placed
- User account created
- Subscription renewed

---

## Application Boundaries

A span represents a unit of work with a clear start and end at a system boundary.
Create spans at integration points — where your code hands off to another system.

**Valid span boundaries:**

| Boundary Type | Examples |
|--------------|---------|
| HTTP server requests | Incoming API calls, webhook handlers, web page requests |
| HTTP client requests | Outgoing calls to external services, third-party APIs |
| Database operations | SQL queries, NoSQL reads/writes, ORM calls |
| Message queue operations | Publishing a message, consuming from a queue or topic |
| RPC calls | gRPC method calls, JSON-RPC requests |
| Cache operations | Get/set/delete on Redis or Memcached |
| External API calls | Stripe, Twilio, SendGrid, any external provider |
| File I/O | Network filesystems (NFS, S3-mounted), not local disk |

**Anti-patterns — never create spans for:**

- Internal function calls — a helper function is not a boundary
- Utility functions — string formatting, date parsing, validation logic
- Loop iterations — one span per loop, not one span per iteration
- Pure computations — CPU-only work with no I/O has no latency variance to measure
- Memory operations — reading from an in-process cache or map is not a span
- Constructors and destructors — object lifecycle is not a trace boundary

If you find yourself creating spans for functions that only call other functions in the
same process, stop. You're adding overhead and creating noise, not observability.

---

## Why This Matters

The cost of telemetry is not just performance overhead — it's cognitive load.

Every unnecessary span is something an engineer must filter out during an incident.
Every superfluous attribute is a field to ignore while looking for the one that matters.
Bad instrumentation doesn't just fail to help — it actively slows you down when things
are broken and time is critical.

The discipline is: every span and every attribute must answer the question
"Will this help debug a production issue?" If the answer requires more than
two seconds of thought, the answer is no.

Instrument less. Instrument well. Start with the boundaries where systems meet.
