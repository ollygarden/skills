---
name: ollygarden-otel-collector-config-decomposition
description: OllyGarden's opinion on when and how to decompose a monolithic OpenTelemetry Collector config into multiple merged files — and when to leave it alone. Use whenever someone wants to split, break up, modularize, or reorganize a large otelcol / collector YAML, or asks "should I split this config", "this collector config is too big to review", "refactor our collector config into multiple files", "organize the collector config by signal / by team". Executes the split directly when warranted (the collector deep-merges repeated --config file: sources), verifies the merged result is behavior-equivalent to the original, and always reports the reasoning — including a deliberate no-op when the config is simple enough not to need it. Plain files and multi-config merge only; not for Terraform/Kustomize/Helm packaging. Layers on facts from otel-collector; hands off behavioral proof to ollygarden-otel-collector-config-validation.
license: Apache-2.0
---

# Decomposing an OTel Collector config

This skill is OllyGarden's opinion that **a collector config should be decomposed only when
the monolith has become painful — and left as one file when it hasn't.** Decomposition buys
smaller reviews, isolated testing, and clean per-environment variation, but it costs
indirection: a reader now has to mentally merge several files to see the whole. When a config
fits on a screen, that cost outweighs the benefit. **Not splitting is a valid, common, and
correct outcome.**

The mechanism that makes decomposition work is the collector's **deep merge** of repeated
`--config file:` sources (later keys win at each level), plus the `file:`/`env:`/`yaml:`
providers. This skill owns the generic mechanics; the specialized
`ollygarden-otel-collector-k8s-daemonset` skill is a *consumer* of this one for its own
reference config.

It layers on upstream facts — point at these rather than duplicating them:

- Component config keys, defaults, signal support → the **`otel-collector`** skill.
- Behaviorally proving the decomposed config still does what it should (a `filter` still drops
  the right spans, a `transform` still sets the attribute) → the
  **`ollygarden-otel-collector-config-validation`** skill.

## Default behavior: execute, but be critical first

When you're handed a collector config, **assess it, then act directly** — don't just advise.
But the first decision is always *whether* to split at all:

1. **Assess** the config against the decision criteria below.
2. **If it's not warranted → stop and say so.** Make no changes. Report *why* the config is
   fine as one file (small, single pipeline, no env drift). A deliberate no-op is a success.
3. **If it is warranted → split it**, pick the best-fit strategy, write the files, and
   **verify the merged result is behavior-equivalent** to the original (see below).
4. **Always report the reasoning** — what you changed (or didn't) and why. The reasoning is
   part of the deliverable, not an afterthought.

## When to decompose — and when not to

Decompose when **two or more** of these are true; a single weak signal is usually not enough:

- **Size.** The config has grown past a few hundred lines and reviews mean scrolling.
- **Multiple signal pipelines.** Traces, metrics, and logs pipelines with distinct
  receivers/processors that different people touch.
- **Environment drift.** Near-identical copies (prod/staging/dev) that have been copy-pasted
  and are drifting apart.
- **Ownership boundaries.** Distinct teams own distinct parts (platform owns receivers,
  observability owns processors, SRE owns exporter destinations).
- **An oversized single block.** One block dominates the file — a long `tail_sampling` policy
  list, a big set of Prometheus scrape jobs, a wall of OTTL statements.

**Do NOT decompose when** the config fits on a screen, has a single pipeline, has no
environment variation, and is owned by one person. Indirection you don't need is a net
negative. If in doubt and the signals are weak, leave it as one file and say why.

## How to split

Pick the strategy that matches the config's **actual** organizational boundaries — don't apply
a pattern mechanically. The three patterns, and how to choose between them, are in
[`references/strategies.md`](references/strategies.md):

- **By signal pipeline** — `common.yaml` + self-contained `traces.yaml` / `metrics.yaml` /
  `logs.yaml`. The default when signals are owned or iterated independently.
- **By component type** — `base.yaml` + `receivers.yaml` / `processors.yaml` / `exporters.yaml`.
  Fits when teams own pipeline *stages*.
- **Environment overlays** — a base plus `production.yaml` / `staging.yaml` / `development.yaml`
  that override values. Layers on top of either split above.
- **Nested inclusion** (`${file:}`) — pull one oversized, independently-ownable sub-block into
  its own bare-fragment file. Use sparingly.

Before writing files, read [`references/mechanics.md`](references/mechanics.md) for the merge
rules and the caveats that bite silently — most importantly that **arrays are replaced, not
merged** (keep anything that varies together, especially a pipeline's `processors:` list, in
one file) and that **`${file:}` paths resolve relative to the collector's working directory**,
not the including file.

## Verify before you're done

A decomposition that changes behavior is a bug, not a refactor. Never hand back a split you
haven't merged and checked. Validate the **merged** set (never a lone fragment) and diff the
fully-resolved output against the original monolith. The commands and the
behavior-equivalence check are in [`references/verifying.md`](references/verifying.md). For
proving a *specific* processor/connector still transforms telemetry correctly, hand off to
the **`ollygarden-otel-collector-config-validation`** skill.

## Report template

End every run with a short report so the reasoning ships with the change:

```
Decision: <decomposed | left as one file>
Why: <which criteria were / weren't met>
Strategy: <by-signal | by-component | overlays | nested — or n/a>
Files: <the file set produced, or "unchanged">
Verification: <merged validate result + equivalence check, or "n/a">
```

## Pitfalls

- **Splitting a config that didn't need it.** The most common mistake. Indirection has a cost;
  a screen-sized single-pipeline config should stay one file.
- **Handing back an unverified split.** If you didn't validate the merged set and confirm
  equivalence, you don't know the refactor was behavior-preserving.
- **Splitting a pipeline's `processors:` array across files.** Arrays are replaced, not merged
  — the last file wins and silently drops the rest of the list. Keep it in one file.
- **Applying a pattern that doesn't match ownership.** Splitting by signal when one team owns
  everything just adds files to merge in your head. Match the split to real boundaries.
- **Over-using `${file:}` nested inclusion.** Externalize only blocks that are both large and
  independently ownable; each include is another file to open.

## Cross-references

- Component facts (keys, defaults, signal support): **`otel-collector`**.
- Behavioral proof that the split config still transforms telemetry correctly:
  **`ollygarden-otel-collector-config-validation`**.
- A worked application of these mechanics on a real reference config:
  **`ollygarden-otel-collector-k8s-daemonset`**.
