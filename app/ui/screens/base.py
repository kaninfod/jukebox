import logging
from PIL import Image

logger = logging.getLogger(__name__)

class Screen:
    def __init__(self, width=480, height=320):
        self.width = width
        self.height = height
        #self.name = "Base Screen"
        self.dirty = True

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


class MenuItemElement(Element):
    """Element for rendering individual menu items with optional selection highlight"""
    def __init__(self, x, y, width, height, text, font, is_selected=False, highlight_color="#24AC5F"):
        super().__init__(x, y, width, height)
        self.text = text
        self.font = font
        self.is_selected = is_selected
        self.highlight_color = highlight_color

    def draw(self, draw_context):
        # Draw background highlight if selected
        if self.is_selected:
            draw_context.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), 
                                 fill=self.highlight_color)
            text_color = "white"
        else:
            text_color = "black"
        
        # Calculate text positioning
        bbox = draw_context.textbbox((0, 0), self.text, font=self.font)
        text_height = bbox[3] - bbox[1]
        
        # Left align with padding, vertically center
        text_x = self.x + 10  # 10px left padding
        text_y = self.y + (self.height - text_height) // 2
        
        draw_context.text((text_x, text_y), self.text, fill=text_color, font=self.font)


class MenuHeaderElement(Element):
    """Element for rendering menu header with breadcrumb"""
    def __init__(self, x, y, width, height, title, font, background_color="white", text_color="black"):
        super().__init__(x, y, width, height)
        self.title = title
        self.font = font
        self.background_color = background_color
        self.text_color = text_color

    def draw(self, draw_context):
        # Draw header background
        draw_context.rectangle((self.x, self.y, self.x + self.width, self.y + self.height), 
                             fill=self.background_color)
        
        # Draw bottom border line
        draw_context.line([(self.x, self.y + self.height - 1), 
                          (self.x + self.width, self.y + self.height - 1)], 
                         fill="gray", width=1)
        
        # Calculate text positioning
        bbox = draw_context.textbbox((0, 0), self.title, font=self.font)
        text_height = bbox[3] - bbox[1]
        
        # Left align with padding, vertically center
        text_x = self.x + 10
        text_y = self.y + (self.height - text_height) // 2
        
        draw_context.text((text_x, text_y), self.title, fill=self.text_color, font=self.font)


class MenuBottomBarElement(Element):
    """Element for rendering the bottom bar with Previous and Exit buttons"""
    def __init__(self, x, y, width, height, font, selected_button=None):
        super().__init__(x, y, width, height)
        self.font = font
        self.selected_button = selected_button  # "previous" or "exit" or None
        self.button_width = width // 2

    def draw(self, draw_context):
        # Draw top separator line
        draw_context.line([(self.x, self.y), (self.x + self.width, self.y)], 
                         fill="gray", width=1)
        
        # Draw Previous button
        prev_bg = "#24AC5F" if self.selected_button == "previous" else "white"
        prev_text_color = "white" if self.selected_button == "previous" else "black"
        
        draw_context.rectangle((self.x, self.y + 1, self.x + self.button_width, self.y + self.height), 
                             fill=prev_bg)
        
        # Draw Exit button  
        exit_bg = "#24AC5F" if self.selected_button == "exit" else "white"
        exit_text_color = "white" if self.selected_button == "exit" else "black"
        
        draw_context.rectangle((self.x + self.button_width, self.y + 1, self.x + self.width, self.y + self.height), 
                             fill=exit_bg)
        
        # Draw vertical separator between buttons
        draw_context.line([(self.x + self.button_width, self.y + 1), 
                          (self.x + self.button_width, self.y + self.height)], 
                         fill="gray", width=1)
        
        # Calculate text positioning for buttons
        prev_text = "← Previous"
        exit_text = "Exit"
        
        # Previous button text
        bbox = draw_context.textbbox((0, 0), prev_text, font=self.font)
        text_height = bbox[3] - bbox[1]
        text_width = bbox[2] - bbox[0]
        
        prev_text_x = self.x + (self.button_width - text_width) // 2
        prev_text_y = self.y + (self.height - text_height) // 2
        
        draw_context.text((prev_text_x, prev_text_y), prev_text, fill=prev_text_color, font=self.font)
        
        # Exit button text
        bbox = draw_context.textbbox((0, 0), exit_text, font=self.font)
        text_width = bbox[2] - bbox[0]
        
        exit_text_x = self.x + self.button_width + (self.button_width - text_width) // 2
        exit_text_y = self.y + (self.height - text_height) // 2
        
        draw_context.text((exit_text_x, exit_text_y), exit_text, fill=exit_text_color, font=self.font)

