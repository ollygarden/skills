---
name: ollygarden-otel-collector-config-validation
description: Behaviorally validate an OpenTelemetry Collector processor or connector against realistic telemetry. Use for "does my filter drop the right spans?", "prove this transform before shipping", "validate passes but behavior is wrong", or testing filter, transform, redaction, tail_sampling, routing, signaltometrics, count, or spanmetrics. Running the harness executes a pinned remote container and requires explicit confirmation. Not for syntax lookup (use `otel-collector`/`otel-ottl`), generic telemetry generation (`otel-telemetrygen`), or receiver/exporter testing.
license: Apache-2.0
---

# Validate Collector behavior end to end

`otelcol validate` proves structure, not behavior. Prove the component under test against the
exact telemetry shape it will receive, then assert the transformed, dropped, or routed result.

Use upstream skills for volatile facts:

- `otel-collector` — component keys, signal support, stability, and connector semantics.
- `otel-ottl` — filter, transform, and routing expressions.
- `otel-telemetrygen` — current flags and supported input shapes.

## Scope and invariants

This workflow tests one processor or connector. Replace production ingress and egress with OTLP-in
and file-out; receiver scraping, exporter connectivity, authentication, and backpressure are other
tests. Copy the production **component block** unchanged. Harness names, receivers, exporters, and
pipeline wiring may differ, but retyping the component means testing a different config.

Never mutate the production file. Work from a throwaway copy and keep every generated artifact in
a fresh scratch directory.

## Workflow

### 1. Pin the target and validate statically

Identify the deployed Collector distribution and version. Confirm it contains the component, then
run its matching binary against the harness:

```sh
otelcol-contrib validate --config harness.yaml
```

Do not validate with one version and execute another. A clean result is required but does not prove
environment substitution, data matching, routing, or output. State that limitation explicitly in
the final plan; do not let static validation appear to be behavioral evidence.

### 2. Build the isolated harness

Read [`references/harnesses.md`](references/harnesses.md). Use `0.0.0.0:4317` inside the container,
one file exporter per asserted destination, and a separate setup transform only when telemetrygen
cannot express the input shape. The component under test stays unchanged.

Define every case before running:

| Component | Required evidence |
| --- | --- |
| Filter/drop | A matching record is absent **and** a non-matching record is present. |
| Transform/attributes | The exact target field has the expected value. |
| Routing | Each record is present only in its expected route; unmatched input reaches `default_pipelines`. |
| Metric-producing connector | Expected series name, type, and datapoint value match the input count/condition. |

Use a separate scratch output per case. Empty output alone is never a pass: it can also mean the
Collector crashed or received nothing.

### 3. Preflight remote execution and request confirmation

Determine Docker or Podman, whether SELinux is enforcing, host UID/GID behavior, port availability,
and the exact immutable image for the deployed version.

**Get explicit user confirmation before pulling or running remote container code.** Show the exact
registry, image, tag, and digest; explain that the runtime may download and execute that image; then
wait for an affirmative response. The original validation request is not consent to pull or run it.

Known example, captured 2026-07 (use only when it matches the target version):

```text
docker.io/otel/opentelemetry-collector-contrib:0.156.0@sha256:125bdbeb7590cc1952c5b3430ecf14063568980c2c93d5b38676cc0446ed8108
```

Never execute a tag-only reference. Re-resolve and review the digest when changing the tag.
If the user did not supply a deployed version, present the exact known example above as a candidate
and ask them to approve it or provide the target version. Do not replace the tag or digest with a
placeholder, and do not execute until one exact reference is confirmed.

On enforcing SELinux, `:Z` privately relabels a host path in place. Apply it only to the fresh
scratch config copy and output directory—never a shared directory, home directory, or sole config
copy. Publish the unauthenticated test receiver on host loopback only.

Before stopping for approval, the preflight must explicitly include all of these review items:

- exact registry/image/tag/digest and the statement that it may be downloaded and executed;
- fresh scratch paths and the host-label mutation risk of private `:Z` relabeling;
- host `127.0.0.1` publication with in-container `0.0.0.0` binding;
- host UID/GID behavior, including the rootless Podman exception;
- bounded readiness/exit detection, cleanup, stop-to-flush, and the exact value assertion.

Use an unambiguous disclosure: **“This may download and execute remote container code.”** Do not
soften it to “pull an image” or assume the user understands what a container run executes.

### 4. Run only after approval

After the exact image is approved, read [`references/run-harness.md`](references/run-harness.md).
Its bounded readiness check must fail if the container exits or never becomes ready, and its cleanup
trap must remove the test container. On rootless Podman, omit `--user` if UID mapping prevents output.

Generate the exact signal, resource attributes, telemetry attributes, name, kind, severity, and
metric type required by each case. Never send telemetry after failed startup.

### 5. Flush and assert

Stop the Collector before reading output so the file exporter flushes. Parse the configured file
format, confirm the Collector received the positive control, and evaluate every presence, absence,
route, and value assertion. Preserve the commands, input markers, output excerpts, Collector version,
image digest, and result for review. “No errors” and “something came out” are not assertions.
