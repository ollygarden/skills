# Harness templates

Copy only the production component block unchanged. Customize signal pipelines, instance names, and
input shaping around it. Use a new output directory for every test case.

## Processor

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  # Optional: shape fields telemetrygen cannot set directly.
  transform/setup:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - set(name, "GET /healthz")

  # Paste the component under test verbatim.
  filter/under_test:
    error_mode: ignore
    traces:
      span:
        - 'IsMatch(name, "GET /healthz.*")'

exporters:
  file/result:
    path: /output/result.json
    flush_interval: 200ms

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [transform/setup, filter/under_test]
      exporters: [file/result]
```

Run matching and non-matching filter cases separately. A positive control that survives proves the
Collector received data; the matching case proves the rule drops the intended shape.

## Connector

A connector is an exporter in its source pipeline and a receiver in every destination pipeline.
Give every destination its own file exporter.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

connectors:
  routing/under_test:
    default_pipelines: [traces/default]
    table:
      - context: span
        condition: 'attributes["http.route"] == "/checkout"'
        pipelines: [traces/checkout]

exporters:
  file/checkout: { path: /output/checkout.json, flush_interval: 200ms }
  file/default: { path: /output/default.json, flush_interval: 200ms }

service:
  pipelines:
    traces/in:
      receivers: [otlp]
      exporters: [routing/under_test]
    traces/checkout:
      receivers: [routing/under_test]
      exporters: [file/checkout]
    traces/default:
      receivers: [routing/under_test]
      exporters: [file/default]
```

Send one input per explicit route and one unmatched input. For each marker, assert presence in the
expected file and absence from all others. Metric-producing connectors use a metrics destination;
assert series identity, type, and value rather than mere file presence.
