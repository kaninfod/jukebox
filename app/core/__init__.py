from .event_bus import event_bus, Event
from .event_factory import EventType, EventFactory

# Optional: alias specific event types for direct import
track_changed = EventType.TRACK_CHANGED
volume_changed = EventType.VOLUME_CHANGED
status_changed = EventType.STATUS_CHANGED
clear_error = EventType.CLEAR_ERROR
button_pressed = EventType.BUTTON_PRESSED
rotary_encoder = EventType.ROTARY_ENCODER
ha_state_changed = EventType.HA_STATE_CHANGED
ha_volume_changed = EventType.HA_VOLUME_CHANGED
rfid_read = EventType.RFID_READ
