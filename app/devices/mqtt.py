import threading
from threading import Lock
import paho.mqtt.client as mqtt
import json
import time

MQTT_BROKER = "192.168.68.100"
MQTT_PORT = 1883
MQTT_ROOT = "jukebox"
MQTT_USERNAME = "mqtt-user"
MQTT_PASSWORD = "bart"

# Home Assistant Discovery Configuration
DISCOVERY_PREFIX = "homeassistant"
DEVICE_ID = "jukebox_01"
DEVICE_NAME = "Raspberry Pi Jukebox"

# MQTT Topics for media player information
MQTT_TOPICS = {
    "ARTIST": "jukebox/artist",
    "ALBUM": "jukebox/album", 
    "YEAR": "jukebox/year",
    "TRACK": "jukebox/track",
    "STATUS": "jukebox/status",
    "VOLUME": "jukebox/volume",
    "YT_ID": "jukebox/yt_id"
}

latest_mqtt_messages = {}
mqtt_message_lock = Lock()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(f"{MQTT_ROOT}/#")
    
    # Publish Home Assistant discovery configuration
    if rc == 0:  # Successful connection
        print("Publishing Home Assistant MQTT Discovery configuration...")
        publish_discovery()
        
        # Publish initial state to ensure sensors have valid data
        print("Publishing initial sensor states...")
        publish_status("idle")
        publish_volume("75")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    with mqtt_message_lock:
        latest_mqtt_messages[topic] = payload
    print(f"Received message: {topic} {payload}")

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def mqtt_loop():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

def start_mqtt():
    thread = threading.Thread(target=mqtt_loop, daemon=True)
    thread.start()


# Media Player MQTT Publishing Functions
def publish_artist(artist):
    """Publish artist to MQTT"""
    try:
        mqtt_client.publish(MQTT_TOPICS["ARTIST"], artist)
        print(f"Published artist: {artist}")
    except Exception as e:
        print(f"Failed to publish artist: {e}")


def publish_album(album):
    """Publish album to MQTT"""
    try:
        mqtt_client.publish(MQTT_TOPICS["ALBUM"], album)
        print(f"Published album: {album}")
    except Exception as e:
        print(f"Failed to publish album: {e}")


def publish_year(year):
    """Publish year to MQTT"""
    try:
        mqtt_client.publish(MQTT_TOPICS["YEAR"], str(year))
        print(f"Published year: {year}")
    except Exception as e:
        print(f"Failed to publish year: {e}")


def publish_track(track):
    """Publish track to MQTT"""
    try:
        mqtt_client.publish(MQTT_TOPICS["TRACK"], track)
        print(f"Published track: {track}")
    except Exception as e:
        print(f"Failed to publish track: {e}")


def publish_status(status):
    """Publish status to MQTT"""
    try:
        mqtt_client.publish(MQTT_TOPICS["STATUS"], status)
        print(f"Published status: {status}")
    except Exception as e:
        print(f"Failed to publish status: {e}")


def publish_volume(volume):
    """Publish volume to MQTT"""
    try:
        mqtt_client.publish(MQTT_TOPICS["VOLUME"], str(volume))
        print(f"Published volume: {volume}")
    except Exception as e:
        print(f"Failed to publish volume: {e}")


def publish_yt_id(yt_id):
    """Publish YouTube ID to MQTT"""
    try:
        mqtt_client.publish(MQTT_TOPICS["YT_ID"], yt_id)
        print(f"Published YT ID: {yt_id}")
    except Exception as e:
        print(f"Failed to publish YT ID: {e}")


def get_all_mediaplayer_info():
    """Get all current mediaplayer information from MQTT messages"""
    with mqtt_message_lock:
        return {
            "artist": latest_mqtt_messages.get(MQTT_TOPICS["ARTIST"], "Unknown"),
            "album": latest_mqtt_messages.get(MQTT_TOPICS["ALBUM"], "Unknown"),
            "year": latest_mqtt_messages.get(MQTT_TOPICS["YEAR"], "----"),
            "track": latest_mqtt_messages.get(MQTT_TOPICS["TRACK"], "No Track"),
            "status": latest_mqtt_messages.get(MQTT_TOPICS["STATUS"], "idle"),
            "volume": latest_mqtt_messages.get(MQTT_TOPICS["VOLUME"], "75"),
            "yt_id": latest_mqtt_messages.get(MQTT_TOPICS["YT_ID"], "")
        }


