---
name: ollygarden-otel-collector-k8s-daemonset
description: OllyGarden's opinionated, optimization-first OpenTelemetry Collector configuration for a Kubernetes node agent (DaemonSet). Use when authoring or reviewing a node-level/agent collector config for logs, metrics, and traces on Kubernetes, or when the user wants to reduce telemetry volume, cost, cardinality, or noise at collection time. Triggers on "collector daemonset config", "node agent collector", "otel collector on kubernetes", "reduce telemetry cost in the collector", "tune kubeletstats/hostmetrics/filelog", "drop noisy spans/logs/metrics in the collector".
license: Apache-2.0
---

# Opinionated OTel Collector — Kubernetes DaemonSet

This skill is OllyGarden's opinion about how a **node-agent collector** (one collector pod
per node, deployed as a DaemonSet) should be configured so that the telemetry leaving the
node is already lean. It layers opinions on top of upstream facts:

- For component config keys, defaults, stability, and renames → the **`otel-collector`** skill.
- For OTTL statement/condition syntax → the **`otel-ottl`** skill.
- For source-side fixes that the collector cannot do → the `ollygarden-otel-*` setup skills.

The companion reference config is [`references/daemonset-collector.yaml`](references/daemonset-collector.yaml).
Read it alongside this file; the prose explains *why*, the YAML shows *how*. Copy it, then
search for `CUSTOMIZE`.

## When this skill applies

