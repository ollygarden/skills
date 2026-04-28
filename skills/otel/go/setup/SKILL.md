---
name: ollygarden-otel-go-setup
description: Ollygarden's recommended pattern for setting up the OpenTelemetry SDK in Go services using otelconf. Covers project structure, the Providers struct, no-op fallback, runtime attribute injection, and the zap log bridge. Use when adding OTel to a Go project, structuring telemetry code, or reviewing an existing setup. Triggers on "go otel setup", "go telemetry pattern", "Providers struct go otel".
---

# Go SDK Setup Conventions

## Recommended import path

For new code, use the root `otelconf` package (`go.opentelemetry.io/contrib/otelconf`) — it
tracks the current schema and includes the propagator-from-YAML fix. The schema-pinned
`otelconf/v0.3.0` subpackage is for keeping existing configs unchanged.

## Project Structure

```
internal/telemetry/
├── const.go          # Service scope and telemetry constants
├── setup.go          # SDK initialization (code below)
├── providers.go      # Provider management utilities
└── carriers.go       # Custom propagation carriers (if needed)
configs/
└── otel.yaml         # Declarative configuration
```

## Setup Pattern

The core setup reads a YAML config file, injects runtime attributes, and creates an SDK
instance that provides all three providers (tracer, meter, logger) plus a propagator.

```go
package telemetry

import (
    "context"
    "errors"
    "fmt"
    "os"

    "github.com/google/uuid"
    "go.opentelemetry.io/contrib/bridges/otelzap"
    otelconf "go.opentelemetry.io/contrib/otelconf"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/log"
    "go.opentelemetry.io/otel/log/global"
    "go.opentelemetry.io/otel/metric"
    "go.opentelemetry.io/otel/propagation"
    semconv "go.opentelemetry.io/otel/semconv/v1.40.0"
    "go.opentelemetry.io/otel/trace"
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

type Providers struct {
    TracerProvider trace.TracerProvider
    MeterProvider  metric.MeterProvider
    LoggerProvider log.LoggerProvider
    Logger         *zap.Logger
    Closer         func(ctx context.Context) error
}

func SetupTelemetry(ctx context.Context, serviceName, version, configFile string) (*Providers, error) {
    providers, sdk, err := providersFromConfig(ctx, serviceName, version, configFile)
    if err != nil {
        return nil, err
    }

    otel.SetTracerProvider(providers.TracerProvider)
    otel.SetMeterProvider(providers.MeterProvider)
    global.SetLoggerProvider(providers.LoggerProvider)

    if sdk != nil {
        otel.SetTextMapPropagator(sdk.Propagator())
    } else {
        otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
            propagation.TraceContext{},
            propagation.Baggage{},
        ))
    }

    return providers, nil
}

func providersFromConfig(ctx context.Context, scope, version, cfgFile string) (*Providers, *otelconf.SDK, error) {
    b, err := os.ReadFile(cfgFile)
    if err != nil {
        if errors.Is(err, os.ErrNotExist) {
            logger := zap.Must(zap.NewProduction())
            logger.Warn("OpenTelemetry config file not found, using no-op providers",
                zap.String("config_file", cfgFile))
            return &Providers{
                TracerProvider: trace.NewNoOpTracerProvider(),
                MeterProvider:  metric.NewNoOpMeterProvider(),
                LoggerProvider: log.NewNoOpLoggerProvider(),
                Logger:         logger,
                Closer:         func(ctx context.Context) error { return nil },
            }, nil, nil
        }
        return nil, nil, fmt.Errorf("failed to read config file %s: %w", cfgFile, err)
    }

    b = []byte(os.ExpandEnv(string(b)))

    conf, err := otelconf.ParseYAML(b)
    if err != nil {
        return nil, nil, err
    }

    if conf.Resource == nil {
        conf.Resource = &otelconf.Resource{}
    }
    if conf.Resource.Attributes == nil {
        conf.Resource.Attributes = []otelconf.AttributeNameValue{}
    }
    conf.Resource.Attributes = insertAttribute(conf.Resource.Attributes,
        string(semconv.ServiceVersionKey), version)
    conf.Resource.Attributes = insertAttribute(conf.Resource.Attributes,
        string(semconv.ServiceInstanceIDKey), uuid.New().String())

    sdk, err := otelconf.NewSDK(
        otelconf.WithContext(ctx),
        otelconf.WithOpenTelemetryConfiguration(*conf),
    )
    if err != nil {
        return nil, nil, err
    }

    core := zapcore.NewTee(
        zapcore.NewCore(
            zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
            zapcore.AddSync(os.Stdout),
            zapcore.InfoLevel,
        ),
        otelzap.NewCore(scope, otelzap.WithLoggerProvider(global.GetLoggerProvider())),
    )

    return &Providers{
        TracerProvider: sdk.TracerProvider(),
        MeterProvider:  sdk.MeterProvider(),
        LoggerProvider: sdk.LoggerProvider(),
        Logger:         zap.New(core),
        Closer:         sdk.Shutdown,
    }, &sdk, nil
}

func insertAttribute(attrs []otelconf.AttributeNameValue, name, value string) []otelconf.AttributeNameValue {
    for _, attr := range attrs {
        if attr.Name == name {
            return attrs
        }
    }
    return append(attrs, otelconf.AttributeNameValue{Name: name, Value: value})
}
```

## Main Integration

```go
func main() {
    ctx := context.Background()

    providers, err := telemetry.SetupTelemetry(ctx,
        telemetry.ServiceName,
        telemetry.ServiceVersion,
        "configs/otel.yaml")
    if err != nil {
        log.Fatalf("Failed to setup telemetry: %v", err)
    }

    defer func() {
        shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
        defer cancel()
        if err := providers.Closer(shutdownCtx); err != nil {
            providers.Logger.Error("Failed to shutdown telemetry", zap.Error(err))
        }
    }()

    tracer := otel.Tracer(telemetry.Scope)
    meter := otel.Meter(telemetry.Scope)

    // Application logic...
}
```

## Key Details

- **No-op fallback**: If the config file doesn't exist, the setup returns no-op providers instead of failing. The application runs without telemetry.
- **Runtime attributes**: `service.version` and `service.instance.id` are injected programmatically because they vary per deployment, not per environment.
- **Zap bridge**: The `otelzap` bridge sends structured logs to the OTel LoggerProvider, enabling log correlation with traces. Stdout JSON output is preserved via a tee.
- **10-second shutdown timeout**: Bounds shutdown so a hung exporter cannot block process exit.

## Cross-References

- Reference: `otel-go` skill — `references/declarative-setup.md` for `otelconf` fetch table, import path facts, schema version mapping; `references/breaking-changes.md` for SDK/contrib upgrade audits.
- General conventions: `ollygarden-otel-declarative-config` — anti-patterns and common YAML patterns.
