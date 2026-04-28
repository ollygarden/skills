---
name: ollygarden-otel-declarative-config
description: Ollygarden's recommended patterns and anti-patterns for OpenTelemetry declarative configuration. Use when reviewing or authoring otel.yaml files, when deciding whether declarative config is right for a project, or when the user asks for "the right way" to configure OpenTelemetry. Triggers on "otel best practices", "otel anti-patterns", "is this otel config correct", "should I use declarative config".
---

# Declarative Configuration Conventions

## Why declarative config is the default for new projects

Prefer declarative YAML configuration over scattered `OTEL_*` environment variables and over
programmatic SDK construction:

- It's language-agnostic (same YAML works across Go, Java, JS, etc.)
- It's version-controlled alongside application code
- It expresses things env vars cannot: views, composite samplers, multiple exporters
- It supports `${VAR}` substitution for secrets and environment-specific values

## When to recommend declarative config

Recommend it when the user is setting up the OTel SDK for Go, Java, or JS. These SDKs have
stable or near-stable implementations.

For .NET and Python, fall back to environment variables or programmatic setup — declarative
config is still in development. To check the current per-language status, fetch the SDK
compatibility matrix listed in the `general/declarative-config` reference skill's Sources of Truth.

## Common Patterns

These patterns describe the **shape** of a correct config. For exact field names and
exporter syntax, fetch `examples/otel-sdk-config.yaml` (see the `general/declarative-config`
reference skill's Sources of Truth) — those details vary by schema version.

### One config file, vary with env vars

```yaml
resource:
  attributes:
    - name: deployment.environment.name
      value: "${DEPLOY_ENV:-development}"
tracer_provider:
  sampler:
    parent_based:
      root:
        trace_id_ratio_based:
          ratio: ${SAMPLE_RATE:-1.0}
```

### Secrets via env var substitution

```yaml
# Inside an exporter block (exact field names: see canonical example)
headers:
  - name: api-key
    value: "${API_KEY}"
endpoint: "${OTEL_ENDPOINT}"
```

## Anti-Patterns

### Missing `parent_based` wrapper

```yaml
# BAD: ignores upstream sampling decisions, breaks distributed traces
tracer_provider:
  sampler:
    trace_id_ratio_based:
      ratio: 0.1

# GOOD: respects parent sampling, applies ratio only to root spans
tracer_provider:
  sampler:
    parent_based:
      root:
        trace_id_ratio_based:
          ratio: 0.1
```

### Using `simple` processor in production

```yaml
# BAD: exports synchronously, blocks the application
tracer_provider:
  processors:
    - simple:
        exporter: { ... }

# GOOD: exports asynchronously in batches
tracer_provider:
  processors:
    - batch:
        exporter: { ... }
```

### Hardcoded secrets

```yaml
# BAD: secrets in version control
headers:
  - name: api-key
    value: "sk-1234567890abcdef"
```

### Mixing env vars and config file

```bash
# BAD: OTEL_TRACES_SAMPLER is ignored when OTEL_CONFIG_FILE is set
export OTEL_CONFIG_FILE="/app/otel.yaml"
export OTEL_TRACES_SAMPLER="always_off"  # This has NO effect
```

## Cross-References

- Reference: `otel-declarative-config` skill — schema sources of truth, env-var substitution, configuration precedence.
- Language conventions: `ollygarden-otel-go-setup`, `ollygarden-otel-java-setup`, `ollygarden-otel-js-setup`.
