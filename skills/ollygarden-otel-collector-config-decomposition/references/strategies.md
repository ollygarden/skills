# Decomposition strategies and how to choose

Companion reference for the `ollygarden-otel-collector-config-decomposition` skill. Three
patterns organize a collector config; they combine, and the right one follows the config's
**actual** ownership and change boundaries — not a template. Read
[`mechanics.md`](mechanics.md) for the merge rules the examples below rely on.

## Choosing

| Boundary in your org | Strategy |
|---|---|
| Traces / metrics / logs owned or iterated independently | **By signal pipeline** |
| Separate teams own receivers vs. processors vs. exporters | **By component type** |
| Same structure, values differ per environment | **Environment overlays** (layer on either) |
| One block dominates the file and is independently ownable | **Nested inclusion** (layer on any) |

When several fit, prefer **by signal** — it keeps each pipeline's `processors:` array (the
array-replace caveat) naturally contained in one file.

## By signal pipeline (the usual default)

`common.yaml` holds everything shared by all pipelines, **defined once** — including receivers
that feed all signals (e.g. `otlp`), shared processors (`memory_limiter`, `batch`,
`resourcedetection`, `k8sattributes`), shared exporters, extensions, and `service.telemetry`.
Each signal file is self-contained: its signal-specific receivers + processors, plus its own
`service.pipelines.<signal>` entry.

```
collector/
  common.yaml     # shared receivers/processors/exporters/extensions + service.telemetry
  traces.yaml     # trace-only bits + service.pipelines.traces
  metrics.yaml    # metric-only bits + service.pipelines.metrics
  logs.yaml       # log-only bits + service.pipelines.logs
```

```yaml
# traces.yaml — self-contained for its signal
processors:
  tail_sampling:
    decision_wait: 30s
    policies: [ ... ]

service:
  pipelines:
    traces:
      receivers: [otlp]                       # otlp defined in common.yaml
      processors: [memory_limiter, tail_sampling, batch]
      exporters: [otlp]
```

The three distinct `service.pipelines.<signal>` keys merge into one complete set.

## By component type

A `base.yaml` (service section + extensions, referencing components by name) plus one file per
stage. Fits when platform/observability/SRE teams own different pipeline stages.

```
collector/
  base.yaml         # service.pipelines (the arrays live here, in one file) + extensions
  receivers.yaml
  processors.yaml
  exporters.yaml
```

Keep the `service.pipelines` arrays in `base.yaml` (one file) — see the array-replace caveat.
A change to the batch processor then touches only `processors.yaml`, reviewable in isolation.

## Environment overlays

A base with the full structure, plus small per-environment files that override only what
differs (limits, endpoints, exporters, added debug exporter). Selected at deploy time with an
extra `--config file:` flag. Layers on top of by-signal or by-component.

```
collector/
  base.yaml
  env/
    production.yaml     # bigger memory_limiter, real endpoint, TLS, retry/queue
    staging.yaml
    development.yaml     # small limits, insecure, + debug exporter
```

```bash
# Production                              # Development
otelcol-contrib --config file:base.yaml \    otelcol-contrib --config file:base.yaml \
  --config file:env/production.yaml            --config file:env/development.yaml
```

Overlay caveat: to *add* a debug exporter in dev you must redefine the whole
`service.pipelines.<signal>.exporters` array (arrays replace), e.g. `exporters: [otlp, debug]`.

## Nested inclusion (`${file:}`)

Externalize a single oversized, independently-ownable block — a long tail-sampling policy list,
a big set of Prometheus scrape jobs — into bare-fragment files (see [`mechanics.md`](mechanics.md)
for the bare-fragment shape). This lets a team own one policy and submit a focused change.
**Don't over-apply it:** each include is another file a reader must open, so reserve it for
blocks that are *both* large *and* independently ownable.
