---
name: ollygarden-otel-declarative-config
description: OllyGarden's review policy for OpenTelemetry declarative YAML. Use for "should I use declarative config?", "review this otel.yaml against OllyGarden conventions", or "what are OllyGarden's config anti-patterns?" Use with the relevant language setup skill when a runtime is known. Not for schema keys, file-format versions, activation, SDK support, or general SDK wiring; use `otel-declarative-config` and the language skills.
---

# Declarative configuration conventions

This skill owns OllyGarden policy, not versioned OpenTelemetry syntax. Use
`otel-declarative-config` for schema, substitution, precedence, and the compatibility matrix; use
the relevant upstream language skill and `ollygarden-otel-*-setup` skill for released activation
and language-specific resource policy. Upstream support status last checked 2026-07.

## Decision gate

Before recommending, reviewing, or generating a file:

1. Identify the exact runtime, package/agent, and version that will parse it.
2. Ask `otel-declarative-config` and the relevant language skill whether every required feature is
   released, how the file is activated, and which `file_format` and fields that parser accepts.
3. Prefer declarative config only when that support is adequate and the user accepts any
   experimental dependency. Otherwise preserve the current env-var or programmatic setup.

Do not maintain a language-support table here or apply a blanket Python fallback. Ask
`otel-declarative-config` and `otel-python` for current Python package, activation, schema, and
support details. Do not recommend declarative YAML for .NET until its upstream skill reports
released support.

## Migration gate: settings are not arbitrary code

Inventory code-registered processors, samplers, detectors, instrumentations, and other guarantees
before migration. Move one only when the selected runtime has a verified declarative equivalent;
otherwise keep it in code. Reviewing or adding a file does not authorize deleting code controls.
If the user or migration diff says a control existed but the current snapshot no longer shows its
registration, treat it as a claimed guarantee: inspect history or ask for the before-state instead
of dismissing it as unused.

Never replace a working control with a guessed implementation-specific YAML node. Some experimental
namespaces may ignore unknown keys, so successful parsing or startup proves only that the file
loaded. Re-run the behavioral check for every migrated guarantee—for sensitive-data controls, send
a unique marker and prove it is absent from exported telemetry.

## OllyGarden policy

Apply these rules after the runtime gate:

### One configuration model

- Keep SDK settings in the file. Do not assume independent SDK-setting `OTEL_*` variables merge
  with file mode; exact precedence and automatic loading are runtime-specific.
- Preserve standard deployment inputs through explicit substitution when required:
  `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`, and `OTEL_EXPORTER_OTLP_*`. Do not invent
  project-specific replacements for values already covered by those contracts.
- Keep secrets external and reference them through supported substitution. Never commit a secret.

### Resource identity without clobbering deployment values

- Ensure a stable `service.name`; use `service.namespace` only when the organization has a
  meaningful namespace. `service.owner.url` is not a universal OpenTelemetry requirement.
- Let the relevant language setup skill decide its lean resource set. Do not copy a generic list
  over a language-specific policy.
- Treat version and environment as deployment/build values. Never duplicate a deploy-varying key
  in a higher-precedence static block where it can overwrite the operator's value.
- Never hardcode one `service.instance.id` for every replica. Generate or inject a per-process
  value when the selected SDK does not provide one.
- Do not hardcode SDK-, process-, host-, container-, or Kubernetes-detected attributes.

### Sampling and suppression

- Preserve upstream sampling decisions with parent-based behavior. Verify the exact sampler shape
  and support in the selected runtime; never emit composite or rule-routing YAML from memory.
- Do not default production to full sampling—or silently choose any ratio—when the instrumentation
  plan or user has not supplied a policy.
- Endpoints marked excluded by the instrumentation plan must not produce exported spans. Choose a
  mechanism supported by the exact runtime/version and prove it with probe traffic. Leave the
  mechanism as an explicit gap when support is absent.

### Production export

- Prefer batch processing in production; synchronous/simple export is for narrow test scenarios.
- Keep exporter endpoints and headers externally configurable through the verified file model.

## Review output

Return only the applicable findings; do not introduce resource, sampling, exporter, or other
rewiring that the request did not put in scope. For unresolved versioned facts, name
`otel-declarative-config` and the exact relevant language/setup skill rather than citing vague
"upstream docs."

When applicable, report:

1. Runtime/version and support evidence consulted.
2. Existing code guarantees and whether each stays, moves, or remains unresolved.
3. Policy findings: configuration model, resources, sampling/suppression, secrets, and batching.
4. Exact upstream facts still needed; do not invent YAML to fill a gap.
5. Behavioral verification for every changed guarantee, including markers and expected evidence.

A file that parses with no errors is not a completed migration.
