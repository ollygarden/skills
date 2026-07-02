# Verifying a decomposition is behavior-preserving

Companion reference for the `ollygarden-otel-collector-config-decomposition` skill. A split
that changes what the collector does is a bug, not a refactor. Two checks prove it didn't:
**the merged set validates**, and **the fully-resolved config matches the original monolith.**

## 1. Validate the merged set — never a fragment

Pass every file, in order, to `validate`. A lone signal or component file references shared
pieces it doesn't define and will fail on its own — that failure is noise, not signal.

```sh
# from the directory that makes any ${file:} include paths resolve (see mechanics.md, caveat 2)
otelcol-contrib validate \
  --config file:common.yaml --config file:traces.yaml \
  --config file:metrics.yaml --config file:logs.yaml
```

`validate` instantiates the pipeline and compiles OTTL, but it does **not** confirm that env
vars resolve, that `${file:}` includes inlined, or that a rule matches your data. It is
necessary, never sufficient. Set any env vars the config requires (empty required fields like
an `otlp` exporter `endpoint` do fail validation).

## 2. Diff the fully-resolved config against the monolith

`print-config` emits the config **after** merging and env substitution — exactly what the
collector would run. That's the artifact to compare against the pre-split monolith:

```sh
otelcol-contrib print-config \
  --config file:common.yaml --config file:traces.yaml \
  --config file:metrics.yaml --config file:logs.yaml > merged.yaml
```

Compare `merged.yaml` to the original. A structural (not textual) diff is what matters — key
order and formatting will differ, semantics must not. In Python (pyyaml), assert:

- equal top-level `receivers` / `processors` / `exporters` / `extensions` **key sets**;
- equal per-pipeline `receivers` / `exporters`, and equal `processors` **arrays** (order
  matters — processors run in sequence);
- if you deliberately split one processor into two, apply a rename map and assert the split
  pieces carry the original OTTL statements/conditions **verbatim**.

Any unexplained difference means the merge didn't reassemble what you started with — most often
the array-replace caveat silently dropping a processor from a pipeline's list.

Confirm nested includes actually inlined: `grep -c` the resolved output for a token that only
appears inside an included fragment (e.g. `job_name` for Prometheus scrape jobs) and check the
count matches the number of includes.

## 3. Behavioral proof (when a component's correctness is in question)

`validate` + equivalence-diff prove the *structure* is preserved. They do **not** prove a
`filter` still drops the right spans or a `transform` still sets the right attribute against
real telemetry. When that's the question — especially if you split or moved a processor — hand
off to the **`ollygarden-otel-collector-config-validation`** skill, which runs the component
under test against generated telemetry and asserts the output.
