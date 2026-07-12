---
name: ollygarden-otel-java-setup
description: Ollygarden's recommended pattern for setting up OpenTelemetry in Java services. Covers the Javaagent vs Spring Boot Starter vs manual autoconfigure decision-making and the Maven BOM dependency pattern. Use when adding OTel to a Java project, choosing a setup path, or reviewing dependency declarations. Triggers on "java otel setup", "javaagent vs starter", "opentelemetry-bom".
---

# Java SDK Setup Conventions

## Setup Decision Tree

```
Is zero-code instrumentation sufficient?
├── Yes → Javaagent with declarative config (recommended)
│         -javaagent:opentelemetry-javaagent.jar -Dotel.config.file=otel.yaml
└── No  → Manual SDK setup
          ├── Spring Boot? → Spring Boot Starter
          └── Plain Java?  → Autoconfigure SDK extension
```

The Javaagent loads a standalone file via `-Dotel.config.file`. The Spring Boot Starter
embeds declarative configuration under the `otel` property tree and opts in with
`otel.file_format`; it does not load `otel.config.file`. Manual autoconfigure needs the
declarative-config extension in addition to the autoconfigure extension.

## Path A: Javaagent + Declarative Config (Recommended)

The Javaagent automatically instruments HTTP, gRPC, DB, and messaging frameworks.
Declarative config replaces the long list of `-Dotel.*` system properties.

For manual instrumentation on top of the agent, add the API. Fetch the latest BOM tag
(see the `otel-java` skill's Sources of Truth) and substitute below:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>io.opentelemetry</groupId>
            <artifactId>opentelemetry-bom</artifactId>
            <version><!-- latest BOM tag, see reference skill's Sources of Truth --></version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-api</artifactId>
    </dependency>
</dependencies>
```

## Path B: Spring Boot Starter

For Spring Boot applications without the Javaagent:

Import the instrumentation BOM so the Starter and its instrumentation dependencies stay
aligned. This is required with Spring Boot 3.5+, whose dependency management can otherwise
select an incompatible OpenTelemetry API version.

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>io.opentelemetry.instrumentation</groupId>
            <artifactId>opentelemetry-instrumentation-bom</artifactId>
            <version><!-- latest instrumentation BOM tag --></version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

```xml
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
</dependency>
```

Configure via `application.yaml`; `otel.file_format` opts into the embedded declarative model:

```yaml
otel:
  file_format: "1.0" # use the literal supported by the selected Starter release
  # tracer_provider, meter_provider, logger_provider, instrumentation, ...
```

## Path C: Manual Autoconfigure

For non-Spring applications without the Javaagent:

```xml
<dependencies>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-api</artifactId>
    </dependency>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-sdk-extension-autoconfigure</artifactId>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-sdk-extension-declarative-config</artifactId>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-exporter-otlp</artifactId>
        <scope>runtime</scope>
    </dependency>
</dependencies>
```

## Key Details

- **BOM alignment**: Use `opentelemetry-instrumentation-bom` for the Spring Boot Starter.
  Use `opentelemetry-bom` for stable core SDK artifacts and the matching
  `opentelemetry-bom-alpha` for the alpha declarative-config extension in manual setup.
- **API at compile, SDK at runtime**: Depend on `opentelemetry-api` at compile scope, SDK/exporter at runtime. This keeps application code decoupled from SDK internals.

## Anti-Patterns

### Agent jar / flag / config path drift

The jar baked into the image, the `-javaagent:<jar-path>` flag, and
`-Dotel.config.file=<yaml-path>` form one contract — all three paths must resolve at
runtime. The failure mode is splitting them across layers:

- If the launch flags come from a deploy-layer env var (e.g. `JAVA_TOOL_OPTIONS` in a
  Kubernetes manifest), that var **overrides** the image's own `ENV` — so a manifest can
  point `-javaagent` at a jar the image never installed.
- A rename or half-reverted change that updates the flag but not the jar (or vice versa)
  yields `agent library failed to load` / `Error opening zip file or JAR manifest missing`
  and a JVM crash loop on every pod.

Keep the jar download, the `otel.yaml` copy, and the launch flag in the **same image
layer** (the Dockerfile). Do not let a manifest re-specify the agent path unless it also
guarantees the jar exists at that path.

## Cross-References

- Reference: `otel-java` skill — `references/declarative-setup.md` for the Javaagent fetch table, activation flags, manual instrumentation API, agent-only properties.
- General conventions: `ollygarden-otel-declarative-config` — anti-patterns and common YAML patterns.
