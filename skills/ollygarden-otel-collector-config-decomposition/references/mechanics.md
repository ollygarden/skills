# Merge mechanics and the caveats that bite silently

Companion reference for the `ollygarden-otel-collector-config-decomposition` skill. The
SKILL.md holds the opinion; this file holds the mechanism you need before writing split files.

## Deep merge

The collector accepts multiple configuration sources and **deep-merges** them in the order
given. Keys from later sources override keys from earlier ones **at each level of the
hierarchy** — not a whole-document replacement, a per-key one. That is the entire foundation
of decomposition: split by concern, and let the merge reassemble the whole.

```bash
otelcol-contrib --config file:common.yaml \
                --config file:traces.yaml \
                --config file:metrics.yaml \
                --config file:logs.yaml
```

Because `service.pipelines.traces`, `service.pipelines.metrics`, and `service.pipelines.logs`
are distinct map keys, three signal files each defining one of them merge without collision
into a complete `service.pipelines` with all three.

## Providers

- **`file:`** — inclusion. Both as a top-level `--config file:x.yaml` source and, *inside* a
  config, as `${file:path}` which inlines another file's raw content at the reference point.
- **`env:`** — substitution. `${env:VAR}` (or shorthand `${VAR}`) is replaced with the
  environment variable's value; `${env:VAR:-default}` supplies a fallback.
- **`yaml:`** — inline YAML values via `${yaml:...}`.

## `${file:}` nested inclusion

For one oversized sub-block, pull it into its own file and reference it:

```yaml
processors:
  tail_sampling:
    decision_wait: 30s
    policies:
      - ${file:policies/errors.yaml}
      - ${file:policies/slo-violations.yaml}
```

Each included file is a **bare fragment** — no top-level keys, just the raw content that slots
in at the reference point. A policy file therefore starts at `name:`, not at `processors:`:

```yaml
# policies/errors.yaml — a bare fragment, inlined where it's referenced
name: errors
type: status_code
status_code:
  status_codes: [ERROR]
```

## The caveats that bite silently

1. **Arrays are replaced, not merged.** If one file defines `processors: [a, b, c]` and a later
   file defines `processors: [a, b]`, the result is `[a, b]` — not the union. This is the single
   most dangerous caveat, because it silently drops pipeline stages. **Keep anything that varies
   together — above all a pipeline's `processors:` list — in one file.**

2. **`${file:}` paths resolve relative to the collector's working directory**, not the file
   containing the include. A `${file:policies/errors.yaml}` reference resolves from wherever the
   collector process runs, regardless of which file holds the reference. Run the collector (and
   `validate`) from the directory that makes the paths resolve, or use absolute paths.

3. **`${env:VAR:-default}` defaults apply only when the variable is _unset_.** An exported
   `VAR=""` is *not* unset — the default will not kick in and you get an empty value. For
   required vars with no sane default, check externally before start:
   `: ${BACKEND_ENDPOINT:?BACKEND_ENDPOINT must be set}`.

4. **OCB-built distributions must list the providers.** The `file`, `env`, and `yaml` providers
   are **not** included by default in a custom `ocb` build. Omit them from the builder manifest
   and `${file:}` / `${env:}` URIs fail with cryptic "unsupported scheme" errors:

   ```yaml
   # builder.yaml
   providers:
     - gomod: go.opentelemetry.io/collector/confmap/provider/fileprovider v1.62.0
     - gomod: go.opentelemetry.io/collector/confmap/provider/envprovider v1.62.0
     - gomod: go.opentelemetry.io/collector/confmap/provider/yamlprovider v1.62.0
   ```

5. **`${...}` tokens in _comments_ can still expand — in nested fragments.** A literal
   `${file:...}` (or `${env:...}`) inside a **comment** is dangerous depending on how the file
   loads:
   - **Nested-included fragment files** (pulled via `${file:}`) have their raw bytes —
     comments included — recursively resolved. A comment in a fragment that references the
     fragment's own path causes **infinite self-recursion**.
   - **Top-level `--config file:` files** are parsed as YAML first, so comments are stripped
     before value-level `${...}` expansion — a `${file:}` in their comments is harmless.
   - **Rule of thumb:** keep literal `${file:}` / `${env:}` out of *all* comments. Write
     `file:` / `env:` (no `${...}`) in prose comments for consistency.
