# Skills

Public OllyGarden AI skills for [Rose](https://github.com/ollygarden/rose) and the broader OllyGarden ecosystem. Skills are self-contained folders that package instructions, scripts, and resources for AI coding agents.

The skills in this repository follow the standardized [Agent Skills](https://agentskills.io/specification) format.

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
| [insight-remediation](skills/insight-remediation/) | Fetch active service insights from the Olive API and apply remediation fixes to the current codebase |

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
