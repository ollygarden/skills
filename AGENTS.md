# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What this repository is

A catalog of **Agent Skills** (per the [agentskills.io](https://agentskills.io/specification) spec) published by OllyGarden. There is no application and no build step: the product is the skills themselves, Markdown and YAML that AI agents consume. Around them sits repository tooling — the gate scripts in `bin/`, the workflows and lychee config in `.github/`, and the JSON that registers each skill — which is where the shell, TOML, and JSON in this repository live. "Correctness" for a skill means well-scoped, accurate, and registered in all the right places, which two scripts under `bin/` check.

## Preferred workflow

Whenever a change adds, renames, moves, or removes a skill, or alters a skill's instructions, thresholds, or safety language, follow [`docs/preferred-workflow.md`](docs/preferred-workflow.md). Typo and prose fixes go straight to a PR, unless they touch `SKILL.md` frontmatter or behavior-bearing instructions — a `description:` edit changes when a skill triggers.

## Architecture

Each skill is a self-contained directory under `skills/<skill-name>/`:

- `SKILL.md` (required) — YAML frontmatter (`name`, `description`, optional `license`, `compatibility`, `metadata`) followed by the instruction body.
- `scripts/` (optional) — helper or validation scripts.
- `references/` (optional) — supporting docs the SKILL.md links to for detail it doesn't inline.
- `assets/` (optional) — static files used by the skill.

Two hard rules that are easy to get wrong:

1. **The directory name must equal the `name:` field** in its `SKILL.md` (spec directory rule).
2. **All skill `name:` fields carry an `ollygarden-` prefix** to claim ownership in the global skill namespace.

### Skill layering

The `ollygarden-otel-*` skills deliberately contain only OllyGarden's *opinions*. They reference upstream OpenTelemetry *facts* (semantic conventions, SDK versions, component config keys, OTTL syntax) that live in the companion package [`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills) — e.g. `otel-semantic-conventions`, `otel-sdk-versions`, `otel-collector`, `otel-ottl`. When editing an opinion skill, point at the upstream skill for facts rather than duplicating them. Some skills also hand off to each other (e.g. `ollygarden-cli` defers *applying* fixes to `ollygarden-insight-remediation`).

## Adding or renaming a skill — keep three places in sync

A new skill is only "registered" when it appears in **all** of these. Missing any one is the most common defect:

1. The directory `skills/<name>/` with a `SKILL.md`.
2. The `plugins` array in `.claude-plugin/marketplace.json` (`name` + `source: ./skills/<name>`).
3. The "Available Skills" table **and** the layout tree in `README.md`.

`./bin/check-skill-inventory.sh` fails the build on any drift between those, in both directions, so run it rather than eyeballing the lists.

## Validation

Two scripts, both run in CI by `.github/workflows/validate.yml`:

- `./bin/validate-skill.sh [skill-dir ...]` — Agent Skills spec conformance (delegated to `skills-ref`) plus the house rules: `SKILL.md` under 500 lines and the `ollygarden-` name prefix. Needs a one-time `uv tool install "$(cat bin/skills-ref.requirement)"`.

  The line cap exists because a `SKILL.md` is loaded in full on every trigger, so each line is context paid for at every activation; detail that isn't needed at trigger time belongs in `references/`, read on demand. A skill near the cap is usually two skills, or one with a reference not yet extracted — don't raise the number.
- `./bin/check-skill-inventory.sh` — the three registration points above.

A third workflow, `.github/workflows/link-check.yml`, runs [lychee](https://github.com/lycheeverse/lychee) over every Markdown and YAML file on pull requests and weekly. Example and unreachable hosts are excluded in `.github/lychee.toml`; add an exclusion there with a reason rather than dropping a broken link.

## Conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat`, `fix`, `docs`, `chore`, `refactor`). New skills are typically `feat`.
- `local/` and `.claude/` are gitignored — scratch notes, research, and agent session state, never published.
- A skill `description` is the trigger surface: it should enumerate concrete user phrasings ("Triggers on ...") so agents activate it reliably. Mirror the existing skills' description style.
- **Harness evidence is required** for any PR that adds or substantively changes a skill: the same representative prompt(s) run on a frontier model in three arms — target skill withheld, current `origin/main` skill, and the proposed PR skill. The `origin/main` arm is the one that catches a regression in a skill that already ships; for a brand-new skill it has no revision to name (`Not present`) and is the same configuration as the withheld arm, so it needs no extra runs. Report the arms in the table in `.github/PULL_REQUEST_TEMPLATE.md`, with links to **sanitized** transcripts — redact credentials, tokens, customer data, and private repository content before posting, or summarize the run instead. `CONTRIBUTING.md` is the source of truth.
