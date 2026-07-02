# Verify before shipping

Companion reference for the `ollygarden-otel-collector-k8s-daemonset` skill. The SKILL.md
summarizes this; the detail lives here.

Validate the config against the collector binary that will run it:

```sh
# Run from inside references/ so the ${file:} include paths resolve
# (arrays/paths caveat in decomposing-config.md).
cd references
otelcol-contrib validate \
  --config file:common.yaml \
  --config file:traces.yaml \
  --config file:metrics.yaml \
  --config file:logs.yaml
```

Inspect the fully-merged, env-substituted result (useful for debugging merge or include
issues) with `print-config` and the same `--config` flags:

```sh
otelcol-contrib print-config \
  --config file:common.yaml --config file:traces.yaml \
  --config file:metrics.yaml --config file:logs.yaml
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
components instantiated and all OTTL compiled. (Validated this way on `otelcol-contrib` v0.155.0.)

`validate` does not check that env vars resolve or that OTTL matches your data. After it
passes, confirm the filters actually drop what you intend with a `debug` exporter and a sample
of real telemetry (see the `otel-collector` skill's verification guidance).
