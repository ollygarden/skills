---
name: ollygarden-otel-js-setup
description: Ollygarden's recommended pattern for setting up OpenTelemetry in Node.js services. Covers project structure, which auto-instrumentations to disable, the entry-point ordering, the programmatic NodeSDK fallback, and the setup checklist (no query strings in telemetry, startup/non-request span hygiene, declarative YAML config, standard OTEL_* env vars honored, lean resource with service.instance.id) closed by a required verification report. Use when adding OTel to a Node.js project, structuring telemetry code, or reviewing an existing setup. Triggers on "node otel setup", "NodeSDK pattern", "auto instrumentation node", "url.query", "query parameter PII", "service.instance.id".
---

# JS/Node.js SDK Setup Conventions

## Status decision: declarative vs programmatic

The `@opentelemetry/configuration` package is experimental. Default to declarative config
for new projects. Use the programmatic NodeSDK fallback below if stability is critical or
the project needs runtime configuration that YAML cannot express.

## Setup Checklist — verify every item before you finish

Setup is not done when the SDK boots. Each unchecked item below produces a specific
telemetry-quality finding in production; work through all of them.

- [ ] **Do not export query strings or other user input.** Telemetry must not capture data
  that can carry user input by default, and the query string is exactly that — yet the Node
  HTTP instrumentation (`@opentelemetry/instrumentation-http`, active through
  `auto-instrumentations-node`) exports it out of the box: `url.query` on server spans and
  folded inside `url.full` on client spans under the stable HTTP semantics. **Check which
  semantic-convention mode your installed instrumentation actually emits** — many contrib
  versions still default to the *old* HTTP attributes, where the query rides in `http.target`
  on server spans and inside `http.url` on client spans; redacting only the stable
  `url.query`/`url.full` keys then leaves the marker exposed. Only userinfo credentials are
  redacted by default; everything else — `GET /owners?lastName=Smith`, search terms, tokens
  pasted into links — goes out verbatim (Critical *PII Leakage* finding). Strip it
  **in-process, before it leaves the application** — overwrite or delete whichever attributes
  carry it in your mode (`url.query`/`url.full`, and/or `http.target`/`http.url`) in the HTTP
  instrumentation's own attribute hook (`applyCustomAttributesOnSpan` /
  `startIncomingSpanHook`) or in a span-processor / exporter wrapper that rewrites the
  attribute before export. A Collector `transform`/`redaction` processor is only
  defense-in-depth, never the sole control: the raw value has already crossed the process
  boundary and may sit in in-transit buffers, debug logs, or an alternate export path that
  skips the Collector. The route template (`http.route`,
  `url.path`) already answers "which endpoint"; if a specific parameter is genuinely needed as
  telemetry, capture it deliberately as a bounded, named attribute — never by keeping the raw
  query string. Leave the opt-in header-capture knobs
  (`OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_*`) off for the same reason. Verify by sending a
  request with a known marker value in a query parameter and inspecting the exported span: the
  marker must not appear anywhere.

- [ ] **Keep startup and other non-request work from polluting trace shapes.** Auto
  instrumentation patches `http`, database drivers, and clients process-wide, so any outbound
  call made during boot — a migration, a warm-up HTTP request, a connection-pool probe — is
  emitted as a parentless CLIENT **root** span because no request context is active yet
  (*Root Client Span* finding). Two obligations: (1) either wrap deliberate startup work in an
  explicit application-startup span so those child spans have a parent, or suppress
  instrumentation for it (run it before `startNodeSDK`, or drop init-phase spans with a
  sampler / Collector rule) — do not ship detached CLIENT roots by default; (2) never build
  span names from unbounded input. Custom spans named with an id, a URL, or any per-request
  value (e.g. `tracer.startSpan('job ' + jobId)`) create unbounded span-name cardinality; name
  the span for the operation and put the varying value in a bounded attribute. Verify by
  booting the app and inspecting the first exported traces: no parentless CLIENT roots, and no
  per-request/per-boot identifiers anywhere in span names.

