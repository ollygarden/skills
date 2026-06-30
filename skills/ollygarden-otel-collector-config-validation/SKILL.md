---
name: ollygarden-otel-collector-config-validation
description: OllyGarden's end-to-end method for validating an OpenTelemetry Collector config by running it — proving a processor or connector transforms, drops, or routes telemetry as intended, not just that the YAML parses. Use whenever someone wants to test, verify, or prove a Collector processor or connector (filter, transform, attributes, redaction, tail_sampling, interval, routing, signaltometrics, count, spanmetrics) against realistic telemetry. Triggers on phrasings like "does my filter actually drop the right spans", "prove this transform works before I ship it", "otelcol validate passes but the rule does the wrong thing", "spin up a throwaway collector and inspect the output". Runs otelcol-contrib validate, then a real collector in Docker or Podman fed by telemetrygen with a file exporter, and asserts the output. Prefer over otel-collector or otel-ottl when the goal is to behaviorally test a config, not look up syntax. Processors and connectors only; receivers/exporters become an OTLP-in / file-out harness.
license: Apache-2.0
---

# Validating an OTel Collector config — end to end

This skill is OllyGarden's opinion that **validating a collector config means an end-to-end
behavioral test, not a structural one**. `otelcol validate` tells you the YAML parses and the
components exist; it does **not** tell you the `filter` drops the spans you meant, the
`transform` sets the attribute you expect, or the `routing` connector sends each signal down
the right pipeline. The only way to know that is to run the component under test against the
*exact shape* of telemetry it will see and read back what comes out.

It layers on upstream facts — point at these rather than duplicating them:

- Component config keys, defaults, signal support, renames → the **`otel-collector`** skill.
- OTTL statement/condition syntax in `filter`/`transform`/`routing` → the **`otel-ottl`** skill.
- `telemetrygen` flags and the bare verify recipe → the **`otel-telemetrygen`** skill. This
  skill is the disciplined, repeatable workflow built on that recipe.

## Scope: processors and connectors only

Validate the component **under test** — a processor (`transform`, `filter`, `attributes`,
`redaction`, `tail_sampling`, `interval`, …) or a connector (`routing`, `signaltometrics`,
`count`, `spanmetrics`, …). The real receivers and exporters of the production config are
**not** under test here; they are replaced by a fixed harness:

- **In:** an `otlp` receiver, so `telemetrygen` can feed it.
- **Out:** a `file` exporter, so the result is inspectable JSON on disk.

This isolates the behavior you care about. Testing the production `kafka`/`prometheus`/vendor
exporters is a different job (connectivity, auth, backpressure) and out of scope. If the
config's *receivers* are what's in question (scrape configs, filelog operators), that is also
out of scope — this skill assumes telemetry arrives over OTLP.

## The five stages

Run them in order. Stage 1 is cheap and catches typos; stages 2–5 catch the bugs that matter.

### Stage 1 — Static validate

```sh
otelcol-contrib validate --config harness.yaml
```

This checks structure, component existence, and OTTL syntax, and instantiates the pipeline.
It does **not** check that env vars resolve, that OTTL matches your data, or that routing
sends data where you think. A clean `validate` is necessary, never sufficient. (See the
`ollygarden-otel-collector-k8s-daemonset` skill for the off-cluster caveats of `validate`.)

### Stage 2 — Build the harness config

Wrap the component under test between an `otlp` receiver and a `file` exporter. Keep the
component's config **byte-for-byte identical** to the production config — copy it, do not
retype it, or you are testing a different component.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317      # 0.0.0.0, not localhost — reachable from the container's view

processors:
  # OPTIONAL: shape the input telemetrygen can't express (span name, kind, specific attrs).
  transform/setup:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - set(name, "GET /health")

  # THE COMPONENT UNDER TEST — copied verbatim from the production config.
  filter/under_test:
    error_mode: ignore
    traces:
      span:
        - 'IsMatch(name, "GET /health.*")'

exporters:
  file:
    path: /output/result.json
    flush_interval: 200ms

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [transform/setup, filter/under_test]
      exporters: [file]
```

**Connectors take two pipelines.** A connector is an exporter in its source pipeline and a
receiver in its destination pipeline. Wire both, with a `file` exporter on the destination:

```yaml
connectors:
  routing/under_test:
    default_pipelines: [traces/other]
    table:
      - context: span
        condition: 'attributes["http.route"] == "/checkout"'
        pipelines: [traces/checkout]

service:
  pipelines:
    traces/in:        { receivers: [otlp],              exporters: [routing/under_test] }
    traces/checkout:  { receivers: [routing/under_test], exporters: [file/checkout] }
    traces/other:     { receivers: [routing/under_test], exporters: [file/other] }
