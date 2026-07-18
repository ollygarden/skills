# OllyGarden Agent Skills

[![CLA](https://img.shields.io/badge/CLA-required-blue.svg)](https://github.com/ollygarden/.github/blob/main/CLA.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Public OllyGarden AI skills for [Rose](https://github.com/ollygarden/rose) and the broader OllyGarden ecosystem. Skills are self-contained folders that package instructions, scripts, and resources for AI coding agents.

The skills in this repository follow the standardized [Agent Skills](https://agentskills.io/specification) format.

## Installation

### skills.sh

Install via [skills.sh](https://skills.sh/docs). Each skill lives in its own directory under `skills/` and can be installed individually, for example:

```
npx skills add https://github.com/ollygarden/skills/tree/main/skills/ollygarden-cli
```

### Claude Code

1. Register the repository as a plugin marketplace:

```
/plugin marketplace add ollygarden/skills
```

2. Install a skill:

```
/plugin install <skill-name>@skills
```

## Layout

Every skill is a top-level directory under `skills/` whose name matches the skill's `name:` field, per the [Agent Skills](https://agentskills.io/specification) directory rule:

```
skills/
├── ollygarden-cli/
├── ollygarden-insight-remediation/
├── ollygarden-otel-declarative-config/
├── ollygarden-otel-instrumentation-planning/
├── ollygarden-otel-manual-instrumentation/
├── ollygarden-otel-sdk-setup/
├── ollygarden-otel-go-setup/
├── ollygarden-otel-java-setup/
├── ollygarden-otel-js-setup/
├── ollygarden-otel-collector-k8s-daemonset/
├── ollygarden-otel-collector-config-validation/
└── ollygarden-otel-collector-config-decomposition/
```

All skill `name:` fields carry an `ollygarden-` prefix to declare ownership in the global skill namespace. The `ollygarden-otel-*` skills are OllyGarden's opinions layered on top of upstream OpenTelemetry facts published in the companion package [`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills); install both packages so the OTel opinion skills can reference the upstream `otel-semantic-conventions`, `otel-sdk-versions`, etc.

## Available Skills

| Skill | Description |
|-------|-------------|
| [`ollygarden-cli`](skills/ollygarden-cli/) | Use the `ollygarden` CLI to query services, insights, analytics, organizations, and manage webhooks from the terminal. |
| [`ollygarden-insight-remediation`](skills/ollygarden-insight-remediation/) | Fetch active service insights from the Olive API and apply remediation fixes to the current codebase. |
| [`ollygarden-otel-declarative-config`](skills/ollygarden-otel-declarative-config/) | OllyGarden's declarative-first OpenTelemetry conventions: when to use YAML config, anti-patterns, common patterns. |
| [`ollygarden-otel-instrumentation-planning`](skills/ollygarden-otel-instrumentation-planning/) | Plan Minimal Viable Instrumentation for a codebase: identify boundaries, classify them as auto vs manual, choose signals, plan attributes with cardinality awareness. |
| [`ollygarden-otel-manual-instrumentation`](skills/ollygarden-otel-manual-instrumentation/) | OllyGarden's manual instrumentation rules: choose runtime boundaries and signals, apply semantic conventions, handle propagation, control cardinality, verify the result. |
| [`ollygarden-otel-sdk-setup`](skills/ollygarden-otel-sdk-setup/) | OllyGarden's OpenTelemetry SDK setup defaults: providers, OTLP exporters, batching/periodic processors, propagators, transport. |
| [`ollygarden-otel-go-setup`](skills/ollygarden-otel-go-setup/) | OllyGarden's recommended Go OTel setup pattern: project structure, Providers struct, runtime attributes, zap log bridge. |
| [`ollygarden-otel-java-setup`](skills/ollygarden-otel-java-setup/) | OllyGarden's recommended Java OTel setup: Javaagent vs Spring Boot Starter vs autoconfigure decision tree, BOM dependency pattern. |
| [`ollygarden-otel-js-setup`](skills/ollygarden-otel-js-setup/) | OllyGarden's recommended Node.js OTel setup: project structure, instrumentation choices, entry-point ordering. |
| [`ollygarden-otel-collector-k8s-daemonset`](skills/ollygarden-otel-collector-k8s-daemonset/) | OllyGarden's opinionated, optimization-first OTel Collector config for a Kubernetes node agent (DaemonSet): drop early at the node, curated receivers, noise/cardinality/cost reduction across logs, metrics, traces. |
| [`ollygarden-otel-collector-config-validation`](skills/ollygarden-otel-collector-config-validation/) | OllyGarden's end-to-end method for validating a collector config: `otelcol validate`, then a real collector in Docker/Podman fed by telemetrygen with a file exporter, asserting that a processor or connector actually transforms, drops, or routes telemetry as intended. |
| [`ollygarden-otel-collector-config-decomposition`](skills/ollygarden-otel-collector-config-decomposition/) | OllyGarden's opinion on when and how to decompose a monolithic OTel Collector config into multiple merged files — and when to leave it alone. Executes the split by concern (deep-merged `--config file:` sources), verifies the merged result is behavior-equivalent, and reports the reasoning, including a deliberate no-op for configs simple enough not to need it. |

## Contributing

Contributions are welcome, including pull requests authored or implemented with AI coding agents.
See [CONTRIBUTING.md](CONTRIBUTING.md) for skill conventions, validation, evaluation evidence, and
pull request expectations. First-time contributors sign the organization-wide
[OllyGarden CLA](https://github.com/ollygarden/.github/blob/main/CLA.md) through the pull request
bot.

## Community and support

- [Support](SUPPORT.md) — where to report defects, propose skills, and ask focused questions.
- [Governance](https://github.com/ollygarden/.github/blob/main/GOVERNANCE.md) — organization-wide project roles and decision-making.
- [Code of Conduct](https://github.com/ollygarden/.github/blob/main/CODE_OF_CONDUCT.md) — the conduct standard and private incident reporting.
- [Security policy](https://github.com/ollygarden/skills/security/policy) — supported versions and private vulnerability reporting.
- [Contributor License Agreement](https://github.com/ollygarden/.github/blob/main/CLA.md) — organization-wide contribution terms and signing instructions.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
