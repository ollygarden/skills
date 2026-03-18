# Contributing to Skills

Thank you for your interest in contributing!

## Getting Started

1. Fork and clone the repository
2. Create a feature branch from `main`
3. Make your changes
4. Open a pull request

## Adding a Skill

Skills live under `skills/<skill-name>/` and must include a `SKILL.md` with YAML frontmatter (`name` and `description`). Optional subdirectories: `scripts/`, `references/`, `assets/`.

After adding a skill, update the table in `README.md`.

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