Use it for the **agent tier**: a DaemonSet collector that ingests OTLP from workloads on its
node and scrapes node-local sources (kubelet, host, same-node pods, pod log files). It does
**not** cover the **gateway/cluster tier** — a separate Deployment (often a singleton) that
runs `k8s_cluster`/`k8s_events`, tail sampling, and load balancing. Two things that belong
there, not here, are called out in the [Out of scope](#out-of-scope) section.

## The core principle: drop early, drop at the node

Every byte you discard at the node is a byte you never pay to batch, compress, transmit,
re-ingest, or store. The node agent is the **first** place you control the data and the
**cheapest** place to shrink it, so the agent config is where volume/cost/cardinality work
belongs. The rest of this skill is that principle applied signal by signal.

## Non-negotiables (every pipeline, every signal)

These four are not tuning knobs — they are the baseline. Omitting any of them is a bug.

1. **`memory_limiter` is the first processor in every pipeline.** It applies backpressure
   *before* downstream processors allocate buffers, so a traffic spike sheds load instead of
   OOM-killing the collector and dropping everything. First, or it cannot protect the
   allocations that follow it.
2. **Truncate resource attributes last** (`transform ... truncate_all(resource.attributes, 2048)`).
   Kubernetes pod annotations can be hundreds of KB and ride along on every record; cap them
   or one annotation inflates every span/metric/log on the pod.
3. **Enrich, don't fabricate.** `resourcedetection` + `k8sattributes` add real identity
   (cloud, node, namespace, workload). Disable `host.name` in the `system` detector so a pod
   name never masquerades as the node hostname. **Scope the `k8sattributes` informer to the
   local node** (`filter.node_from_env_var: K8S_NODE_NAME`) — without it every DaemonSet replica
   watches every pod in the cluster, which is a large and avoidable memory cost at fleet scale.
   (`resourcedetection` detector *ordering* interacts with `override` and the precedence has
   differed across versions — pin your distro and confirm which detector wins before relying on it.)
4. **Restart-safe state.** Persist filelog read offsets via the `file_storage` extension, so
   a collector restart does not re-read every pod log from the top and duplicate it.

## Metrics: the largest, most reducible bill

Metrics volume is driven by **series count × datapoints-per-minute**. Attack both.

- **Collect a curated set, not the default firehose.** `kubeletstats` and `hostmetrics`
  default to far more than anyone dashboards. The reference config enables an allowlist
  (usage + utilization) and turns the rest off. For `hostmetrics`, prefer the bounded
  `*.utilization` gauges over the per-state monotonic `*.time`/`*.usage` counters, which
  multiply series.
- **Scrape no faster than the signal changes, and split fast from slow.** The reference
  config now ships the **dual-receiver split** baked in: `kubeletstats/main` (container/pod/node)
  at 20s alongside `kubeletstats/volume` at 60s, and `hostmetrics/fast` (cpu/memory) at 60s
  alongside `hostmetrics/slow` (filesystem) at 300s. Finer intervals multiply DPM for metrics
  that barely move.
- **Drop static-volume metrics (secrets, configmaps, serviceaccount tokens).** kubeletstats
  emits `k8s.volume.*` for *every* mounted volume, but `secret` / `configMap` / `downwardAPI`
  / `emptyDir` volumes and the projected serviceaccount-token volume (`kube-api-access-*`) have
  static capacity that never moves — those datapoints are pure DPM waste. The reference config's
  `filter/drop_static_volume_mounts` discards them by `k8s.volume.type` (which requires
  `extra_metadata_labels: [k8s.volume.type]` on the volume receiver). Dropping is strictly
  cheaper than slow-scraping. The kube-state-metrics side of the same data — `kube_secret_*`,
  `kube_configmap_*`, `kube_serviceaccount_*` and the `*_info`/`*_labels` metadata gauges — is
  near-static too; the `kube-state-metrics-metadata` scrape job keeps only those families at 5m.
- **Cut datapoints-per-minute on the metrics you keep but that change slowly**
  (capacity/limits/requests, `*_info`/`*_labels` metadata gauges, replica counts). This is
  OllyGarden's **metric DPM reduction** remediation — see `remediation-metric-dpm-reduction`
  for the full catalog and decision tree. Two patterns, in preference order:
  - **Pattern A — dual-receiver split (preferred, no extra processors; shipped above).** Run the
    same receiver twice over disjoint metric subsets at different `collection_interval`:
    `kubeletstats` volume metrics at 60s while container/pod/node stay at 20s; `hostmetrics`
    `filesystem` at 300s while cpu/memory stay at 60s; two Prometheus scrape jobs splitting
    fast status metrics (30s) from slow `kube_.*_info|_labels|_limits|_requests` (300s) — the
    `kube-state-metrics-metadata` job is the slow half of this (the fast KSM job is left for you
    to add if you want those status metrics). Do NOT just raise the interval on a single
    receiver — that also downsamples the high-information CPU/memory series.
  - **Pattern B — `routing` connector + `interval` processor (fallback, not shipped).** Use when
    the cadence is SDK-set and arrives over OTLP, or the receiver has no partition knob. Route
    the slow families to a pipeline whose `interval` processor re-emits them on a fixed tick;
    keep a `default_pipelines` passthrough (unmatched metrics are dropped silently otherwise).
    `interval` must be longer than the source `collection_interval`, never stack two, and note
    it emits empty pdata between ticks — any "emission rate" alert must filter empties first.
- **Shard Prometheus scraping by node.** Each DaemonSet replica scrapes only pods on its own
  node (`field: spec.nodeName=${K8S_NODE_NAME}`), so N replicas cover a disjoint set instead
  of every replica scraping every pod. Add a slow tier (`5m`) for expensive endpoints and
  drop terminal-phase pods.
- **Kill synthetic Prometheus identity.** The scrape pipeline invents `service.name`
  (= job name) and `service.instance.id` (= host:port). Delete them so the backend resolves
  identity from real resource attributes instead of minting high-cardinality junk.
- **Trim to monitored namespaces.** Node-wide receivers see every namespace; a `filter`
  drops datapoints whose `k8s.namespace.name` is outside your allowlist.

## Logs: cap, dedup at source, and prefer metrics

- **Cap line size** (`max_log_size: 100KiB`). A few runaway lines (serialized payloads,
  stack dumps) otherwise dominate log ingest.
- **Drop low-value severities** you never query (e.g. sub-INFO in production) with a `filter`.
  When severity rides inside a structured body rather than on the record, derive
  `severity_number` first (e.g. `ParseJSON(body)` then map `level`), or the severity filter has
  nothing to match.
- **Dedup repeated log lines at the source — but mind the offset attributes.** `logdedup`
  collapses identical lines over a window, but the `filelog` receiver stamps every record with
  `log.file.path` and (if enabled) `log.file.record_number`, and `logdedup` hashes the
  attributes — so unless you strip those two keys first, dedup matches nothing and is a silent
  no-op. Scope dedup to known-chatty services and strip the offset attributes on the same
  condition immediately before it. See the `otel-collector` skill's `logdedup` page.
- **Access logs are cheaper as metrics.** High-volume HTTP access logs whose value is the
  *aggregate* (request/error rate, latency by route) should be converted to metrics and the
  raw records dropped — OllyGarden's **access-log-to-metrics** remediation. Three opinions that
  are easy to get wrong: emit the semconv `http.server.request.duration` **exponential
  histogram** via a `signal_to_metrics` connector (its count is the request volume, a filtered
  count is the error rate) — do NOT invent an `http.server.request.count` sum, semconv has no
  request counter; put the `batch` processor **before** the connector, since it aggregates per
  incoming batch; and note `signal_to_metrics` is a **contrib-only** connector, so confirm your
  distro ships it. This pipeline is owned end-to-end (with a validated reproducer) by
  `remediation-access-log-to-metrics`; use that skill rather than rebuilding it here.
- **Some log fixes are source-side, not collector-side.** Unstructured logs that bake data
  into the message string are fixed in app code (structured logging with semconv field
  names), not by a brittle collector regex — see `remediation-structured-logging-migration`.
  Point the user at the source fix rather than implying the collector covers it.

## Traces: drop noise here, sample at the gateway

- **Drop probe spans** (health/readiness/liveness). The probe path lands on `http.route`
  (stable semconv), `url.path` (current), or the deprecated `http.target` depending on the
  instrumentation, so the reference filter checks all three; and many frameworks name the span
  after the handler (Spring → `HealthController.health`, or bare method names like `getStatus` /
  `isReady`) so there is no `/health` string to match — match the span `name` too. Anchor the
  name match (`\b…\b`); do **not** copy unanchored field globs like `"*/health.*"` — that is not
  a valid RE2 anchor and silently matches the wrong spans. Probe spans have been measured at
  ~28% of all spans in real fleets. There is no agent-side knob for this in the Java
  instrumentation, so the collector is the right place — see `remediation-java-agent-hygiene`.
- **Drop static-asset spans** (`.css`, `.js`, images, fonts, `.map`). These are high-volume
  and never the subject of a latency investigation. The **preferred** fix is at the source —
  suppress the span in nginx / ingress-nginx (`remediation-nginx-static-asset-tracing`); the
  collector `filter` on `url.path` is the portable fallback when you do not control the proxy.
- **Do not head-sample on the agent for cost.** Probabilistic head sampling here saves money
  but makes per-node keep decisions blind to the whole trace. Real trace reduction is
  tail-based and belongs at the gateway tier (`tail_sampling` + `load_balancing`), where a
  whole trace is visible. Keep the agent lossless except for the deterministic noise drops
  above. (See [Out of scope](#out-of-scope).)

## Self-monitoring: watch the collector, cheaply

Run the collector's internal telemetry at `level: detailed` but drop the noisiest,
highest-cardinality internal series with metric `views` (e.g. `otelcol.k8s.pod.association`,
`http.*`/`rpc.*` client/server histograms), and report on a 30s reader. You want to see queue
depth and refusals without the agent's self-telemetry becoming its own cost line.

## Out of scope

These belong in the gateway/cluster collector, not the node agent:

- **Tail sampling and load balancing.** A whole-trace keep/drop decision needs every span of
  a trace in one place; on a node agent you only have the local spans. Run `tail_sampling`
  behind a `load_balancing` exporter in the gateway tier.
- **Cluster-singleton metrics.** `k8s_cluster` and `k8s_events` must run once per cluster, not
  once per node — otherwise every node double-counts them. Their tuning (e.g. dropping
  zero-value replicaset datapoints, disabling `k8s.namespace.phase`) lives in that Deployment.

## Verify before shipping

Validate the config against the collector binary that will run it:

```sh
otelcol-contrib validate --config references/daemonset-collector.yaml
```

`validate` checks structure, component existence, and OTTL syntax, and also instantiates the
pipeline. Several errors are pure **off-cluster** artifacts: cloud detectors in
`resourcedetection` (e.g. `eks`) and `kubeletstats` `auth_type: serviceAccount` (it reads the
SA CA cert at build time) fail because there is no Kubernetes API or service-account mount, and
`hostmetrics` `root_path: /hostfs` needs the host mount. They disappear when the DaemonSet runs
in the cluster. A genuine config error (a bad OTTL statement, an unknown component, a misspelled
key) surfaces during the same phase, so they can mask one: the build aborts at the *first*
failure. To force the **whole** pipeline to build off-cluster — and thus compile every OTTL
filter/transform downstream of `resourcedetection` — validate a throwaway overlay with the cloud
detectors swapped for `[env]` and `kubeletstats` `auth_type: none`; a clean run then means all
components instantiated and all OTTL compiled. (Validated this way on `otelcol-contrib`
v0.154.0.)

`validate` does not check that env vars resolve or that OTTL matches your data. After it
passes, confirm the filters actually drop what you intend with a `debug` exporter and a sample
of real telemetry (see the `otel-collector` skill's verification guidance).

## Cross-references

- Component facts: **`otel-collector`** (receivers/processors/exporters/connectors, renames).
- OTTL: **`otel-ottl`** (the conditions and statements in the filter/transform blocks).
- Optimization remediations this config draws on or defers to:
  - `remediation-metric-dpm-reduction` — dual-receiver split / `interval` patterns and the
    per-metric target-interval catalog.
  - `remediation-access-log-to-metrics` — the full access-log → `signaltometrics` pipeline.
  - `remediation-nginx-static-asset-tracing` — source-side span suppression for static assets.
  - `remediation-java-agent-hygiene` — health-check filtering plus the agent-side knobs.
  - `remediation-structured-logging-migration` — app-code structured logging.
- Source-side fixes the collector can't make: `ollygarden-otel-sdk-setup`,
  `ollygarden-otel-manual-instrumentation`, and the language `ollygarden-otel-*-setup` skills.
