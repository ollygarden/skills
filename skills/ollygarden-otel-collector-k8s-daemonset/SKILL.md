---
name: ollygarden-otel-collector-k8s-daemonset
description: OllyGarden's opinionated, optimization-first OpenTelemetry Collector configuration for a Kubernetes node agent (DaemonSet). Use when authoring or reviewing a node-level/agent collector config for logs, metrics, and traces on Kubernetes, or when the user wants to reduce telemetry volume, cost, cardinality, or noise at collection time. Triggers on "collector daemonset config", "node agent collector", "otel collector on kubernetes", "reduce telemetry cost in the collector", "tune kubeletstats/hostmetrics/filelog", "drop noisy spans/logs/metrics in the collector".
license: Apache-2.0
---

# Opinionated OTel Collector — Kubernetes DaemonSet

Use this skill for the **agent tier**: one collector per node ingesting node-local OTLP,
kubelet/host metrics, same-node Prometheus targets, and pod logs. Use a separate gateway or
cluster Deployment for `tail_sampling`, `load_balancing`, `k8s_cluster`, and `k8s_events`.

This repository owns OllyGarden's decisions, not component facts. Consult `otel-collector` for
current component keys, defaults, and stability; `otel-ottl` for syntax; and the relevant
`ollygarden-otel-*` setup skill for source-side fixes.

## Non-negotiable pipeline contract

Apply these to traces, metrics, and logs:

1. Put `memory_limiter` first so backpressure happens before downstream buffering.
2. Enrich with real identity; do not fabricate it. Scope `k8sattributes` to the local node with
   `filter.node_from_env_var: K8S_NODE_NAME`, disable the system detector's `host.name`, and verify
   detector order/`override` against the pinned Collector distribution.
3. Put resource-value truncation last among transforms. Kubernetes metadata can otherwise inflate
   every record.
4. Persist `filelog` offsets with `file_storage` on host-backed storage. Container-local storage
   loses offsets when the pod is recreated.

The OTLP listener binding alone does not make ingest node-local. The DaemonSet deployment must
route each workload to the agent on its own node. Confirm the networking topology before claiming
the agent/gateway boundary holds.

## Metrics: reduce series and cadence

Metric cost is series count × datapoints per minute. The references implement these decisions:

- Curate `kubeletstats` and `hostmetrics`; prefer bounded utilization measurements over redundant
  per-state series.
- Split fast and slow groups into disjoint receiver instances. Keep container/pod/node metrics at
  20s, volume metrics at 60s, CPU/memory at 60s, and filesystem at 300s. Do not slow a single
  receiver globally and lose useful CPU/memory resolution.
- Drop read-only `secret`, `configMap`, `downwardAPI`, and projected service-account-token volume
  metrics. Retain `emptyDir`: its writable usage is a disk-pressure signal.
- Scrape each pod only from the agent on its node using
  `field: spec.nodeName=${env:K8S_NODE_NAME}`; use a separate slow scrape for expensive endpoints
  and discard terminal pods.
- Remove Prometheus-generated `service.name` and `service.instance.id` when real Kubernetes
  resource identity is available, and filter to monitored namespaces.

The preferred DPM pattern is separate receivers over disjoint subsets. For SDK-set OTLP cadence or
receivers without a partition knob, defer the `routing` connector + `interval` processor fallback
to `remediation-metric-dpm-reduction`; unmatched passthrough and empty emissions make that pattern
unsafe to improvise here.

## Logs: cap and scope

- Cap individual pod-log records (`max_log_size: 100KiB`) and exclude the collector's own logs.
- Drop low-value severities only after structured records have a usable `severity_number`.
- Deduplicate only known-chatty services. Immediately before scoped `logdedup`, remove
  `log.file.path` and `log.file.record_number` under the same condition or those changing offsets
  defeat the hash. The shipped YAML deliberately does not enable dedup without a service-specific
  scope; consult the `otel-collector` `logdedup` reference before adding it.
- Convert high-volume access logs to metrics only through the validated
  `remediation-access-log-to-metrics` workflow. Keep `batch` before its connector and confirm the
  pinned distribution includes the required contrib component.
- Fix telemetry values embedded in message text at the application with
  `remediation-structured-logging-migration`, not brittle Collector regexes.

## Traces: deterministic noise only

- Drop probe spans using the bounded route/path/name patterns in `references/traces.yaml`; the
  filters cover current and legacy HTTP attributes plus framework handler names. Keep regexes
  anchored.
- Prefer source-side suppression for static assets
  (`remediation-nginx-static-asset-tracing`); use the Collector filter as a portable fallback.
- Do not probabilistically head-sample at the agent for cost. Keep the agent lossless except for
  reviewed deterministic noise filters; whole-trace reduction requires gateway
  `tail_sampling` behind `load_balancing`.

## Self-monitoring

Use detailed internal telemetry at a modest reporting interval, with views dropping the noisiest
high-cardinality internal series. Retain queue, refusal, and export-failure visibility so savings do
not hide an unhealthy collector.

## Reference configuration

Copy the full set and search for `CUSTOMIZE`:

- `references/common.yaml` — shared receiver, processors, exporter, state, and self-telemetry.
- `references/traces.yaml`, `metrics.yaml`, `logs.yaml` — one complete signal pipeline each.
- `references/prometheus/*.yaml` — bare scrape-job fragments included by `metrics.yaml`.

Read `references/decomposing-config.md` before editing. Processor arrays replace rather than merge,
and `${file:}` paths depend on the Collector working directory.

## Verify before shipping

Complete every gate below; a parser-only or single-fragment check is not verification:

1. Obtain `common.yaml`, `traces.yaml`, `metrics.yaml`, and `logs.yaml`; if one is missing, stop and
   request it. From `references/`, validate all four together against the pinned distribution.
2. Supply non-secret synthetic `K8S_NODE_NAME`, `K8S_CLUSTER_NAME`, and exporter endpoint values,
   then inspect `print-config` output for all pipelines, processor order, and included scrape jobs.
3. Use sanitized positive and near-miss telemetry to prove each filter drops only its intended
   target. Never use production ingest/export endpoints for verification.

Follow `references/validating.md` for the exact commands, disposable off-cluster overlay, and
version limits.

## Handoffs

- Component configuration and OTTL: `otel-collector`, `otel-ottl`.
- Generic deep-merge mechanics: `ollygarden-otel-collector-config-decomposition`.
- DPM reduction: `remediation-metric-dpm-reduction`.
- Access logs to metrics: `remediation-access-log-to-metrics`.
- Probe/static/source logging fixes: `remediation-java-agent-hygiene`,
  `remediation-nginx-static-asset-tracing`, `remediation-structured-logging-migration`.
