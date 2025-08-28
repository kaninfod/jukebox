
import threading
import logging
logger = logging.getLogger("ui.event_bus")

class UIEvent:
    def __init__(self, type, payload=None):
        self.type = type
        self.payload = payload or {}

class UIEventBus:
    def __init__(self):
        self._subscribers = []
        self._lock = threading.Lock()

    def subscribe(self, callback):
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback):
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def emit(self, event: UIEvent):
        import traceback
        stack = traceback.format_stack(limit=5)
        stack_str = ''.join(stack[:-1])  # Exclude this emit() call itself
        logger.info(f"📢 UIEvent emitted: type='{event.type}' payload={event.payload}")
        with self._lock:
            subscribers = list(self._subscribers)
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"⚠️ UIEventBus callback error: {e}")

# Singleton instance for the app
ui_event_bus = UIEventBus()
