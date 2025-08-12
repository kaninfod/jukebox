import pytest
import os
from PIL import Image, ImageDraw, ImageFont
from app.ui.screens.rfid_loading import RfidLoadingScreen, RfidLoadingStatus

class DummyTheme:
    def __init__(self):
        from app.ui.manager import ScreenManager
        self.colors = {
            "background": "white",
            "text": "black",
            "secondary": "gray",
            "error": "red"
        }
        # Use the app's font loading logic
        self.fonts = ScreenManager._load_fonts(ScreenManager)
        print("Fonts loaded in DummyTheme:", self.fonts.keys())
        self.layout = {
            "title_y": 10,
            "line_height": 24
        }

def test_draw_loading_album():
    theme = DummyTheme()
    screen = RfidLoadingScreen(theme)
    context = {"status": RfidLoadingStatus.LOADING_ALBUM, "album_name": "Test Album"}
    image = Image.new('RGB', (screen.width, screen.height), 'white')
    draw = ImageDraw.Draw(image)
    screen.draw(draw, theme.fonts, context, image=image)
    image.save("tests/test_draw_loading_album.png")
    assert image.size == (480, 320)

def test_draw_error():
    theme = DummyTheme()
    screen = RfidLoadingScreen(theme)
    context = {"status": RfidLoadingStatus.ERROR, "error_message": "Card error"}
    image = Image.new('RGB', (screen.width, screen.height), 'white')
    draw = ImageDraw.Draw(image)
    screen.draw(draw, theme.fonts, context, image=image)
    image.save("tests/test_draw_error.png")
    assert image.size == (480, 320)

def test_draw_new_rfid():
    theme = DummyTheme()
    screen = RfidLoadingScreen(theme)
    context = {"status": RfidLoadingStatus.NEW_RFID, "rfid_id": "1234567890ABCDEF"}
    image = Image.new('RGB', (screen.width, screen.height), 'white')
    draw = ImageDraw.Draw(image)
    screen.draw(draw, theme.fonts, context, image=image)
    image.save("tests/test_draw_new_rfid.png")
    assert image.size == (480, 320)

def test_draw_reading():
    theme = DummyTheme()
    screen = RfidLoadingScreen(theme)
    context = {"status": RfidLoadingStatus.READING}
    image = Image.new('RGB', (screen.width, screen.height), 'white')
    draw = ImageDraw.Draw(image)
    screen.draw(draw, theme.fonts, context, image=image)
    image.save("tests/test_draw_reading.png")
    assert image.size == (480, 320)
