## Summary

<!-- What does this PR change, and why? -->

## Agent involvement

<!-- We welcome PRs authored and implemented by AI coding agents (see CONTRIBUTING.md).
     Note here whether an agent wrote/implemented this change, and confirm a human reviewed it. -->

## Harness results (required for new or substantively changed skills)

<!-- A/B comparison proving the skill helps, per CONTRIBUTING.md:
     - Prompt(s) used, and how many times each was repeated
     - Model + harness
     - Baseline run (without the skill): what it got wrong, outdated, or wasteful
     - Skill run (same prompt, same model): what improved
     - Any failing or unknown run you chose to keep, and why
     - Links to transcripts
     Delete this section for changes that don't touch skill content. -->

## Checklist

- [ ] `./bin/validate-skill.sh` passes ([Agent Skills spec](https://agentskills.io/specification) + house rules)
- [ ] `./bin/check-skill-inventory.sh` passes — skill registered in all three places (skill directory, `.claude-plugin/marketplace.json`, `README.md` table + tree)
- [ ] Content keeps OllyGarden opinions separate from upstream OpenTelemetry facts
- [ ] Harness comparison results included above — if skill content changed
- [ ] Commit messages follow Conventional Commits
- [ ] I have signed (or will sign via the CLA bot on this PR) the [OllyGarden CLA](https://github.com/ollygarden/.github/blob/main/CLA.md)
- [ ] I have read and will follow the [Code of Conduct](https://github.com/ollygarden/.github/blob/main/CODE_OF_CONDUCT.md)
