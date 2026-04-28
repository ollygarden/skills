# Skills

Public OllyGarden AI skills for [Rose](https://github.com/ollygarden/rose) and the broader OllyGarden ecosystem. Skills are self-contained folders that package instructions, scripts, and resources for AI coding agents.

The skills in this repository follow the standardized [Agent Skills](https://agentskills.io/specification) format.

## Layout

Skills are grouped by topic under `skills/`:

```
skills/
├── ollygarden/                       # OllyGarden's own products
│   └── insight-remediation/
└── otel/                             # OllyGarden's opinions on OpenTelemetry
    ├── general/
    │   ├── declarative-config/
    │   ├── manual-instrumentation/
    │   └── sdk-setup/
    ├── go/setup/
    ├── java/setup/
    └── js/setup/
```

All skill `name:` fields carry an `ollygarden-` prefix to declare ownership in the global skill namespace. Skills under `otel/` are OllyGarden's opinions layered on top of upstream OpenTelemetry facts published in the companion package [`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills); install both packages so the OTel opinion skills can reference the upstream `otel-semantic-conventions`, `otel-sdk-versions`, etc.

## Installation

### Claude Code

1. Register the repository as a plugin marketplace:

```
/plugin marketplace add ollygarden/skills
```

2. Install a skill:

```
/plugin install <skill-name>@skills
```

## Available Skills

| Skill | Description |
|-------|-------------|
| [`ollygarden-insight-remediation`](skills/ollygarden/insight-remediation/) | Fetch active service insights from the Olive API and apply remediation fixes to the current codebase. |
| [`ollygarden-otel-declarative-config`](skills/otel/general/declarative-config/) | OllyGarden's declarative-first OpenTelemetry conventions: when to use YAML config, anti-patterns, common patterns. |
| [`ollygarden-manual-instrumentation`](skills/otel/general/manual-instrumentation/) | OllyGarden's manual instrumentation rules: choose runtime boundaries and signals, apply semantic conventions, handle propagation, control cardinality, verify the result. |
| [`ollygarden-sdk-setup`](skills/otel/general/sdk-setup/) | OllyGarden's OpenTelemetry SDK setup defaults: providers, OTLP exporters, batching/periodic processors, propagators, transport. |
| [`ollygarden-otel-go-setup`](skills/otel/go/setup/) | OllyGarden's recommended Go OTel setup pattern: project structure, Providers struct, runtime attributes, zap log bridge. |
| [`ollygarden-otel-java-setup`](skills/otel/java/setup/) | OllyGarden's recommended Java OTel setup: Javaagent vs Spring Boot Starter vs autoconfigure decision tree, BOM dependency pattern. |
| [`ollygarden-otel-js-setup`](skills/otel/js/setup/) | OllyGarden's recommended Node.js OTel setup: project structure, instrumentation choices, entry-point ordering. |

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