```

Give each route its **own** `file` exporter (`file/checkout`, `file/other`) so you can assert
*where* each record landed, not just that it survived. For metric-producing connectors
(`signaltometrics`, `count`, `spanmetrics`) the destination pipeline is a `metrics` pipeline —
assert on the emitted series and remember the count/sum semantics described in `otel-collector`.

### Stage 3 — Pick a container runtime (Docker or Podman, + SELinux)

Use whichever is installed; the run command is nearly identical:

```sh
if command -v podman >/dev/null 2>&1; then RUNTIME=podman
elif command -v docker >/dev/null 2>&1; then RUNTIME=docker
else echo "need docker or podman" >&2; exit 1; fi
```

**SELinux bind-mount relabeling.** On SELinux systems (Fedora, RHEL, CentOS Stream) a bind
mount is unreadable inside the container unless the host path is relabeled. Append the **`:Z`**
flag to each bind mount so the runtime relabels it with a container-private SELinux category:

```sh
SEL=""
if command -v getenforce >/dev/null 2>&1 && [ "$(getenforce)" = "Enforcing" ]; then SEL=":Z"; fi
```

- **`:Z` (uppercase) = private**, unshared label — correct for these single-collector scratch
  mounts. `:z` (lowercase) is the *shared* label for paths several containers mount at once;
  you don't need it here.
- **Only relabel scratch paths.** `:Z` rewrites the SELinux label of the host path in place.
  Pointing it at a path other processes also use (a shared config dir, `$HOME`) can break their
  access. Mount a throwaway copy of the config and a fresh output dir — never `:Z` a path you
  don't own.
- Off SELinux, leave the suffix empty (`SEL=""`); an unnecessary `:Z` is at best a no-op and at
  worst relabels a host path for nothing.

### Stage 4 — Run the collector and generate the telemetry shape

Work in a scratch directory with `harness.yaml` from Stage 2 in it — a throwaway copy you're
willing to let `:Z` relabel (see Stage 3), never your only copy of a shared config.

```sh
mkdir -p ./out

$RUNTIME run -d --rm --name otelcol-verify \
  --network host \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)/harness.yaml:/etc/otelcol-contrib/config.yaml:ro$SEL" \
  -v "$(pwd)/out:/output$SEL" \
  otel/opentelemetry-collector-contrib:0.155.0 \
  --config=/etc/otelcol-contrib/config.yaml

# wait until the collector reports ready, then feed it. Grepping the runtime's own
# logs is portable — it works on any host OS and whether you used host or bridge
# networking, unlike a host-side port probe (ss/nc aren't on macOS).
until $RUNTIME logs otelcol-verify 2>&1 | grep -q "Everything is ready"; do sleep 0.25; done
telemetrygen traces --otlp-insecure --traces 1 --service "checkout"
```

Generate the *exact* shape the component is supposed to act on — matching `service.name`,
resource and telemetry attributes, span kind, severity, metric type. See the **`otel-telemetrygen`**
skill for the flags; what telemetrygen can't set directly (span name, span kind, renames), set
with the `transform/setup` processor from Stage 2.

Two runtime caveats:

- **`--user "$(id -u):$(id -g)"`** lets the `file` exporter write to the bind-mounted output
  dir as you. On **rootless Podman** the container already runs as your user, so this flag is
  usually unnecessary and can even mismap — drop it if the file exporter can't write.
- **`--network host`** lets `telemetrygen` on the host reach `localhost:4317`. It works cleanly
  on Linux. On **Docker Desktop (macOS/Windows)** host networking is limited; instead publish
  the port (`-p 4317:4317`) and keep targeting `localhost:4317`, or run telemetrygen as a second
  container on a shared network.
- **Pin a recent release tag** — `0.155.0` above is illustrative; use the current released
  version so the component under test behaves as it will in production. Mind the tag formats:
  the Docker Hub `otel/opentelemetry-collector-contrib` image is **unprefixed** (`:0.155.0`),
  while the ghcr `telemetrygen` image is **`v`-prefixed** (`:v0.155.0`). See `otel-telemetrygen`
  for the telemetrygen image.

### Stage 5 — Assert the output

Stop the collector first to flush the file exporter, then read the JSON back and **assert on
its contents**. "No error in the logs" is not a pass.

```sh
$RUNTIME stop otelcol-verify           # flushes the file exporter
python3 -m json.tool ./out/result.json # or: jq . ./out/result.json
```

Assert the **transformation**, not just the presence of output:

- **A `filter`/drop rule** — run it twice. Send a record that *should* be dropped and assert the
  matching route's output is empty; then send one that should *survive* and assert it's present.
  Empty output alone is ambiguous: it also happens when the collector crashed or never received
  data. Both halves are required.
- **A `transform`/`attributes` rule** — assert the specific attribute/field has the new value in
  the output record, not merely that a record came through.
- **A `routing` connector** — assert each record landed in the *right* per-route file and is
  *absent* from the others. Don't forget a record that matches no rule: confirm it went to
  `default_pipelines` (and isn't silently dropped).
- **A metric-producing connector** — assert the expected series name, type, and that its
  datapoint value reflects the input volume/condition (e.g. an error-filtered count equals the
  number of error inputs).

## Pitfalls

- **Trusting `validate`.** It is stage 1 of 5. A config that validates can still drop the wrong
  spans or route to the wrong pipeline.
- **Re-typing the component under test.** Copy it from the production config; a hand-retyped
  approximation tests a config you'll never ship.
- **Asserting "something came out".** Survival ≠ correctness. Assert the changed value, or the
  specific route, or the emitted series.
- **One-sided filter tests.** Only checking that matching records are gone (or only that
  non-matching survive) misses the half where the rule is too greedy or too lax.
- **`endpoint: localhost:4317` in the harness.** Inside the container that binds the loopback
  interface only; use `0.0.0.0:4317` so the receiver is reachable.
- **Forgetting `default_pipelines` on `routing`.** Unmatched telemetry is dropped silently —
  if your test only sends matching data you won't notice the hole.
- **Reading the file before the collector flushed.** Stop the container (or wait past
  `flush_interval`) before asserting, or you'll read a partial/empty file.

## Cross-references

- Component facts (keys, defaults, signal support, connector semantics): **`otel-collector`**.
- OTTL in the filter/transform/routing rules under test: **`otel-ottl`**.
- `telemetrygen` flags and the underlying verify recipe: **`otel-telemetrygen`**.
- `validate`'s off-cluster caveats and the broader "verify before shipping" stance:
  **`ollygarden-otel-collector-k8s-daemonset`**.
