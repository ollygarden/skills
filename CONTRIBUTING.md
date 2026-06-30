# Contributing to Skills

Thank you for your interest in contributing!

## Getting Started

1. Fork and clone the repository
2. Create a feature branch from `main`
3. Make your changes
4. Open a pull request

## Adding a Skill

Prefer using the [`skill-creator`](https://github.com/anthropics/skills/tree/main/skill-creator) skill to scaffold and refine new skills rather than authoring them by hand — it walks you through the structure and helps keep skills well-scoped.

Skills live under `skills/<skill-name>/` and must follow the [Agent Skills specification](https://agentskills.io/specification). Each must include a `SKILL.md` with YAML frontmatter (`name` and `description`), where the directory name matches the `name` field. Optional subdirectories: `scripts/`, `references/`, `assets/`.

Validate your skill locally before opening a pull request to confirm it conforms to the spec and activates as intended.

When you add or rename a skill, keep all three registration points in sync: the `skills/<skill-name>/SKILL.md` directory, the `plugins` entry in `.claude-plugin/marketplace.json`, and the table and layout tree in `README.md`.

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/). Format:

```
<type>: <short description>

<optional body>
```

Common types:

- `feat` — new skill or feature
- `fix` — bug fix
- `docs` — documentation only
- `chore` — maintenance, CI, tooling
- `refactor` — code restructuring without behavior change

## Pull Requests

- Keep PRs focused on a single change
- Include a summary and test plan in the PR description
- Update `README.md` if adding or removing a skill
