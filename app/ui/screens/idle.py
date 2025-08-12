import logging
from app.ui.theme import UITheme
from app.ui.screens.base import Screen
from PIL import ImageDraw

logger = logging.getLogger(__name__)
class IdleScreen(Screen):
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "Idle Screen"

    def draw(self, draw_context, fonts, context=None, image=None):
        # Draw the background
        draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["background"])

        # Draw the text
        title_font = self.theme.fonts["title"]
        info_font = self.theme.fonts["info"]
        small_font = self.theme.fonts["small"]
        center_x = self.width // 2
        welcome_text = "Welcome to"
        welcome_bbox = draw_context.textbbox((0, 0), welcome_text, font=title_font)
        welcome_width = welcome_bbox[2] - welcome_bbox[0]
        welcome_x = center_x - (welcome_width // 2)
        draw_context.text((welcome_x, self.theme.layout["title_y"]), welcome_text, fill=self.theme.colors["text"], font=title_font)
        company_text = "Siemens"
        company_bbox = draw_context.textbbox((0, 0), company_text, font=info_font)
        company_width = company_bbox[2] - company_bbox[0]
        company_x = center_x - (company_width // 2)
        draw_context.text((company_x + 1, self.theme.layout["company_y"] + 1), company_text, fill=self.theme.colors["secondary"], font=info_font)
        draw_context.text((company_x, self.theme.layout["company_y"]), company_text, fill=self.theme.colors["text"], font=info_font)
        product_text = "Klangmeister RG406"
        product_bbox = draw_context.textbbox((0, 0), product_text, font=info_font)
        product_width = product_bbox[2] - product_bbox[0]
        product_x = center_x - (product_width // 2)
        draw_context.text((product_x, self.theme.layout["product_y"]), product_text, fill=self.theme.colors["primary"], font=info_font)
        line_y = 180
        line_start_x = center_x - 100
        line_end_x = center_x + 100
        draw_context.line([(line_start_x, line_y), (line_end_x, line_y)], fill=self.theme.colors["primary"], width=2)
        instruction_text = "Scan a card to proceed..."
        instruction_bbox = draw_context.textbbox((0, 0), instruction_text, font=small_font)
        instruction_width = instruction_bbox[2] - instruction_bbox[0]
        instruction_x = center_x - (instruction_width // 2)
        draw_context.text((instruction_x, 220), instruction_text, fill=self.theme.colors["secondary"], font=small_font)
        card_width = 60
        card_height = 40
        card_x = center_x - (card_width // 2)
        card_y = 260
        draw_context.rectangle([card_x, card_y, card_x + card_width, card_y + card_height], outline=self.theme.colors["text"], fill=self.theme.colors["background"], width=2)
        chip_size = 8
        chip_x = card_x + 10
        chip_y = card_y + 10
        draw_context.rectangle([chip_x, chip_y, chip_x + chip_size, chip_y + chip_size], fill=self.theme.colors["highlight"], outline=self.theme.colors["text"])
        draw_context.text((card_x + 20, card_y + 22), "NFC", fill=self.theme.colors["text"], font=small_font)

        logger.info("IdleScreen drawn")
