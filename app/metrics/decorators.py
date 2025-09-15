import time
from app.metrics.collector import metrics

def track_event_handler(event_type):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                metrics.inc("event_handler_success", event_type)
                return result
            except Exception as e:
                metrics.inc("event_handler_failure", event_type)
                raise
            finally:
                duration = time.time() - start
                metrics.observe("event_handler_duration", duration, event_type)
        return wrapper
    return decorator
