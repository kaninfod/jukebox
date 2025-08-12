from app.ui.theme import UITheme
from app.ui.screens.idle import IdleScreen
from app.ui.screens.home import HomeScreen
from app.ui.screens.rfid_loading import RfidLoadingScreen
from app.ui.screens.error import ErrorScreen

def screen_factory(theme: UITheme):
    return {
        "idle": IdleScreen(theme),
        "home": HomeScreen(theme),
        "rfid_loading": RfidLoadingScreen(theme),
        "error": ErrorScreen(theme),
    }