- [ ] **Configure the SDK declaratively — one YAML document, not option sprawl.** A scatter of
  `OTEL_*` flags plus hand-wired `new NodeSDK({...})` exporter/processor code is the
  anti-pattern: operators cannot review or change the telemetry pipeline as a single document
  without a redeploy. Prefer the declarative model — `startNodeSDK()` from
  `@opentelemetry/sdk-node` loads the file named by `OTEL_CONFIG_FILE` through the experimental
  `@opentelemetry/configuration` package (mechanics: `otel-js` skill,
  `references/declarative-setup.md`; YAML conventions: `ollygarden-otel-declarative-config`).
  Keep the programmatic `NodeSDK` fallback only when stability is critical or the config needs
  runtime values YAML cannot express (see the status decision above). **The file replaces
  option/env-based configuration — not code.** Components that must run in code — the
  query-string redaction from the first item, the startup-span policy from the second, the
  disabled `fs`/`dns`/`net` instrumentations — stay in place and are passed to
  `startNodeSDK()`; going declarative does not discharge those items, and every earlier item's
  verification must be re-run after the switch. The file must also preserve the standard
  `OTEL_*` contract via `${ENV}` substitution — the next item spells that out. Verify by
  changing a config value (e.g. the sampler argument or the exporter endpoint) in the YAML and
  confirming behavior changes with no code change and no rebuild.

- [ ] **Honor the standard `OTEL_*` environment variables end-to-end.**
  `OTEL_EXPORTER_OTLP_*`, `OTEL_SERVICE_NAME`, and `OTEL_RESOURCE_ATTRIBUTES` must all take
  effect at runtime. Do not invent custom variables (`SERVICE_VERSION`,
  `DEPLOYMENT_ENVIRONMENT`, ...) for values the standard variables already express, and never
  let a hardcoded default clobber an operator-supplied value. The programmatic `NodeSDK` reads
  these variables directly, but **a declarative YAML loaded via `OTEL_CONFIG_FILE` does not** —
  when the config file is set the SDK stops falling back to the environment, so each standard
  variable must be threaded in explicitly with substitution:

  ```yaml
  resource:
    attributes:
      - name: service.name
        value: "${OTEL_SERVICE_NAME:-my-node-service}"
        type: string
    # standard deploy-time attributes (service.version,
    # deployment.environment.name, ...) arrive through the STANDARD variable:
    attributes_list: "${OTEL_RESOURCE_ATTRIBUTES}"
  ```

  Do not also hardcode a deploy-varying key (e.g. `deployment.environment.name`) under
  `attributes`, or the literal silently wins and misfiles every signal. Point the exporter at
  `${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4318}`. Verify by booting with all three
  standard variables set to non-default values: `OTEL_SERVICE_NAME` and
  `OTEL_RESOURCE_ATTRIBUTES` must land on the exported resource, while the overridden
  `OTEL_EXPORTER_OTLP_ENDPOINT` — a destination, not a telemetry attribute — is confirmed at
  the receiving collector, not on the spans.

- [ ] **Keep the resource lean and add `service.instance.id`.** The Node SDK's default
  detector set (`envDetector`, `processDetector`, `hostDetector`) does **not** include
  `service.instance.id` — the `serviceinstance` detector that would mint one is experimental
  and off by default — so unless you act, every process of a replicated service is
  indistinguishable (*Missing service.instance.id* finding). Add a per-process UUID
  (`crypto.randomUUID()`) alongside `service.version`: programmatically via
  `resourceFromAttributes` (the string key is `service.instance.id`, or `ATTR_SERVICE_INSTANCE_ID`
  from `@opentelemetry/semantic-conventions/incubating`), or in declarative YAML as a resource
  attribute fed a per-process value. Keep the rest of the resource minimal — `service.name`,
  `service.version`, `service.instance.id`, `deployment.environment.name` is the full set. Do
  not enable host/process/OS resource detectors that stamp discouraged `process.*` / `os.*`
  attributes (*Discouraged Resource Attribute* finding). Verify by inspecting the exported
  resource: `service.instance.id` is present and differs between two separate process starts,
  and no `process.*`/`os.*` attributes are attached.

## Required: Verification Report

Setup is not complete until you produce this report. It is a table with one row per
checklist item above. Fill each row with artifacts from THIS run — the marker value you
sent, an excerpt of the exported span dump, a trace id, the config value you changed.
Never a restatement of the requirement, never a bare "done".

The table below is an **illustrative example, not a report you can submit**: every value in
it is a placeholder showing the expected *shape* of evidence. Replace every cell with your
own run's artifacts. If you did not run a check, write `GAP — not run` in that row and
leave it visible — a missing or hand-waved row is itself a finding.

