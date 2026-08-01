# Decomposing this config

This reference records only this skill's file layout. Generic deep-merge behavior, providers, and
alternative split strategies belong to `ollygarden-otel-collector-config-decomposition`.

The config is decomposed **by signal pipeline**.

[`common.yaml`](common.yaml) owns shared components. [`traces.yaml`](traces.yaml),
[`metrics.yaml`](metrics.yaml), and [`logs.yaml`](logs.yaml) each own their signal-specific
components and complete `service.pipelines.<signal>` entry.

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

Two caveats are binding: a pipeline's `processors:` array is replaced, not merged, so its owning
signal file contains the complete list; `${file:prometheus/...}` resolves from the Collector's
working directory, so run from `references/` (or use absolute paths). Validate the merged set with
[`validating.md`](validating.md), never one fragment.
