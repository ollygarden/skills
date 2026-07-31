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
Avoid empty or null map stubs in later files: they can remove earlier values.

**Sequences are replaced, not combined.** A later `processors: [a, b]` replaces an earlier
`processors: [a, c, b]`. Keep every pipeline's `receivers`, `processors`, and `exporters` sequence
whole in one file. Processor order must remain unchanged.

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

Nested fragments are resolved from raw bytes, including comments. Keep literal provider tokens out
of comments in fragments to avoid accidental or recursive expansion.
