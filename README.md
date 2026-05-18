# Skills

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
└── ollygarden-otel-js-setup/
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

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
