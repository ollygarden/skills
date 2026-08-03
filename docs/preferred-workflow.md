# Preferred workflow

How to take a change through this repository, end to end. [`CONTRIBUTING.md`](../CONTRIBUTING.md)
states the rules a contribution must satisfy; this file is the order to do them in and the reasoning
behind each gate.

Follow this whenever a change adds, renames, moves, or removes a skill, or alters a skill's
instructions, thresholds, or safety language. Typo and prose fixes go straight to a PR — but only
outside `SKILL.md` frontmatter and outside behavior-bearing instructions. A `description:` edit
changes when a skill triggers, so it takes the full path however small the wording change looks.
Skip a step only when it clearly does not apply, and say so rather than skipping silently.

Reviews run in a fixed order — **local adversarial → agent in CI → human**. Never ask for the next
reviewer until the previous one is clean; a human should never be the one to find what a sub-agent
or the review bot would have caught.

1. **Track it.** Open or find a GitHub issue describing the goal, and say what "done" looks like
   there rather than only in chat. For a new skill or a substantial design change, get agreement on
   the proposal before investing in the implementation. (OllyGarden maintainers also track the work
   in Linear; that is internal bookkeeping and never a substitute for the public issue.)

2. **Branch and isolate.** Always branch from freshly fetched `origin/main` — never from the working
   checkout's `HEAD`, which is sometimes detached or on a stale branch. A dedicated worktree per
   task keeps unrelated work isolated and the main checkout clean:

   ```bash
   git fetch origin
   git worktree add --no-track ../skills-worktrees/<slug> -b <branch> origin/main
   ```

   `--no-track` keeps the new branch from tracking `origin/main`, which reduces the risk of an
   accidental push to the default branch. It is not a complete guard: `push.default` and
   `remote.pushDefault` can still route a bare `git push` elsewhere.

