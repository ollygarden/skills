# Decomposing this config

Companion reference for the `ollygarden-otel-collector-k8s-daemonset` skill. The SKILL.md
summarizes this; the detail lives here.

This reference config is split into multiple files instead of one monolith, because a
single ~470-line collector YAML is painful to review, test, and vary per environment. The
collector **deep-merges** repeated `--config file:` sources — later keys override earlier
ones at each level — and the file/env/yaml providers do inclusion and variable substitution.
That merge is what lets you split by concern and have the collector reassemble the whole.

**The layout we ship — by signal pipeline.** [`common.yaml`](common.yaml) holds
everything shared by all three pipelines (the `otlp` receiver, `memory_limiter`,
`resourcedetection`, `k8sattributes`, `resource/clustername`, `transform/truncate_resources`,
`batch`, the `otlp` exporter, the `file_storage` extension, and `service.telemetry`), defined
once. Each of [`traces.yaml`](traces.yaml), [`metrics.yaml`](metrics.yaml), and
[`logs.yaml`](logs.yaml) is self-contained for its signal: its own signal-specific receivers
and processors plus its own `service.pipelines.<signal>` entry. The three pipeline keys are
distinct, so the merge combines them without collision. This pattern fits because this skill's
guidance is already organized signal by signal, and because it keeps each pipeline's processor
*array* in one file (see the array caveat below).

**Nested inclusion for big sub-blocks.** The Prometheus receiver's three scrape jobs are the
one block large and independent enough to externalize, so each lives as a bare-fragment file
under [`prometheus/`](prometheus/) and is pulled in with the file provider:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - ${file:prometheus/scrape-pods.yaml}
        - ${file:prometheus/scrape-pods-slow.yaml}
        - ${file:prometheus/scrape-kube-state-metrics.yaml}
```

Each included file is a raw YAML fragment (a single scrape-job map, no top-level keys) that the
provider inlines at the reference point. The same shape works for future tail-sampling policies
at the gateway tier. Don't over-apply it: indirection has a cost, so externalize only blocks
that are both large and independently ownable.

**Two other patterns, if your org boundaries differ** (described here, not shipped):

- *Split by component type* — `base.yaml` (service + extensions) plus `receivers.yaml`,
  `processors.yaml`, `exporters.yaml`. Fits when separate teams own receivers vs. processors
  vs. exporter destinations. The `service.pipelines` arrays still live in one file.
- *Environment overlays* — a base plus `production.yaml` / `staging.yaml` / `development.yaml`
  that override limits, endpoints, and exporters. Layer this on top of either split. Selected
  at deploy time with an extra `--config file:` flag.

**Merge caveats — these bite silently:**

1. **Arrays are replaced, not merged.** If a base defines `processors: [a, b, c]` and an
   overlay defines `processors: [a, b]`, the result is `[a, b]`, not the union. Keep things
   that vary together — especially a pipeline's processor list — in one file.
2. **`${file:}` paths resolve relative to the collector's working directory**, not the file
   containing the include. Run the collector (and `validate`) from the directory that makes the
   `prometheus/...` paths resolve — i.e. from inside `references/` — or use absolute paths.
3. **`${env:VAR:-default}` defaults apply only when the variable is *unset*.** An exported
   `VAR=""` is not unset, so the default does not kick in. Validate required vars externally
   before start (e.g. `: ${OTLP_EXPORTER_ENDPOINT:?must be set}`).
4. **OCB-built distributions must list the providers.** The file, env, and yaml providers are
   not included by default; add them to the builder manifest, or `${file:}` / `${env:}` URIs
   fail with cryptic scheme errors.
5. **Validate and `print-config` the *merged* set**, never a fragment alone — a single signal
   file references shared processors it does not define and will not validate on its own. See
   [`validating.md`](validating.md).
