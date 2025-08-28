import logging
from app.ui.theme import UITheme
from app.ui.screens.idle import IdleScreen
from app.ui.screens.home import HomeScreen
from app.ui.screens.rfid_loading import RfidLoadingScreen, RfidReadingScreen, RfidNewRfidScreen, RfidErrorScreen
from app.ui.screens.error import ErrorScreen

logger = logging.getLogger(__name__)

def screen_factory(theme):
    screens = {
        "idle": IdleScreen(theme),
        "home": HomeScreen(theme),
        "rfid_reading": RfidReadingScreen(theme),
        "rfid_loading": RfidLoadingScreen(theme),
        "rfid_new_rfid": RfidNewRfidScreen(theme),
        "rfid_error": RfidErrorScreen(theme),
        "error": ErrorScreen(theme),
    }
    logger.info(f"ScreenFactory: Created screens: {list(screens.keys())}")
    return screens