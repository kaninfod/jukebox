import requests
import json
import logging
from app.config import config

class HomeAssistantService:
    def __init__(self):
        self.ha_url = config.HA_BASE_URL + "/api/services/media_player/play_media"
        self.token = config.HA_TOKEN
        self.entity_id = config.MEDIA_PLAYER_ENTITY_ID
        logging.info("HomeAssistantService initialized.")


    def get_volume(self):
        """Fetch the current volume (0.0-1.0) from the media player entity in Home Assistant."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        url = f"{config.HA_BASE_URL}/api/states/{self.entity_id}"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            entity_data = resp.json()
            volume = entity_data.get("attributes", {}).get("volume_level", 0)
            logging.debug(f"Fetched volume from HA: {volume}")
            return volume
        except Exception as e:
            logging.error(f"Failed to fetch volume from HA: {e}")
            return 0
        

    def set_volume(self, volume_level):
        """Set volume on the media player (0.0–1.0)."""
        data = {
            "entity_id": self.entity_id,
            "volume_level": volume_level
        }
        return self._call_service("media_player", "volume_set", data)
    
    def play_pause(self):
        """Toggle play/pause on the media player."""
        return self._call_service("media_player", "media_play_pause")

    def _call_service(self, domain, service, data=None):
        url = f"{config.HA_BASE_URL}/api/services/{domain}/{service}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = data or {"entity_id": self.entity_id}
        resp = requests.post(url, headers=headers, data=json.dumps(payload))
        if resp.status_code == 200:
            logging.info(f"Called {domain}.{service} successfully.")
        else:
            logging.error(f"Failed to call {domain}.{service}: {resp.status_code} {resp.text}")
        return resp.status_code == 200

    def stop(self):
        """Stop playback on the media player."""
        return self._call_service("media_player", "media_stop")


    def volume_up(self):
        """Increase volume on the media player."""
        return self._call_service("media_player", "volume_up")

    def volume_down(self):
        """Decrease volume on the media player."""
        return self._call_service("media_player", "volume_down")

    def cast_stream_url(self, stream_url, entity_id=None, media_info={}):
        # logging.info(f"Casting stream URL: {stream_url} to entity {entity_id or self.entity_id}")
        entity = entity_id or self.entity_id
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "entity_id": entity,
            "media_content_id": stream_url,
            "media_content_type": "music",
            "extra": media_info
            
        }
        resp = requests.post(self.ha_url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200:
            logging.info("Casting started!")
        else:
            logging.error(f"Failed to cast: {resp.status_code} {resp.text}")
        return resp.status_code == 200
