class UIContext:
    def __init__(self, player_status=None, track_info=None, rfid_status=None):
        self.player_status = player_status
        self.track_info = track_info or {}
        self.rfid_status = rfid_status or {}
