import logging

logger = logging.getLogger(__name__)

class Screen:
    def __init__(self, width=480, height=320):
        self.width = width
        self.height = height
        #self.name = "Base Screen"
        self.dirty = True
        # event_type = None
        # name = None


    # @classmethod
    # def show(cls, context=None):
    #     """Emit an event to show the home screen via the event bus."""
    #     from app.core.event_bus import event_bus, Event
    #     logger.info(f"Raising {cls.event_type} to EventBus with {id(event_bus)}")
    #     event_bus.emit(Event(type=cls.event_type, payload=context))
    #     logger.info(f"EventBus: Emitted {cls.event_type} event from {cls.name}.show()")

    def draw(self, draw_context, fonts, jukebox_mediaplayer=None):
        pass

    def is_dirty(self, context):
        return self.dirty