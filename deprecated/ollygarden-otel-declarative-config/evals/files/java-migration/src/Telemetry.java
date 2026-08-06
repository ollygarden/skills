package example;

final class Telemetry {
  // This processor removes url.query and url.full before export.
  static final class QuerySanitizingSpanProcessor {
    String sanitize(String key, String value) {
      return (key.equals("url.query") || key.equals("url.full")) ? "[redacted]" : value;
    }
  }
}
