# Verify behavior-preserving decomposition

A pure decomposition must pass merged validation and resolved equivalence. Captured 2026-07:
`print-config` remains version-sensitive, so confirm the pinned distribution supports it with
`otel-collector`.

## 1. Freeze inputs

Record the exact Collector distribution and version, configuration source order, working directory,
and required environment values. Use the same binary, environment, validation mode, and provider
inputs for the monolith and split. Do not substitute production secrets into review artifacts.

## 2. Validate the complete configurations

Validate the monolith and the complete ordered split set, never a fragment:

```sh
otelcol-contrib validate --config=file:monolith.yaml

otelcol-contrib validate \
  --config=file:common.yaml \
  --config=file:traces.yaml \
  --config=file:metrics.yaml \
  --config=file:logs.yaml
```

Validation instantiates components and compiles expressions. It is necessary, but does not prove
that a rule matches telemetry or that a connector routes it correctly.

## 3. Compare both fully resolved outputs

Run `print-config` for both forms under the frozen inputs. Keep its default redacted mode; an
unredacted artifact can expose credentials and is unnecessary for this comparison.

```sh
otelcol-contrib print-config --mode=redacted \
  --config=file:monolith.yaml > original.resolved.yaml

otelcol-contrib print-config --mode=redacted \
  --config=file:common.yaml \
  --config=file:traces.yaml \
  --config=file:metrics.yaml \
  --config=file:logs.yaml > split.resolved.yaml
```

If the pinned distribution lacks this experimental command, use its supported configuration
resolver; do not claim equivalence from raw concatenation or key inspection.

Parse and recursively compare `original.resolved.yaml` with `split.resolved.yaml`:

- compare all component definitions, extensions, connectors, and the full `service` block;
- ignore map ordering and serialization differences;
- compare sequences order-sensitively, especially pipeline processors;
- permit only separately authorized changes, documented one by one.

Do not compare resolved split output directly with raw monolith YAML. Resolution can add defaults,
expand providers, and redact sensitive fields. For fields hidden by redaction, separately confirm
that both source forms preserve the same provider expression or value source under the frozen
environment; never persist secret values merely to make the diff visible.

## 4. Escalate behavioral questions

Resolved equality proves the refactor preserved configuration structure. It does not prove that a
filter drops the intended records, a transform sets the right field, or a connector routes inputs.
For those claims, hand the unchanged component to `ollygarden-otel-collector-config-validation` and
test matching and non-matching telemetry with two-sided assertions. Name that handoff explicitly in
the decision report; a generic suggestion to test the component does not identify the responsible
workflow.