def publish_discovery():
    """Publish Home Assistant MQTT Discovery configuration"""
    try:
        # Device configuration (shared across all entities)
        device_config = {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "manufacturer": "Raspberry Pi Foundation",
            "model": "Jukebox Media Player",
            "model_id": "RPI-JUKEBOX-V1",
            "sw_version": "1.0.0",
            "configuration_url": f"http://{MQTT_BROKER}:8000"
        }
        
        # Origin information
        origin_config = {
            "name": "Jukebox MQTT Integration",
            "sw": "1.0.0",
            "url": "https://github.com/kaninfod/jukebox"
        }
        
        # Artist sensor discovery
        artist_config = {
            "name": "Artist",
            "unique_id": f"{DEVICE_ID}_artist", 
            "state_topic": MQTT_TOPICS["ARTIST"],
            "icon": "mdi:account-music",
            "device": device_config,
            "origin": origin_config
        }
        
        # Album sensor discovery  
        album_config = {
            "name": "Album",
            "unique_id": f"{DEVICE_ID}_album",
            "state_topic": MQTT_TOPICS["ALBUM"], 
            "icon": "mdi:album",
            "device": device_config,
            "origin": origin_config
        }
        
        # Year sensor discovery
        year_config = {
            "name": "Year",
            "unique_id": f"{DEVICE_ID}_year",
            "state_topic": MQTT_TOPICS["YEAR"],
            "icon": "mdi:calendar",
            "device": device_config,
            "origin": origin_config
        }
        
        # Track sensor discovery
        track_config = {
            "name": "Track",
            "unique_id": f"{DEVICE_ID}_track",
            "state_topic": MQTT_TOPICS["TRACK"],
            "icon": "mdi:music-note",
            "device": device_config,
            "origin": origin_config
        }
        
        # Status sensor discovery
        status_config = {
            "name": "Status", 
            "unique_id": f"{DEVICE_ID}_status",
            "state_topic": MQTT_TOPICS["STATUS"],
            "icon": "mdi:play-pause",
            "device": device_config,
            "origin": origin_config
        }
        
        # Volume sensor discovery
        volume_config = {
            "name": "Volume",
            "unique_id": f"{DEVICE_ID}_volume",
            "state_topic": MQTT_TOPICS["VOLUME"],
            "unit_of_measurement": "%",
            "icon": "mdi:volume-high",
            "device": device_config,
            "origin": origin_config
        }
        
        # YouTube ID sensor discovery
        yt_id_config = {
            "name": "YouTube ID",
            "unique_id": f"{DEVICE_ID}_yt_id",
            "state_topic": MQTT_TOPICS["YT_ID"],
            "icon": "mdi:youtube",
            "device": device_config,
            "origin": origin_config
        }
        
        # Publish all discovery configurations with retain=True
        discovery_configs = [
            (f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/artist/config", artist_config),
            (f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/album/config", album_config),
            (f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/year/config", year_config),
            (f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/track/config", track_config),
            (f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/status/config", status_config),
            (f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/volume/config", volume_config),
            (f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/yt_id/config", yt_id_config)
        ]
        
        for topic, config in discovery_configs:
            mqtt_client.publish(topic, json.dumps(config), retain=True)
            print(f"Published discovery config to {topic}")
            time.sleep(0.1)  # Small delay to avoid overwhelming the broker
            
        print("Home Assistant MQTT Discovery configuration published successfully!")
        
    except Exception as e:
        print(f"Failed to publish discovery configuration: {e}")


def remove_discovery():
    """Remove Home Assistant MQTT Discovery configuration"""
    try:
        # List of discovery topics to clear
        discovery_topics = [
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/artist/config",
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/album/config", 
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/year/config",
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/track/config",
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/status/config",
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/volume/config",
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/yt_id/config"
        ]
        
        # Publish empty payloads to remove discovery
        for topic in discovery_topics:
            mqtt_client.publish(topic, "", retain=True)
            print(f"Removed discovery config from {topic}")
            time.sleep(0.1)
            
        print("Home Assistant MQTT Discovery configuration removed successfully!")
        
    except Exception as e:
        print(f"Failed to remove discovery configuration: {e}")