# Verify before shipping

Commands below were captured with `otelcol-contrib` v0.155.0 on 2026-07-31. Run them against the
exact distribution/version being deployed; component availability and validation behavior vary.

Set non-secret representative values before validation. Do not put production credentials into
shell history or retained transcripts.

```sh
# Run from inside references/ so the ${file:} include paths resolve
# (arrays/paths caveat in decomposing-config.md).
cd references
export K8S_NODE_NAME=synthetic-node
export K8S_CLUSTER_NAME=synthetic-cluster
export OTLP_EXPORTER_ENDPOINT=127.0.0.1:4317
otelcol-contrib validate \
  --config file:common.yaml \
  --config file:traces.yaml \
  --config file:metrics.yaml \
  --config file:logs.yaml
```

Inspect the fully merged, env-substituted result with `print-config` and the same flags:

```sh
otelcol-contrib print-config \
  --config file:common.yaml --config file:traces.yaml \
  --config file:metrics.yaml --config file:logs.yaml
```

Assert that the printed result contains all three pipelines, `memory_limiter` first in each,
`transform/truncate_resources` after signal-specific transforms/filters, and all three included
Prometheus jobs. A successful command without this inspection does not prove the merge was correct.

`validate` checks structure, component existence, and OTTL syntax, and also instantiates the
pipeline. Several errors are pure **off-cluster** artifacts: cloud detectors in
`resourcedetection` (e.g. `eks`) and `kubeletstats` `auth_type: serviceAccount` (it reads the
SA CA cert at build time) fail because there is no Kubernetes API or service-account mount, and
`hostmetrics` `root_path: /hostfs` needs the host mount. They disappear when the DaemonSet runs
in the cluster. A genuine config error (a bad OTTL statement, an unknown component, a misspelled
key) surfaces during the same phase, so they can mask one: the build aborts at the *first*
failure. To force the **whole** pipeline to build off-cluster—and thus compile every OTTL
filter/transform downstream of `resourcedetection`—validate a throwaway overlay with the cloud
detectors swapped for `[env]` and `kubeletstats` `auth_type: none`; a clean run then means all
components instantiated and all OTTL compiled. (Validated this way on `otelcol-contrib` v0.155.0;
re-run it against the pinned deployment version rather than treating that stamp as evergreen.)

`validate` does not prove that runtime environment values are correct, that workloads reach their
own node agent, or that OTTL matches real telemetry. After it passes, use sanitized representative
telemetry and the `otel-collector` verification workflow to prove intended records are dropped and
near-miss controls remain. Do not test against production ingest/export endpoints.
