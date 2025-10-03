# Singleton for NFC encoding session state

class NfcEncodingSession:
    def __init__(self):
        self.active = False
        self.album_id = None
        self.last_uid = None
        self.success = False

    def start(self, album_id):
        self.active = True
        self.album_id = album_id
        self.last_uid = None
        self.success = False

    def stop(self):
        self.active = False
        self.album_id = None
        self.last_uid = None
        self.success = False

    def complete(self, uid):
        self.last_uid = uid
        self.success = True
        self.active = False

nfc_encoding_session = NfcEncodingSession()