3. **Do the work.** Read the target `SKILL.md` and every reference it routes to before editing. Make
   the smallest defensible change. Keep OllyGarden opinions separate from upstream OpenTelemetry
   facts, which belong in
   [`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills). Never
   weaken safety, trust-boundary, or human-review language while compacting prose.

4. **Run the evals.** Any change that can alter when a skill triggers, or what an agent retrieves,
   recommends, or emits, must be backed by eval evidence. A skill that does not measurably help is
   context-window cost with no benefit. Skills that carry evals keep them in
   `skills/<name>/evals/evals.json`, with fixtures under `evals/files/` where a case needs them. Add
   or update a case whenever a change closes a newly discovered gap; a prose fix for testable
   behavior is incomplete without a regression case that would have caught it.

   - Cover a representative happy path, an ambiguous or incomplete input, and — for any skill
     consuming telemetry, CLI output, config, or identifiers — a hostile, malformed, or misleading
     input.
   - Run each case at least three times. A single run cannot distinguish a real fix from a lucky
     sample.
   - Run the with-skill and without-skill arms `CONTRIBUTING.md` requires under the same model,
     harness, grading rules, and tool access, and say which harness produced the numbers.
   - Preserve genuine misses. Never retry a failing repetition until it passes, and never report a
     designed or deferred eval as passing.

   > Under discussion, in a separate PR: adding a third arm — **current `origin/main` skill** —
   > alongside withheld and proposed. It is the only arm that can catch a regression in a skill that
   > already shipped, since neither existing arm is the shipped baseline. It changes what we ask of
   > every contributor, so it gets its own review rather than riding in on a tooling change, and it
   > must land identically here and in
   > [`opentelemetry-agent-skills`](https://github.com/ollygarden/opentelemetry-agent-skills).

5. **Run the local checks.** Both run in CI, so a miss here surfaces as a failed check rather than a
   review comment:

   ```bash
   ./bin/validate-skill.sh          # Agent Skills spec + house rules, every skill
   ./bin/check-skill-inventory.sh   # README table, README tree, and marketplace vs skills/
   ```

   `validate-skill.sh` shells out to `skills-ref`, which needs a one-time
   `uv tool install "$(cat bin/skills-ref.requirement)"` from the repository root.

   If your change touches links, run the third gate too:

   ```bash
   lychee --no-progress --root-dir "$PWD" --config .github/lychee.toml .
   ```

   Quote the lychee version alongside any count you report — exclusion patterns
   are version-sensitive, since lychee percent-encodes `{`/`}` in a URL but leaves `$` literal, so
   a count without a version is not reproducible. Fix genuine rot rather than excluding it, and
   verify that any exclusion you add actually changes the result before keeping it.

6. **Sweep for stale documentation.** A change is done when nothing left in the repository describes
   the old behavior — not when the check passes. Fix these in the same PR rather than a follow-up:

   - `README.md` — the "Available Skills" table, the layout tree, and any Installation or
     Contributing step the change alters.
   - `CONTRIBUTING.md` and `AGENTS.md` — the registration points, constraints, and conventions.
   - **This file.** `AGENTS.md` points here as the authoritative path, so a new gate, script, or
     tool that is not written down here does not exist for anyone following it.
   - Any `references/` doc, or any other skill, that restates a threshold, schema, command, or file
     path this change moved. A skill's contract is often quoted in more than one place.

   Be exact about what is enforced and what is not. A doc that promises a check nothing runs is
   worse than no doc, because the next contributor trusts it; when a constraint is review-enforced
   rather than automated, say so where the constraint is stated.

7. **Adversarially review it locally, in a sub-agent.** Before pushing, dispatch a read-only
   sub-agent to attack the diff: verify every factual claim against the repository instead of
   trusting the prose, hunt for contradictions with existing guidance, and judge whether the change
   is actionable and worth its context cost. Ask for prioritized findings with evidence, not praise.
   Fix the valid ones; state why you dismissed the rest.

8. **Open the PR.** Conventional Commits for both the commit message and the PR title. Fill in the
   pull request template: what changed and why, the agent-involvement disclosure, the harness
   results with per-case totals, any failing or unknown case you kept and its adjudication, and the
   limitations. Keep raw transcripts out of the repository; summarize and link them instead.

9. **Clear the agent in CI** (CodeRabbit today). Read threads with a thread-aware query —
   `gh pr view --comments` shows the flat view and hides resolution state:

   ```bash
   gh api graphql -f query='{repository(owner:"ollygarden",name:"skills"){pullRequest(number:<pr>){reviewThreads(first:100,after:null){pageInfo{hasNextPage endCursor}nodes{isResolved path comments(first:10,after:null){pageInfo{hasNextPage endCursor}nodes{body}}}}}}}'
   ```

   Both connections are paged, and both must be walked. If
   `reviewThreads.pageInfo.hasNextPage` is true, repeat with `after:"<endCursor>"` until it is
   false — an unresolved count taken from one page is not a count of zero. Each thread's
   `comments` connection has its own `pageInfo`, asked for above so you can see when it truncates;
   page any thread whose `comments.pageInfo.hasNextPage` is true before concluding it was
   answered, since the reply that resolves a long thread is the last comment, not the first ten.

   Verify each suggestion against the current head, fix the valid ones, and reply with evidence.
   Dismiss a finding only with a stated reason — a bare resolve is not an answer. Push, then wait
   for a review of the *new* head. Repeat until checks are green and unresolved threads are zero.

   If a review round changes behavior, rerun the evals against the new head and update the results
   in the PR body. Evidence from an older head does not describe what is about to merge.

10. **Then request human review.** Only once the agent in CI is clean and every one of its comments
    is addressed or explicitly dismissed. Summarize what changed since the last look, what the
    sub-agent and the CI agent found, and what you chose not to act on.

11. **Merge behind the gate.** Approval binds to the SHA it was given on. GitHub only dismisses a
    stale approval when branch protection is configured to, and `--match-head-commit` only refuses a
    *different* head — neither guarantees the approval you have describes the head you are merging.
    Confirm the review was submitted against the current head SHA, and get fresh approval if it was
    not. A merge cannot be recalled, so do not send it while a review question is open. Run it from
    the primary checkout, not from inside the task worktree:

    ```bash
    gh pr merge <pr> --repo ollygarden/skills --squash --match-head-commit <approved-full-sha>
    ```

12. **Close out.** Verify the worktree is tracked-clean, remove it with a non-forced
    `git worktree remove <exact-path>`, and only then delete the local branch. Never prune broadly
    or touch worktrees you did not create.

## Why each gate exists

Every rule above came from a change that went wrong: branching from a detached primary checkout, an
approval that had gone stale against a newer head, a merge command sent while a review question was
still open, and worktree cleanup that risked unrelated worktrees.

The eval rules have the same origin. All-pass suites have hidden policy defects when a fixture
rewarded behavior the skill's contract forbids; single runs have read as fixes when they were
sampling luck; and a schema a provider rejected produced a clean-looking run with no behavioral
evidence behind it.
