# Contributing to OllyGarden Skills

Thank you for your interest in contributing!

By participating, you agree to follow OllyGarden's organization-wide
[Code of Conduct](https://github.com/ollygarden/.github/blob/main/CODE_OF_CONDUCT.md). Report
suspected vulnerabilities privately under the inherited
[security policy](https://github.com/ollygarden/skills/security/policy), not through a public issue
or pull request. For questions and issue-routing guidance, see [SUPPORT.md](SUPPORT.md).

## Contributions from AI coding agents

We accept and encourage pull requests authored or implemented with AI coding agents. Agent-authored
changes are held to the same bar as any other contribution:

- A human contributor must own the pull request, review the agent's output, and be able to respond
  to review feedback.
- Disclose agent involvement in the pull request description.
- The evaluation requirement below applies regardless of who or what wrote the change.

## Getting started

1. Search existing issues and pull requests for related work.
2. For a new skill or substantial design change, open a proposal before investing in the implementation.
3. Fork and clone the repository.
4. Create a focused feature branch from the latest `main`.
5. Make and validate your changes.
6. Open a pull request using the repository template and respond to review feedback.

## Adding or changing a skill

Prefer using the [`skill-creator`](https://github.com/anthropics/skills/tree/main/skill-creator)
skill to scaffold and refine new skills rather than authoring them by hand.

Skills live under `skills/<skill-name>/` and must follow the
[Agent Skills specification](https://agentskills.io/specification). Each skill must include a
`SKILL.md` with YAML frontmatter containing `name` and `description`; the directory name must match
the `name` field. Skill names in this repository use the `ollygarden-` prefix. Optional
subdirectories include `scripts/`, `references/`, and `assets/`.

Validate spec conformance locally with the
[`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref) reference tool:

```bash
skills-ref validate skills/<skill-name>
```

When you add or rename a skill, keep all three registration points in sync:

1. `skills/<skill-name>/SKILL.md`;
2. the plugin entry in `.claude-plugin/marketplace.json`; and
3. the Available Skills table and layout tree in `README.md`.

### Keep opinions and upstream facts separate

This repository contains OllyGarden-owned workflows and opinions. Vendor-neutral OpenTelemetry
facts belong in the companion
[`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills) repository.
Reference those upstream skills for semantic conventions, SDK versions, component configuration,
and OTTL syntax instead of duplicating them here. Keep skills token-efficient by preferring targeted
lookups and progressive disclosure over broad copied context.

## Proving the skill helps: harness results

Every pull request that adds a skill or substantively changes one must include evaluation results
showing that the skill improves agent output:

1. Choose representative prompts that exercise the changed behavior.
2. Run each prompt without the skill on a frontier model in a fresh session.
3. Run the same prompt with the skill using the same model and harness in another fresh session.
4. Include the prompts, model and harness versions, a comparison of the results, and links to the
   transcripts in the pull request description.

Useful evidence includes correcting stale or inaccurate guidance, avoiding wrong turns, retrieving
the right source more efficiently, or applying OllyGarden's intended workflow consistently. If the
comparison shows no meaningful improvement, refine the skill before submitting it.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) with an optional skill scope:

```text
<type>(<optional scope>): <short description>
```

Common types are `feat`, `fix`, `docs`, `chore`, and `refactor`.

## Pull requests

- Keep the pull request focused on a single change.
- Include a summary, motivation, validation results, and agent-involvement disclosure.
- Include harness comparison results for new or substantively changed skills.
- Update every registration point when adding, renaming, or removing a skill.
- Confirm documentation links resolve and generated artifacts were regenerated rather than
  hand-edited.
- Ensure required checks pass and address maintainer review before merge.

## Contributor License Agreement

Before we can merge your first pull request, you must sign the OllyGarden
[Contributor License Agreement](https://github.com/ollygarden/.github/blob/main/CLA.md). The CLA bot
comments with instructions; sign by replying with the requested confirmation. You only need to
sign once for this repository.

## License and conduct

Contributions are accepted under the [Apache License 2.0](LICENSE) and the organization-wide
[OllyGarden CLA](https://github.com/ollygarden/.github/blob/main/CLA.md). All project interactions
are governed by OllyGarden's
[Code of Conduct](https://github.com/ollygarden/.github/blob/main/CODE_OF_CONDUCT.md).
