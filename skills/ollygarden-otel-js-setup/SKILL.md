---
name: ollygarden-otel-js-setup
description: Ollygarden's recommended pattern for setting up OpenTelemetry in Node.js services. Covers project structure, which auto-instrumentations to disable, the entry-point ordering, and the programmatic NodeSDK fallback. Use when adding OTel to a Node.js project, structuring telemetry code, or reviewing an existing setup. Triggers on "node otel setup", "NodeSDK pattern", "auto instrumentation node".
---

# JS/Node.js SDK Setup Conventions

## Status decision: declarative vs programmatic

The `@opentelemetry/configuration` package is experimental. Default to declarative config
for new projects. Use the programmatic NodeSDK fallback below if stability is critical or
the project needs runtime configuration that YAML cannot express.

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
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

// When OTEL_CONFIG_FILE is set, NodeSDK reads config from that file.
// Exporters, processors, samplers, and resource are all configured via YAML.
export const sdk = new NodeSDK({
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
sdk.start();

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
import { resourceFromAttributes } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';

const resource = resourceFromAttributes({
  [ATTR_SERVICE_NAME]: 'my-service',
  [ATTR_SERVICE_VERSION]: process.env.SERVICE_VERSION ?? '0.0.0',
});

export const sdk = new NodeSDK({
  resource,
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
