# Instrumentation plan template

Remove inapplicable rows and guidance text. Leave no placeholders or TBDs.

```markdown
# Instrumentation Plan: {service or system}

## Application Profile

- **Types**: {API, batch, real-time, background worker; include hybrids}
- **Existing instrumentation**: {none or exact brownfield inventory}
- **Languages/frameworks/package managers**: {detected values}

## Business Workflows

| Workflow | User outcome | Entry point | Critical dependencies | Degraded states | Trace expectation |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

## Services In Scope

| Service | Include? | Role | Reason | SDK strategy | Signals |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

## Signal Scope

| Signal | Enabled? | Scope | Reason | Guardrails |
|---|---|---|---|---|
| Traces | ... | ... | ... | ... |
| Metrics | ... | ... | ... | bounded dimensions and series budget |
| Logs | ... | ... | ... | redaction/export policy or disabled |
| Baggage | ... | ... | ... | bounded allowlist or disabled |

## SLOs And SLIs

| SLO | Target/window | Status | SLI and user boundary | Producing telemetry | Gap |
|---|---|---|---|---|---|
| ... | {confirmed or unconfirmed} | ... | ... | ... | ... |

## Auto-Instrumented Boundaries

The implementation must not create duplicate manual boundary spans.

| Service | Boundary | Decision | Verified coverage | Manual context | Suppression/tuning | Privacy and volume risk |
|---|---|---|---|---|---|---|
| ... | ... | {auto, auto + manual context, excluded} | ... | ... | ... | ... |

## Manual Boundaries

### {boundary}

- **Service/file/function**: ...
- **Reason and strategy**: {manual or auto + manual context}
- **Create new span**: {yes or no}
- **Signals**: ...
- **Attributes**: {name, boundedness, metric cross-product, privacy risk, investigation value}
- **Diagnostic records**: {none or bounded fields under logs policy}
- **Failure definition/status**: ...
- **Recording owner**: ...
- **Do not record**: ...
- **SLI or debugging coverage**: ...

## Privacy And Sensitive Data Policy

| Source | Risk | Decision |
|---|---|---|
| ... | ... | ... |

## Noise, Volume, And Cost

| Source | Risk/budget | Decision |
|---|---|---|
| ... | ... | ... |

## Propagation Policy

- **Trace context**: ...
- **Baggage**: disabled or bounded allowlist with rationale
- **Messaging propagation**: ...

## SDK Setup Constraints

- **Services to configure**: ...
- **Services excluded or lower priority**: ...
- **Allowed/disallowed signals**: ...
- **Sampling**: ...
- **Required suppressions**: ...
- **Sensitive-capture restrictions**: ...
- **Required environment inputs**: ...

## Excluded Boundaries

- {boundary} — {reason}

## Gaps And Risks

- {unconfirmed SLOs, missing telemetry, uncertain coverage, cardinality/privacy/cost risks}

## Verification Checklist

- [ ] Business workflows are understandable from the resulting traces.
- [ ] Existing coverage is not duplicated.
- [ ] Only planned services and signals are configured.
- [ ] Logs have a redaction/export policy or remain disabled.
- [ ] Baggage has a bounded, non-sensitive allowlist or remains disabled.
- [ ] Production sampling is justified and required noisy endpoints are suppressed.
- [ ] Raw personal data, credentials, payloads, identifiers, SQL values, and exception messages are absent.
- [ ] Metric dimensions are bounded and within the stated series budget.
- [ ] Every manual boundary defines failure, status, and one recording owner.
- [ ] Every SLI maps to available telemetry or an explicit gap.
```
