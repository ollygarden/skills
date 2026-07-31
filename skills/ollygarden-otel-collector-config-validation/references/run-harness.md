# Approved local run recipe

Use this only after the user approves the exact image reference. Substitute the reviewed harness
and telemetrygen command; do not execute placeholders.

```bash
set -euo pipefail

if command -v podman >/dev/null 2>&1; then
  OTEL_TEST_RUNTIME=podman
elif command -v docker >/dev/null 2>&1; then
  OTEL_TEST_RUNTIME=docker
else
  echo "need Docker or Podman" >&2
  exit 1
fi

OTEL_TEST_IMAGE='docker.io/otel/opentelemetry-collector-contrib:0.156.0@sha256:125bdbeb7590cc1952c5b3430ecf14063568980c2c93d5b38676cc0446ed8108'
OTEL_TEST_DIR=$(mktemp -d)
OTEL_TEST_NAME="otelcol-verify-$$"
OTEL_TEST_SELINUX=

cp ./harness.yaml "$OTEL_TEST_DIR/harness.yaml"
mkdir "$OTEL_TEST_DIR/out"

if command -v getenforce >/dev/null 2>&1 && [ "$(getenforce)" = Enforcing ]; then
  OTEL_TEST_SELINUX=:Z
fi

cleanup() {
  "$OTEL_TEST_RUNTIME" rm -f "$OTEL_TEST_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

OTEL_TEST_USER_ARGS="--user $(id -u):$(id -g)"
if [ "$OTEL_TEST_RUNTIME" = podman ] && \
   [ "$(podman info --format '{{.Host.Security.Rootless}}' 2>/dev/null)" = true ]; then
  OTEL_TEST_USER_ARGS=
fi

"$OTEL_TEST_RUNTIME" run -d --rm --name "$OTEL_TEST_NAME" \
  -p 127.0.0.1:4317:4317 \
  $OTEL_TEST_USER_ARGS \
  -v "$OTEL_TEST_DIR/harness.yaml:/etc/otelcol-contrib/config.yaml:ro$OTEL_TEST_SELINUX" \
  -v "$OTEL_TEST_DIR/out:/output$OTEL_TEST_SELINUX" \
  "$OTEL_TEST_IMAGE" --config=/etc/otelcol-contrib/config.yaml

OTEL_TEST_ATTEMPTS=0
until "$OTEL_TEST_RUNTIME" logs "$OTEL_TEST_NAME" 2>&1 | grep -q "Everything is ready"; do
  if [ "$("$OTEL_TEST_RUNTIME" inspect -f '{{.State.Running}}' "$OTEL_TEST_NAME" 2>/dev/null)" != true ]; then
    echo "collector exited before readiness" >&2
    exit 1
  fi
  OTEL_TEST_ATTEMPTS=$((OTEL_TEST_ATTEMPTS + 1))
  if [ "$OTEL_TEST_ATTEMPTS" -ge 120 ]; then
    echo "collector readiness timed out" >&2
    exit 1
  fi
  sleep 0.25
done

# Run the reviewed telemetrygen command here.

"$OTEL_TEST_RUNTIME" stop "$OTEL_TEST_NAME"
```

Inspect `$OTEL_TEST_DIR/out` before removing the scratch directory. Use a distinct scratch directory
for every positive/negative or routing case so outputs cannot be conflated. Record the image digest,
Collector logs, generated markers, assertion commands, and output excerpts.