Example (illustrative values — replace every cell with your own run's evidence):

| Item | Check performed | Observed evidence |
| -- | -- | -- |
| No query strings exported | `GET /owners?lastName=MARKER_7f3a` → inspected exported span (check which semconv mode: `url.query`/`url.full` vs legacy `http.target`/`http.url`) | query attribute absent; `MARKER_7f3a` nowhere in span dump (trace `4bf9...`) |
| Startup / non-request span hygiene | Booted app, inspected first exported traces | No parentless CLIENT roots; startup DB call is child of `app.startup` span; no ids in span names |
| SDK configured declaratively | Changed sampler arg in `configs/otel.yaml`, restarted without rebuild | Sampling ratio changed on exported spans; no code edit needed |
| Standard `OTEL_*` honored | Booted with `OTEL_SERVICE_NAME`/`OTEL_RESOURCE_ATTRIBUTES` set to non-defaults, and `OTEL_EXPORTER_OTLP_ENDPOINT` pointed at a marker collector | `service.name`/`deployment.environment.name` carry the supplied values on the exported resource; the marker collector's log / receipt confirms telemetry arrived at the overridden endpoint (the endpoint is a destination, evidenced there, not on the spans) |
| Lean resource + `service.instance.id` | Dumped resource from two separate process starts | `service.instance.id` present and differs across starts; no `process.*`/`os.*` attrs |

A row you cannot fill with observed evidence is a visible gap — that item is not done.
Do not delete the row, copy these example values, or write "N/A" to hide it; go run the
check and record what you actually saw.

## Dependencies

```bash
npm install @opentelemetry/api @opentelemetry/sdk-node @opentelemetry/configuration
npm install @opentelemetry/auto-instrumentations-node
npm install @opentelemetry/semantic-conventions
```

Fetch the latest versions of these packages (see the `otel-js` skill's Sources of Truth)
and pin them in `package.json` as appropriate for your project.

## Project Structure

```
src/
├── telemetry/
│   ├── constants.ts      # Service scope and telemetry constants
│   ├── setup.ts          # SDK initialization
│   └── index.ts          # Re-exports
├── index.ts              # App entry point (imports telemetry first)
configs/
└── otel.yaml             # Declarative configuration
```

## Instrumentation File (`src/telemetry/setup.ts`)

```typescript
import { startNodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

// startNodeSDK loads OTEL_CONFIG_FILE and registers the configured providers.
// new NodeSDK(...) is the separate programmatic path and does not load the file.
export const sdk = startNodeSDK({
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-fs': { enabled: false },
      '@opentelemetry/instrumentation-dns': { enabled: false },
      '@opentelemetry/instrumentation-net': { enabled: false },
    }),
  ],
});
```

## Entry Point (`src/index.ts`)

```typescript
// IMPORTANT: Import and start telemetry BEFORE any other imports
import { sdk } from './telemetry/setup';

import { app } from './app';

const PORT = process.env.PORT ?? 3000;
const server = app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});

process.on('SIGTERM', () => {
  server.close(async () => {
    await sdk.shutdown();
    process.exit(0);
  });
});
```

## Fallback: Programmatic NodeSDK Setup

If declarative config is not suitable (e.g., need dynamic runtime config or older SDK version),
use programmatic setup:

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { BatchLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { resourceFromAttributes, envDetector } from '@opentelemetry/resources';
import { ATTR_SERVICE_INSTANCE_ID } from '@opentelemetry/semantic-conventions/incubating';
import { randomUUID } from 'node:crypto';

// service.name / service.version / deployment.environment.name arrive through the standard
// OTEL_SERVICE_NAME and OTEL_RESOURCE_ATTRIBUTES variables (applied by envDetector below);
// do not invent custom vars for them. Mint only the per-process service.instance.id that no
// default detector provides.
const resource = resourceFromAttributes({
  [ATTR_SERVICE_INSTANCE_ID]: randomUUID(),
});

export const sdk = new NodeSDK({
  resource,
  // Only envDetector: honor the OTEL_* contract without stamping discouraged
  // process.* / os.* attributes from the default process/host detectors.
  resourceDetectors: [envDetector],
  traceExporter: new OTLPTraceExporter(),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter(),
    exportIntervalMillis: 30_000,
  }),
  logRecordProcessors: [
    new BatchLogRecordProcessor(new OTLPLogExporter()),
  ],
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-fs': { enabled: false },
      '@opentelemetry/instrumentation-dns': { enabled: false },
      '@opentelemetry/instrumentation-net': { enabled: false },
    }),
  ],
});
```

## Key Details

- **Disable noisy instrumentations**: `fs`, `dns`, and `net` instrumentations generate high volumes of low-value spans. Disable them unless specifically needed.
- **SIGTERM handler**: Always register a shutdown handler to flush buffered telemetry before the process exits.

## Cross-References

- Reference: `otel-js` skill — `references/declarative-setup.md` for the package version fetch table, activation, ESM/CJS rules, v2.0 migration facts.
- General conventions: `ollygarden-otel-declarative-config` — anti-patterns and common YAML patterns.
