import pytest
import os
from PIL import Image, ImageDraw, ImageFont
from app.ui.screens.rfid_loading import RfidLoadingScreen, RfidLoadingStatus
from app.ui.screens.home import HomeScreen
from app.ui.theme import UITheme
from app.ui.manager import ScreenManager
class DummyTheme:
    def __init__(self):
        
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



def test_draw_home():
    fonts = ScreenManager._load_fonts(ScreenManager)
    theme = UITheme(fonts=fonts)
    
    screen = HomeScreen(theme)

    context = {
        'artist': 'Nick Murphy',
        'album': 'Run Fast Sleep Naked',
        'year': '2019',
        'track': 'Believe Mex',
        'image_url': 'https://lh3.googleusercontent.com/i0_hZgNACgkwkVd4qNwB5S52977iNOjzvrDcB3OhD1fYDEGPdljBCWDBs6a7frEofGAQUYkRjC7WhxQ=w120-h120-l90-rj',
        'yt_id': 'OLAK5uy_kDP1Alo5TC7qVzFIDx4UPjCgzEW0-9Sn4',
        'volume': 30,
        'state': 'playing'
    }
    image = Image.new('RGB', (screen.width, screen.height), 'white')
    draw = ImageDraw.Draw(image)
    draw_status = screen.draw(draw, theme.fonts, context, image=image)
    image.save("tests/test_draw_home.png")
    print(draw_status)
    assert image.size == (480, 320)
