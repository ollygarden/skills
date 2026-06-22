# Propagation

Preserve trace continuity across boundaries.

## Rules

At inbound boundaries:
- extract incoming trace context
- start the server or consumer span from that extracted context

At outbound boundaries:
- inject trace context into headers, metadata, or message properties

Across internal calls:
- preserve the active context instead of starting disconnected traces
- spans link to their parent **only** through the active context; if it does not reach a downstream
  DB/client call, that call's span detaches into a separate trace (often a CLIENT-kind root)
- this failure is structural: a data/client layer built on global handles, or functions whose
  signatures don't accept the context, **cannot** emit connected traces no matter how the
  instrumentation is configured — the context has to be threaded down to the call
- never invoke an instrumented client with an empty/background context on a request path

## Baggage

Use baggage intentionally.

Good uses:
- bounded business context that must cross service boundaries
- values that help downstream decisions or correlation

Avoid:
- large payloads
- sensitive data unless explicitly approved and protected
- turning baggage into a generic key-value dump

## Default Preference

Prefer W3C Trace Context and W3C Baggage unless a legacy environment requires otherwise.
