# Decomposition strategies

Choose from the config's real ownership and change boundaries.

| Boundary | Strategy |
| --- | --- |
| Traces, metrics, and logs change independently | By signal |
| Teams own ingress, processing, and egress stages | By component |
| Structure is shared but environment values differ | Overlay either layout |
| One large block has an independent owner | Nested inclusion |

When boundaries overlap, prefer by signal because each complete pipeline sequence naturally stays
in one file. Use the fewest files that preserve the boundary.

## By signal

```text
collector/
  common.yaml
  traces.yaml
  metrics.yaml
  logs.yaml
```

`common.yaml` defines shared receivers, processors, exporters, extensions, and service telemetry
once. Each signal file defines its signal-specific components and complete
`service.pipelines.<signal>` entry, including all ordered sequences.

## By component

```text
collector/
  base.yaml
  receivers.yaml
  processors.yaml
  exporters.yaml
```

`base.yaml` owns extensions and complete pipeline entries; stage files own component definitions.
This fits stage ownership, but it separates pipeline wiring from definitions, so do not use it when
signal ownership is stronger.

## Environment overlays

```text
collector/
  base.yaml
  env/production.yaml
  env/staging.yaml
```

Load the base first and exactly one environment file last. Keep overlays small and record their
order. A sequence override must restate the entire intended sequence; adding a debug exporter, for
example, requires the full resulting pipeline exporter list.

## Nested inclusion

Externalize only a block that is both large and independently owned, such as a sampling policy set
or Prometheus scrape catalog. Each include adds navigation and working-directory coupling. Read
[`mechanics.md`](mechanics.md) before using it.
