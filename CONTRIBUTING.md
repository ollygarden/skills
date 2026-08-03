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

[`docs/preferred-workflow.md`](docs/preferred-workflow.md) walks the same path in order, with the
reasoning behind each gate and the exact commands. Follow it for anything beyond a typo fix.

## Adding or changing a skill

Prefer using the [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
skill to scaffold and refine new skills rather than authoring them by hand.

Skills live under `skills/<skill-name>/` and must follow the
[Agent Skills specification](https://agentskills.io/specification). Each skill must include a
`SKILL.md` with YAML frontmatter containing `name` and `description`; the directory name must match
the `name` field. Skill names in this repository use the `ollygarden-` prefix. Optional
subdirectories include `scripts/`, `references/`, and `assets/`.

When you add or rename a skill, keep all three registration points in sync:

1. `skills/<skill-name>/SKILL.md`;
2. the plugin entry in `.claude-plugin/marketplace.json`; and
3. the Available Skills table and layout tree in `README.md`.

### Validate locally

Two scripts check the rules above, and both run in CI — a miss surfaces as a failed check rather
than a review comment:

```bash
# One-time: install the pinned reference validator.
uv tool install "$(cat bin/skills-ref.requirement)"

./bin/validate-skill.sh          # spec conformance, <500 lines, ollygarden- prefix
./bin/check-skill-inventory.sh   # README table, README tree, and marketplace vs skills/
```

`validate-skill.sh` delegates spec conformance to
[`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref) and accepts skill
directories as arguments, so `./bin/validate-skill.sh skills/<skill-name>` checks just yours. The
inventory script reports drift in both directions: a skill with no entry, and an entry naming a
skill that does not exist.

A third check runs [lychee](https://github.com/lycheeverse/lychee) over the repository's links on
every pull request. Example and unreachable hosts are excluded in `.github/lychee.toml`; if your
change needs a new exclusion, add it there with a reason.

### Keep opinions and upstream facts separate

This repository contains OllyGarden-owned workflows and opinions. Vendor-neutral OpenTelemetry
facts belong in the companion
[`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills) repository.
Reference those upstream skills for semantic conventions, SDK versions, component configuration,
and OTTL syntax instead of duplicating them here. Keep skills token-efficient by preferring targeted
lookups and progressive disclosure over broad copied context.

## Proving the skill helps: harness results

Every pull request that adds a skill or substantively changes one must include evaluation results
showing that the skill improves agent output. The required evidence comes from an agent harness
(Claude Code, or a comparable harness driving a frontier model), run in **three arms**:

1. **Target skill withheld** — the skill is not installed.
2. **Current `origin/main` skill** — the skill exactly as it ships today.
3. **Proposed PR skill** — the skill as this PR would ship it.

Arms 1 and 3 are the A/B comparison this repo has always asked for: does this skill help at all?
Arm 2 is what catches a **regression in a skill that already ships** — neither of the others can,
because neither is the current baseline. For a brand-new skill there is no revision to name, so its
revision cell is `Not present` — but the arm still reports results. It is then the same
configuration as the withheld arm, so it needs no extra runs. For a change to an existing skill it
is the arm that matters most.

1. Pick one or more representative prompts a user would realistically ask — ideally prompts that
   exercise the part of the skill you added or changed. Skills that carry a checked-in suite keep it
   in `skills/<skill-name>/evals/evals.json`.
2. Run every arm with the **same** cases, repetitions, model, harness, grading rules, and tool
   access, each in a fresh session. Name the model and harness once, above the table.
3. In the withheld arm, withhold **only** the target skill. Leave everything else in place.
4. Run each case **at least three times** per arm. A single run cannot distinguish a real
   improvement from a lucky sample.
5. Report the results in the PR description using the table in the pull request template, and attach
   or link the transcripts (a gist is fine) so reviewers can verify.

**Sanitize a transcript before you link it.** A harness transcript records everything the agent saw:
environment variables, tokens pasted into a session, customer names, paths and file contents from
private repositories. This repository is public and a linked gist usually is too, so redact before
posting — and if a transcript cannot be sanitized without destroying the evidence, summarize the run
instead and say that is what you did. A reviewer can work with a summary; neither of us can unpublish
a leaked credential.

Recording the arms honestly matters more than a clean-looking table:

- **`Not present`** goes in the target-skill revision cell only — for a new skill, on the
  `origin/main` arm; for a removal, on the proposed arm. The arm's *results* are still required
  either way.
- **An arm you did not run, or that was invalidated, is `Not run`, with the reason.** Incomplete
  evidence is not an improvement claim, and a gap named plainly costs a reviewer far less than one
  they have to find.
- **Preserve genuine misses.** Never retry a failing repetition until it passes, and never report a
  designed-but-unrun case as passing.

Useful evidence includes correcting stale or inaccurate guidance, avoiding wrong turns, retrieving
the right source more efficiently, or applying OllyGarden's intended workflow consistently — and no
regression against the shipping version. If the comparison shows no meaningful difference, that's a
signal the skill (or the change) isn't earning its place — rework it rather than submitting the
results anyway.

A pure **efficiency** improvement — trimming a skill so it costs less context while behaving
identically — is a legitimate result here. Say so, state how you measured it, and show the required
behavior still passing in the proposed arm.

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
