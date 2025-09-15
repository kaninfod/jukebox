from prometheus_client import Counter, Histogram
from app.config import config

# Prometheus metrics definitions
event_emitted = Counter('event_emitted_total', 'Events emitted', ['event_type'])
event_dropped = Counter('event_dropped_total', 'Events dropped (no handler)', ['event_type'])
event_handler_success = Counter('event_handler_success_total', 'Event handler success', ['event_type'])
event_handler_failure = Counter('event_handler_failure_total', 'Event handler failure', ['event_type'])
event_handler_duration = Histogram('event_handler_duration_seconds', 'Event handler execution time', ['event_type'])

# Helper functions for compatibility with previous collector API
class MetricsCollector:
    def inc(self, name, label=None):
        if name == "event_emitted":
            event_emitted.labels(event_type=label).inc()
        elif name == "event_dropped":
            event_dropped.labels(event_type=label).inc()
        elif name == "event_handler_success":
            event_handler_success.labels(event_type=label).inc()
        elif name == "event_handler_failure":
            event_handler_failure.labels(event_type=label).inc()

    def observe(self, name, value, label=None):
        if name == "event_handler_duration":
            event_handler_duration.labels(event_type=label).observe(value)

    def get_metrics(self):
        # Prometheus metrics are exposed via /metrics endpoint, not as dicts
        return {}, {}

metrics = MetricsCollector()
