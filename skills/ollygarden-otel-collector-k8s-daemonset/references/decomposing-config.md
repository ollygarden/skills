# Decomposing this config

Companion reference for the `ollygarden-otel-collector-k8s-daemonset` skill. It records how
*this* reference config is laid out across files. The **generic mechanics** — the deep-merge
behavior that reassembles the files, the file/env/yaml providers, the alternative split
strategies, and the caveats that bite silently — live in the
**`ollygarden-otel-collector-config-decomposition`** skill. Read that skill first; this file
does not restate it.

This config is decomposed **by signal pipeline**, because a single ~470-line collector YAML is
painful to review, test, and vary, and this skill's guidance is already organized signal by
signal.

**The file set.** [`common.yaml`](common.yaml) holds everything shared by all three pipelines,
defined once: the `otlp` receiver, `memory_limiter`, `resourcedetection`, `k8sattributes`,
`resource/clustername`, `transform/truncate_resources`, `batch`, the `otlp` exporter, the
`file_storage` extension, and `service.telemetry`. Each of [`traces.yaml`](traces.yaml),
[`metrics.yaml`](metrics.yaml), and [`logs.yaml`](logs.yaml) is self-contained for its signal:
its own signal-specific receivers and processors plus its own `service.pipelines.<signal>`
entry.

**Nested inclusion.** The Prometheus receiver's three scrape jobs are the one block large and
independent enough to externalize, so each lives as a bare-fragment file under
[`prometheus/`](prometheus/) and is pulled in with the file provider:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - ${file:prometheus/scrape-pods.yaml}
        - ${file:prometheus/scrape-pods-slow.yaml}
        - ${file:prometheus/scrape-kube-state-metrics.yaml}
```

The same shape would fit future tail-sampling policies at the gateway tier.

**Editing this set safely.** Two caveats from the decomposition skill matter most here:
a pipeline's `processors:` **array** is replaced (not merged) on overlay, so keep each
pipeline's processor list in the one file that owns it; and `${file:prometheus/...}` paths
resolve relative to the collector's **working directory**, so run the collector and `validate`
from inside `references/` (or use absolute paths). Validate the **merged** set, never a single
fragment — see [`validating.md`](validating.md).
