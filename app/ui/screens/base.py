import logging
from PIL import Image

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
    
class Element():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.box = (self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    def rect_coords(self):
        """Return rectangle coordinates in PIL format: [(x1, y1), (x2, y2)]"""
        return [(self.x, self.y), (self.x + self.width, self.y + self.height)]

    @property
    def x2(self):
        """Return the x2 coordinate of the element."""
        return self.x + self.width

    @property
    def y2(self):
        """Return the y2 coordinate of the element."""
        return self.y + self.height

    def draw(self, draw_context):
        raise NotImplementedError("Subclasses must implement this method")

class RectElement(Element):
    def __init__(self, x, y, width, height, fill):
        super().__init__(x, y, width, height)
        self.fill = fill

    def draw(self, draw_context):
        draw_context.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), fill=self.fill)

class TextElement(Element):
    def __init__(self, x, y, width, height, text, font):
        super().__init__(x, y, width, height)
        self.text = text
        self.font = font

    def draw(self, draw_context):
        # Calculate text bounding box
        bbox = draw_context.textbbox((0, 0), self.text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text within the element bounds (or adjust for left align)
        text_x = self.x  # left align
        text_y = self.y + (self.height - text_height) // 2  # vertically center
        
        draw_context.text((text_x, text_y), self.text, fill="black", font=self.font)

class ImageElement(Element):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height)
        self.image = image

    def draw(self, draw_context, canvas):
        if self.image is not None:
            try:
                mask = self.image if self.image.mode == 'RGBA' else None
                canvas.paste(self.image, (self.x, self.y), mask)
            except Exception as e:
                logger.error(f"Error displaying image: {e}")
                draw_context.rectangle(self.rect_coords, outline="black", fill=None)
                draw_context.text((self.x, self.y), "ERROR", fill="black")
        else:
            logger.error(f"No image")
            draw_context.rectangle(self.rect_coords, outline="black", fill=None)
            draw_context.text((self.x, self.y), "No Image", fill="black")

