# Merge mechanics

Captured 2026-07. Confirm current syntax and the pinned distribution with `otel-collector` before
editing; this reference retains only decomposition-specific failure gates.

## Multiple configuration sources

The Collector accepts repeated configuration sources in order:

```sh
otelcol-contrib \
  --config=file:common.yaml \
  --config=file:traces.yaml \
  --config=file:metrics.yaml \
  --config=file:logs.yaml
```

Maps merge by key and later conflicts win. This lets distinct
`service.pipelines.traces`, `.metrics`, and `.logs` entries reassemble under one `service` map.
Avoid null map stubs such as `processors:` in later files: they remove earlier values. Use
`processors: {}` for an intentional empty map, or omit the key.

**By default, sequences are replaced, not combined.** A later `processors: [a, b]` replaces an
earlier `processors: [a, c, b]`. The experimental `confmap.enableMergeAppendOption` gate changes
that behavior only for `service.extensions` and pipeline `receivers` and `exporters`; pipeline
`processors` still replace. Keep every pipeline's ordered sequences whole in one file. Record the
exact feature-gate set and configuration URIs rather than assuming append behavior. Processor
order must remain unchanged.

## Provider references

Top-level `--config=file:...` inputs merge complete or partial configs. A nested `${file:path}`
inlines raw content at one location. Use nesting only for one large independently owned block:

```yaml
processors:
  tail_sampling:
    policies:
      - ${file:policies/errors.yaml}
```

The included policy is a bare fragment, not another `processors:` map:

```yaml
name: errors
type: status_code
status_code:
  status_codes: [ERROR]
```

Relative nested paths resolve from the Collector process's working directory, not from the
including file. Record the required working directory or use reviewed absolute paths.

Environment and YAML providers are useful for value overlays, but their exact syntax and behavior
are upstream facts. Preserve provider expressions verbatim during a pure refactor. In particular,
do not assume an environment default applies to an explicitly empty variable.

Custom OCB distributions must include every provider used by the config. Consult `otel-collector`
for the matching provider modules and versions for the pinned build rather than copying a version
from this reference.

The built-in file provider parses included content as YAML before resolver expansion, so YAML
comments are discarded. Provider expressions in parsed configuration values are still resolved;
preserve those expressions verbatim during a pure refactor.
