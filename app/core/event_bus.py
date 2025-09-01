import threading
import logging
from collections import defaultdict

logger = logging.getLogger("core.event_bus")

class Event:
    def __init__(self, type, payload=None):
        self.type = type
        self.payload = payload or {}

class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)  # EventType -> [handler_fn]
        self._lock = threading.Lock()

    def subscribe(self, event_type, handler):
        logger.info(f"Subscribing handler {handler} to event type {event_type}")
        self._handlers[event_type].append(handler)

    def emit(self, event: Event):
        results = []

        logger.info(f"Emitting event: type={event.type}, payload={event.payload}")
        handlers = self._handlers.get(event.type, [])
        if not handlers:
            logger.warning(f"No handlers registered for event type: {event.type}")
        else:
            for handler in handlers:
                logger.info(f"Calling handler {handler.__name__} for event type {event.type}")
                result = handler(event)
                results.append(result)
        return results

# Singleton instance for the app
event_bus = EventBus()
