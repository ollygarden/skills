---
name: ollygarden-otel-declarative-config
description: Ollygarden's recommended patterns and anti-patterns for OpenTelemetry declarative configuration. Use when reviewing or authoring otel.yaml files, when deciding whether declarative config is right for a project, or when the user asks for "the right way" to configure OpenTelemetry. Triggers on "otel best practices", "otel anti-patterns", "is this otel config correct", "should I use declarative config".
---

# Declarative Configuration Conventions

## The file replaces properties and env vars — not code

Declarative YAML supersedes scattered `otel.*` properties, `-Dotel.*` flags, and
SDK-setting `OTEL_*` variables. It does **not** supersede SDK components registered
through code: `SpanProcessor`s (e.g. an attribute-stripping processor that removes
`url.query`/`url.full`), custom samplers, and other SPI-registered components keep
working alongside the file and stay where they are. When migrating a service to
declarative config, inventory the code-registered components first — each one either
has a schema-supported equivalent (move it) or it does not (keep the code); deleting one
because "everything is YAML now" silently removes the guarantee it enforced.

Two facts make this failure silent:

- **Unrecognized keys under `instrumentation/development` are ignored, not rejected** —
  that subtree is not schema-validated. A misspelled or invented node (including a missing
  experimental `/development` key suffix) parses, boots, and does nothing.
- **A config file that boots proves only that it parsed.** After the migration, re-run the
  behavioral verification for every guarantee the old setup enforced (e.g. a
  marker-value request to prove sensitive data still doesn't export) — never conclude
  from the YAML's contents.

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
| `service.name` | author-time, stable | `${OTEL_SERVICE_NAME:-<literal>}` — literal fallback, standard variable can override |
| `service.namespace` | author-time, stable | literal |
| `service.owner.url` | author-time, stable | literal — the service's repository URL |
| `service.version` | build-time, varies | `OTEL_RESOURCE_ATTRIBUTES` via `attributes_list` |
| `deployment.environment.name` | deploy-time, varies | `OTEL_RESOURCE_ATTRIBUTES` via `attributes_list` |

```yaml
resource:
  attributes:
    # Static — known at author time; the standard variable still wins when set
    - name: service.name
      value: "${OTEL_SERVICE_NAME:-checkout-service}"
    - name: service.namespace
      value: "payments"
    - name: service.owner.url
      value: "https://github.com/acme/checkout-service"
  # Deploy-varying attributes arrive through the STANDARD variable, e.g.
  #   OTEL_RESOURCE_ATTRIBUTES=service.version=1.4.2,deployment.environment.name=production
  attributes_list: ${OTEL_RESOURCE_ATTRIBUTES}
```

**Rules:**

- **Static values** (`service.namespace`, `service.owner.url`, and the `service.name`
  fallback) are hardcoded literals — they are stable per service and must never silently
  degrade when a variable is missing.
- **Deploy-varying values** (`service.version`, `deployment.environment.name`, ...) come
  through the **standard** `OTEL_RESOURCE_ATTRIBUTES` variable into `attributes_list`. Do
  NOT invent custom environment variables (`SERVICE_VERSION`,
  `DEPLOYMENT_ENVIRONMENT_NAME`, ...) for values the standard variables already express —
  the standard variable is the contract every OTel-aware deployment layer, operator, and
  test harness already speaks. A declarative file ignores the environment unless it
  references it, so omitting `attributes_list: ${OTEL_RESOURCE_ATTRIBUTES}` silently
  breaks that contract.
- **Precedence:** entries under `attributes` override `attributes_list`. Never duplicate
  a deploy-varying key under `attributes` — a hardcoded
  `deployment.environment.name: development` clobbers the operator's real environment and
  misfiles every signal the service emits.
- **The env vars are a contract.** `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`, and
  `OTEL_EXPORTER_OTLP_*` must be wired into the runtime (CI build arg, container env,
  k8s manifest). That wiring is the deployment layer's responsibility, not this config
  file's — but the config MUST reference the standard variables so they keep working.
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

### Replacing code-level guarantees with invented YAML nodes

```yaml
# BAD: written to replace a SpanProcessor that stripped url.query. The leaf key
# is missing its experimental /development suffix, so the runtime silently
# ignores it — and the processor it "replaced" is gone. The PII ships.
instrumentation/development:
  general:
    sanitization:
      url:
        sensitive_query_parameters:
          - lastName
```

The schema is not a superset of what code can do (see *The file replaces properties and
env vars — not code*). Before expressing a guarantee in YAML, confirm the exact node in
the selected runtime's schema/source; keep the code component unless a supported
equivalent exists; and re-verify the guarantee behaviorally after the switch.

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
