---
name: ollygarden-otel-collector-config-decomposition
description: >-
  Decide and execute plain-file decomposition for OpenTelemetry Collector YAML. Use for "should I split this collector config?", "break up this otelcol YAML", "organize it by signal or team", or "create environment overlays". Leaves simple configs intact and proves warranted splits equivalent after merge. Not for Helm, Kustomize, or Terraform packaging; use otel-collector for component facts and ollygarden-otel-collector-config-validation for behavioral proof.
license: Apache-2.0
---

# Decompose Collector config only when it pays

OllyGarden's default is restraint: decomposition reduces review and ownership scope, but makes every
reader reconstruct the whole. A deliberate no-op is the correct result when indirection costs more
than it saves.

Use upstream skills for facts that change independently:

- `otel-collector` — current providers, merge behavior, commands, component keys, and distribution
  support.
- `ollygarden-otel-collector-config-validation` — behavioral proof for a processor or connector.
- `ollygarden-otel-collector-k8s-daemonset` — a consumer of this workflow, not its source of truth.

## Workflow

1. Inspect the monolith, environment variants, ownership, and deployment command. Record the exact
   Collector distribution and version, feature-gate set, and ordered configuration URIs.
2. Count the pressures below. If fewer than two are meaningful, stop without changing files.
3. If warranted, choose the split from actual change and ownership boundaries.
4. Read [`references/mechanics.md`](references/mechanics.md), then write the split directly unless
   the user requested a plan or the workspace is read-only.
5. Validate and compare the fully resolved monolith and split using
   [`references/verifying.md`](references/verifying.md). Do not call the refactor complete without
   both checks.
6. Return the decision report.

## Decision gate

Decompose when at least two of these are substantial:

- reviews regularly struggle with a config of hundreds of lines;
- independently changing traces, metrics, or logs pipelines share one file;
- copied environment variants are drifting;
- different teams own ingress, processing, egress, or signal pipelines;
- one independently owned block dominates the file, such as sampling policies or scrape jobs.

Keep one file when it fits on a screen, has one pipeline, one owner, and no environment drift. A
single weak signal is not enough.
An existing split or a request to split is not itself a pressure; judge the underlying config.

## Select the boundary

Read [`references/strategies.md`](references/strategies.md) for layouts and overlay mechanics.

- Independent signal teams → by signal: `common.yaml` plus complete signal files. This is the usual
  default and keeps each pipeline together.
- Stage-owning teams → by component: a service/pipeline base plus component-type files.
- Same structure, different values → environment overlays on either layout.
- One large independently owned sub-block → one nested `file:` inclusion; do not fragment small
  blocks.

When several fit, prefer the smallest file set that follows the strongest real boundary. Do not
invent an ownership model to justify a pattern.

## Non-negotiable preservation rules

- Keep each pipeline's `receivers`, `processors`, and `exporters` sequence in one file. Under the
  default merge behavior, later sequences replace earlier ones. Even when
  `confmap.enableMergeAppendOption` is enabled, only `service.extensions` and pipeline receivers
  and exporters append; processors still replace, and processor order is behavior.
- Define shared components once. Distinct `service.pipelines.<name>` map entries may live with their
  owning signal.
- Preserve component IDs, values, provider expressions, extensions, connectors, service telemetry,
  and pipeline membership unless the user separately authorized a behavior change.
- Treat environment overlays as ordered inputs. Record their order, exact configuration URIs, and
  feature-gate set.
- Validate the complete ordered source set, never a fragment in isolation.
- Compare fully resolved output from the monolith with fully resolved output from the split under
  the same pinned Collector and environment. Raw YAML versus resolved YAML is not an equivalence
  test.
- Structural equality does not prove that an OTTL rule, processor, or connector behaves correctly;
  explicitly hand that question to `ollygarden-otel-collector-config-validation` in the report.

## Decision report

End with:

```text
Decision: <decomposed | left as one file>
Why: <criteria met or absent>
Strategy: <by-signal | by-component | overlays | nested | n/a>
Files: <created/changed files or unchanged>
Verification: <merged validation and resolved-equivalence result, pending reason, or n/a>
```
