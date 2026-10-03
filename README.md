# OllyGarden Agent Skills

[![skills.sh](https://www.skills.sh/b/ollygarden/skills)](https://www.skills.sh/ollygarden/skills)
[![CLA](https://img.shields.io/badge/CLA-required-blue.svg)](https://github.com/ollygarden/.github/blob/main/CLA.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

OllyGarden Agent Skills are open source skills that carry OllyGarden's opinions on OpenTelemetry into coding agents such as Claude Code, Cursor, Codex, and GitHub Copilot: how to configure and validate the OpenTelemetry Collector, and how to work with the OllyGarden platform. They build on the vendor-neutral facts in the companion [`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills) package, and [Rose](https://ollygarden.com/products/rose), OllyGarden's AI instrumentation agent, uses both. See both packages at [ollygarden.com/resources/agent-skills](https://ollygarden.com/resources/agent-skills).

The skills in this repository follow the standardized [Agent Skills](https://agentskills.io/specification) format.

## Available Skills

| Skill | Description |
|-------|-------------|
| [`ollygarden-cli`](skills/ollygarden-cli/) | Use the `ollygarden` CLI to inspect Rose repositories, findings, and executions alongside telemetry services, insights, analytics, organizations, and webhooks. |
| [`ollygarden-insight-remediation`](skills/ollygarden-insight-remediation/) | Fetch active service insights from the Olive API and apply remediation fixes to the current codebase. |
| [`ollygarden-otel-collector-k8s-daemonset`](skills/ollygarden-otel-collector-k8s-daemonset/) | OllyGarden's opinionated, optimization-first OTel Collector config for a Kubernetes node agent (DaemonSet): drop early at the node, curated receivers, noise/cardinality/cost reduction across logs, metrics, traces. |
| [`ollygarden-otel-collector-config-validation`](skills/ollygarden-otel-collector-config-validation/) | OllyGarden's end-to-end method for validating a collector config: `otelcol validate`, then a real collector in Docker/Podman fed by telemetrygen with a file exporter, asserting that a processor or connector actually transforms, drops, or routes telemetry as intended. |
| [`ollygarden-otel-collector-config-decomposition`](skills/ollygarden-otel-collector-config-decomposition/) | OllyGarden's opinion on when and how to decompose a monolithic OTel Collector config into multiple merged files — and when to leave it alone. Executes the split by concern (deep-merged `--config file:` sources), verifies the merged result is behavior-equivalent, and reports the reasoning, including a deliberate no-op for configs simple enough not to need it. |

## Installation

### skills.sh

Install via [skills.sh](https://skills.sh/docs). Each published skill lives in its own directory
under `skills/` and can be installed individually, for example:

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

### Cursor, Codex, GitHub Copilot, and other agents

The `skills` CLI installs into the coding agents it detects. Pass `-a` to choose one, such as `cursor`, `codex`, or `github-copilot`:

```bash
npx skills add ollygarden/skills -a cursor
```

See the [skills CLI documentation](https://github.com/vercel-labs/skills#supported-agents) for every supported agent.

## Layout

Every published skill is a top-level directory under `skills/` whose name matches the skill's
`name:` field, per the [Agent Skills](https://agentskills.io/specification) directory rule:

```
skills/
├── ollygarden-cli/
├── ollygarden-insight-remediation/
├── ollygarden-otel-collector-k8s-daemonset/
├── ollygarden-otel-collector-config-validation/
└── ollygarden-otel-collector-config-decomposition/
```

All published skill `name:` fields carry an `ollygarden-` prefix to declare ownership in the global
skill namespace. The Collector skills contain OllyGarden's opinions layered on top of upstream
OpenTelemetry facts published in the companion package
[`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills); install
both packages so they can reference upstream skills such as `otel-collector` and `otel-ottl`.

## Deprecated Skills

Retired skills are preserved under [`deprecated/`](deprecated/) for historical reference. They are
not published through the plugin marketplace or included in active skill validation. Use the
companion [`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills)
package for general OpenTelemetry SDK and instrumentation guidance.

## Contributing

Contributions are welcome, including pull requests authored or implemented with AI coding agents.
See [CONTRIBUTING.md](CONTRIBUTING.md) for skill conventions, validation, evaluation evidence, and
pull request expectations, and [docs/preferred-workflow.md](docs/preferred-workflow.md) for the
end-to-end path a change takes through this repository.

Before opening a pull request, run the two validation gates CI runs:

```bash
uv tool install "$(cat bin/skills-ref.requirement)"   # one-time
./bin/validate-skill.sh
./bin/check-skill-inventory.sh
```

CI also link-checks the whole repository. That one needs
[lychee](https://github.com/lycheeverse/lychee) installed; see
[docs/preferred-workflow.md](docs/preferred-workflow.md) for the command if your change touches
links.

First-time contributors sign the organization-wide
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
