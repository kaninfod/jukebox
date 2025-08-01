import threading
from threading import Lock
import paho.mqtt.client as mqtt

MQTT_BROKER = "192.168.68.100"
MQTT_PORT = 1883
MQTT_ROOT = "jukebox"
MQTT_USERNAME = "mqtt-user"
MQTT_PASSWORD = "bart"

latest_mqtt_messages = {}
mqtt_message_lock = Lock()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(f"{MQTT_ROOT}/#")

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