# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What this repository is

A catalog of **Agent Skills** (per the [agentskills.io](https://agentskills.io/specification) spec) published by OllyGarden. There is no application, build step, test suite, or linter — every change is to Markdown and YAML files that AI agents consume. "Correctness" means a skill is well-scoped, accurate, and registered in all the right places.

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

## Conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat`, `fix`, `docs`, `chore`, `refactor`). New skills are typically `feat`.
- `local/` is gitignored — used for scratch/research notes, never published.
- A skill `description` is the trigger surface: it should enumerate concrete user phrasings ("Triggers on ...") so agents activate it reliably. Mirror the existing skills' description style.

## Documentation and compatibility checks

For repository-guidance changes, run these checks from the repository root.
Set `BASE_SHA` to the pull request base commit when checking an already
committed branch diff.

```bash
test -f AGENTS.md
test ! -L AGENTS.md
test -L CLAUDE.md
test -e CLAUDE.md
test "$(readlink CLAUDE.md)" = AGENTS.md
cmp -s AGENTS.md CLAUDE.md
test ! -e .agents/skills
test ! -L .agents/skills
test ! -e .claude/skills
test ! -L .claude/skills
git diff --check
test -z "${BASE_SHA:-}" || git diff --check "${BASE_SHA}...HEAD"
perl -MFile::Basename=dirname -MFile::Spec -ne 'while (/\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)/g) { $target = $1; next if $target =~ m{^(?:https?://|mailto:)}; $path = File::Spec->catfile(dirname($ARGV), $target); die "$ARGV: missing $target\n" unless -e $path }' AGENTS.md README.md CONTRIBUTING.md
```
