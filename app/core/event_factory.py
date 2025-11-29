from enum import Enum
from app.core.event_bus import Event

class EventType(Enum):
    SYSTEM_REBOOT_REQUESTED = "system_reboot_requested"
    SYSTEM_SHUTDOWN_REQUESTED = "system_shutdown_requested"
    SYSTEM_RESTART_REQUESTED = "system_restart_requested"
    SYSTEM_REBOOT_CANCELLED = "system_reboot_cancelled"
    SYSTEM_SHUTDOWN_CANCELLED = "system_shutdown_cancelled"
    SYSTEM_RESTART_CANCELLED = "system_restart_cancelled"

    TRACK_CHANGED = "track_changed"
    VOLUME_CHANGED = "volume_changed"
    STATUS_CHANGED = "status_changed"
    TRACK_FINISHED = "track_finished"
    TRACK_PAUSED = "track_paused"
    TRACK_RESUMED = "track_resumed"
    NEXT_TRACK = "next_track"
    PREVIOUS_TRACK = "previous_track"
    PLAY_TRACK = "play_track"
    PLAY_PAUSE = "play_pause"
    PLAY = "play"
    STOP = "stop"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    SET_VOLUME = "set_volume"
    PLAY_ALBUM = "play_album"
    
    CLEAR_ERROR = "clear_error"
    BUTTON_PRESSED = "button_pressed"
    ROTARY_ENCODER = "RotaryEncoder"
    STATE_CHANGED = "state_changed"
    RFID_READ = "rfid_read"
    SHOW_IDLE = "show_idle"
    SHOW_HOME = "show_home"
    SHOW_MESSAGE = "show_message"
    SHOW_MENU = "show_menu"
    # Menu system events
    MENU_ENTER = "menu_enter"
    MENU_EXIT = "menu_exit"
    MENU_NAVIGATE = "menu_navigate"
    MENU_ACTIVATE = "menu_activate"
    MENU_ACTION = "menu_action"
    # Chromecast events
    CHROMECAST_DEVICE_CHANGED = "chromecast_device_changed"
    SHOW_SCREEN_QUEUED = "show_screen_queued"
    ENCODE_CARD = "encode_card"
    NOTIFICATION = "notification"
    TOGGLE_REPEAT_ALBUM = "toggle_repeat_album"

class EventFactory:
    @staticmethod
    def show_screen_queued(screen_type, context, duration=3.0):
        """Create a queued screen event"""
        return Event(
            type=EventType.SHOW_SCREEN_QUEUED,
            payload={
                "screen_type": screen_type,
                "context": context,
                "duration": duration
            }
        )
    @staticmethod
    def notification(payload):
        return Event(
            type=EventType.NOTIFICATION.value,
            payload=payload
        )

    # @staticmethod
    # def volume_changed(payload):
    #     return Event(
    #         type=EventType.VOLUME_CHANGED.value,
    #         payload=payload
    #     )

    # @staticmethod
    # def status_changed(payload):
    #     return Event(
    #         type=EventType.STATUS_CHANGED.value,
    #         payload=payload
    #     )

    # @staticmethod
    # def clear_error(button=None):
    #     return Event(
    #         type=EventType.CLEAR_ERROR.value,
    #         payload={"button": button} if button else {},
    #     )

    # @staticmethod
    # def button_pressed(button, action):
    #     return Event(
    #         type=EventType.BUTTON_PRESSED.value,
    #         payload={"button": button, "action": action},
    #     )

    # @staticmethod
    # def rotary_encoder(direction, action):
    #     return Event(
    #         type=EventType.ROTARY_ENCODER.value,
    #         payload={"direction": direction, "action": action},
    #     )

    # @staticmethod
    # def ha_state_changed(old_status, state):
    #     return Event(
    #         type=EventType.HA_STATE_CHANGED.value,
    #         payload={"from": old_status, "to": state},
    #     )

    # @staticmethod
    # def rfid_read(rfid):
    #     return Event(
    #         type=EventType.RFID_READ.value,
    #         payload={"rfid": rfid},
    #     )

    # @staticmethod
    # def play_album(album_id, album_name=None):
    #     return Event(
    #         type=EventType.PLAY_ALBUM.value,
    #         payload={
    #             "audioPlaylistId": album_id,
    #             "album_name": album_name
    #         }
    #     )

    # @staticmethod
    # def show_idle():
    #     return Event(
    #         type=EventType.SHOW_IDLE.value,
    #     )
    
    # @staticmethod
    # def show_home(payload):
    #     return Event(
    #         type=EventType.SHOW_HOME.value,
    #         payload=payload
    #     )
