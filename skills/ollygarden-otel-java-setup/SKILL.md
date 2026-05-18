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

All paths support declarative configuration via `-Dotel.config.file`.

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

```xml
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
</dependency>
```

Configure via `application.properties` or use declarative config with:

```properties
otel.config.file=configs/otel.yaml
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
        <artifactId>opentelemetry-exporter-otlp</artifactId>
        <scope>runtime</scope>
    </dependency>
</dependencies>
```

Always use the BOM to align dependency versions.

## Key Details

- **BOM alignment**: Always import `opentelemetry-bom` to prevent version conflicts.
- **API at compile, SDK at runtime**: Depend on `opentelemetry-api` at compile scope, SDK/exporter at runtime. This keeps application code decoupled from SDK internals.

## Cross-References

- Reference: `otel-java` skill — `references/declarative-setup.md` for the Javaagent fetch table, activation flags, manual instrumentation API, agent-only properties.
- General conventions: `ollygarden-otel-declarative-config` — anti-patterns and common YAML patterns.
