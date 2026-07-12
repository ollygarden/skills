---
name: ollygarden-otel-declarative-config
description: Ollygarden's recommended patterns and anti-patterns for OpenTelemetry declarative configuration. Use when reviewing or authoring otel.yaml files, when deciding whether declarative config is right for a project, or when the user asks for "the right way" to configure OpenTelemetry. Triggers on "otel best practices", "otel anti-patterns", "is this otel config correct", "should I use declarative config".
---

# Declarative Configuration Conventions

## Why declarative config is the default for new projects

Prefer declarative YAML configuration over scattered `OTEL_*` environment variables and over
programmatic SDK construction:

- It uses a shared schema across languages, subject to each runtime's released support matrix
- It's version-controlled alongside application code
- It expresses things env vars cannot: views, composite samplers, multiple exporters
- It supports `${VAR}` substitution for secrets and environment-specific values

## When to recommend declarative config

Recommend it when the selected Go, Java, or JS runtime release supports the configuration
features the project needs. Several implementations and activation APIs remain experimental,
so verify the exact runtime and version first.

For .NET and Python, fall back to environment variables or programmatic setup — declarative
config is still in development. To check the current per-language status, fetch the SDK
compatibility matrix listed in the `otel-declarative-config` reference skill's Sources of Truth.

## Common Patterns

These patterns describe the **shape** of a correct config. For exact field names and
exporter syntax, fetch `examples/otel-sdk-config.yaml` (see the `otel-declarative-config`
reference skill's Sources of Truth) — those details vary by schema version.

### Resource attributes

Every config MUST set these. They identify the service across all signals; without them
telemetry reports as `unknown_service` and cannot be grouped or owned.

| Attribute | Source | How |
|---|---|---|
| `service.name` | author-time, stable | literal |
| `service.namespace` | author-time, stable | literal |
| `service.owner.url` | author-time, stable | literal — the service's repository URL |
| `service.version` | build-time, varies | `${SERVICE_VERSION:-unknown}` |
| `deployment.environment.name` | deploy-time, varies | `${DEPLOYMENT_ENVIRONMENT_NAME:-unknown}` |

```yaml
resource:
  attributes:
    # Static — known at author time, identical across every deploy
    - name: service.name
      value: "checkout-service"
    - name: service.namespace
      value: "payments"
    - name: service.owner.url
      value: "https://github.com/acme/checkout-service"
    # Injected — varies per build / environment
    - name: service.version
      value: "${SERVICE_VERSION:-unknown}"
    - name: deployment.environment.name
      value: "${DEPLOYMENT_ENVIRONMENT_NAME:-unknown}"
```

**Rules:**

- **Static values** (`service.name`, `service.namespace`, `service.owner.url`) are
  hardcoded — they are stable per service. Do NOT route them through env vars; a missing
  var silently degrades the value (e.g. to `unknown_service`).
- **Injected values** (`service.version`, `deployment.environment.name`) use
  `${VAR:-default}`. Declarative config cannot compute values — the env var must be
  supplied at build/deploy time. Always include a `:-default` so the attribute is never empty.
- **The env vars are a contract.** `SERVICE_VERSION` and `DEPLOYMENT_ENVIRONMENT_NAME`
  must be wired into the runtime (CI build arg, container env, k8s manifest). That wiring
  is the deployment layer's responsibility, not this config file's — but the config MUST
  list which vars it expects.
- **Do NOT hardcode `service.instance.id`.** Generate or inject a unique value per process when
  the selected SDK does not do so automatically. A shared literal makes every replica report
  the same id and corrupts per-instance metrics.
- **Do NOT set `telemetry.sdk.*`, host, container, k8s, or process attributes.** Resource
  detectors populate these automatically. Hardcoding produces wrong data.

### One config file, vary with env vars

```yaml
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

### Dropping health-check / probe spans

When the instrumentation plan marks endpoints as `excluded` (health, readiness, and
liveness probes — see `ollygarden-otel-instrumentation-planning`), the declarative
mechanism is a **rule-based routing sampler that drops matching spans**. Do NOT reach for
`OTEL_INSTRUMENTATION_*` exclude-path env vars as a second configuration channel unless the
selected runtime explicitly documents how they combine with file configuration.

Nest a rule-based routing sampler as the `root` of `parent_based`, keeping your normal
ratio sampler as its fallback:

```yaml
tracer_provider:
  sampler:
    parent_based:
      root:
        rule_based_routing:
          fallback_sampler:           # used when no rule matches
            trace_id_ratio_based:
              ratio: ${SAMPLE_RATE:-1.0}
          span_kind: SERVER           # only inbound server spans
          rules:
            - action: DROP            # DROP or RECORD_AND_SAMPLE
              attribute: url.path     # match the request path
              pattern: /health.*    # align with the plan's probe path list (e.g /actuator /health /ready etc.)
```

**Rules:**

- Nest inside `parent_based.root` so only root spans are evaluated — upstream sampling
  decisions still propagate to downstream services.
- `span_kind: SERVER` keeps client/producer/consumer spans untouched.
- Align `pattern` with the exclusion path list in the instrumentation plan
  (`/health`, `/healthz`, `/actuator/*`, etc.).
- Availability is per-runtime — confirm the composite/rule-based sampler is supported by
  the target SDK or agent, and fetch exact field names from the canonical example (see the
  `otel-declarative-config` reference skill's Sources of Truth). For language-specific
  availability and agent details, see the relevant `ollygarden-otel-*-setup` skill.

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
# BAD: assuming OTEL_* knobs merge predictably with a config file.
export OTEL_CONFIG_FILE="/app/otel.yaml"
export OTEL_TRACES_SAMPLER="always_off"              # precedence varies by runtime
export OTEL_INSTRUMENTATION_HTTP_EXCLUDE_PATTERNS="" # do not assume this merges with the file
```

Configuration precedence and automatic file loading are runtime-specific. Do not mix an
`OTEL_CONFIG_FILE` deployment with separate SDK-setting `OTEL_*` variables unless the selected
runtime documents that combination. Keep SDK settings in the config model; reserve environment
variables for `${VAR}` substitution inside it. Health-check exclusion becomes the
`rule_based_routing` sampler above when that sampler is supported, not a second configuration
channel.

## Cross-References

- Reference: `otel-declarative-config` skill — schema sources of truth, env-var substitution, configuration precedence.
- Language conventions: `ollygarden-otel-go-setup`, `ollygarden-otel-java-setup`, `ollygarden-otel-js-setup`.
