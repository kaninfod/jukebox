import RPi.GPIO as GPIO
#GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


from fastapi import FastAPI
from app.routes.display import router as display_router
from app.routes.ytmusic import router as ytmusic_router, create_ytmusic_entry
#from routes.rfid import router as rfid_router
from app.mqtt import (
    start_mqtt,
    mqtt_client,
    mqtt_message_lock,
    latest_mqtt_messages,
    MQTT_ROOT,
)
from app.ili9488 import ILI9488
from app.rfid import RC522Reader
from app.pushbutton import PushButton
from app.rotaryencoder import RotaryEncoder

app = FastAPI()

app.include_router(display_router)
app.include_router(ytmusic_router)
#app.include_router(rfid_router)

display = ILI9488()

def handle_new_uid(uid):
    print(f"****New RFID tag detected: {uid}")
    display_text = f"RFID UID: {uid}"
    # Publish to MQTT
    mqtt_client.publish(f"{MQTT_ROOT}/test", display_text)
    # Show on display
    display.display_image(display_text)
    create_ytmusic_entry(uid)  # Create or update YTMusic entry

rfid_reader = RC522Reader(cs_pin=7, on_new_uid=handle_new_uid)

@app.on_event("startup")
def startup_event():
    start_mqtt()

@app.on_event("shutdown")
def shutdown_event():
    # Clean up GPIO resources
    display.cleanup()
    rfid_reader.stop()  # RC522Reader uses stop() method
    encoder.cleanup()
    # Note: You have two buttons defined, cleaning up both pins
    GPIO.remove_event_detect(19)
    GPIO.remove_event_detect(26)
    GPIO.cleanup()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI and Jukebox!"}


def on_button_press():
    print("Button was pressed!")



def on_rotate(position, direction):
    print(f"Rotary encoder moved to {position}, direction: {'CW' if direction > 0 else 'CCW'}")

encoder = RotaryEncoder(pin_a=5, pin_b=6, callback=on_rotate)
button = PushButton(19, callback=on_button_press)
button = PushButton(26, callback=on_button_press)
# import RPi.GPIO as GPIO
# #GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)  # or GPIO.BOARD, but BCM is common

# from fastapi import FastAPI, Path, Body
# from mqtt import (
#     start_mqtt,
#     mqtt_client,
#     mqtt_message_lock,
#     latest_mqtt_messages,
#     MQTT_ROOT,
# )
# from ili9488 import ILI9488
# from PIL import Image, ImageDraw
# from rfid import RC522Reader

# app = FastAPI()
# display = ILI9488()

# def handle_new_uid(uid):
#     print(f"New RFID tag detected: {uid}")
#     display_text = f"RFID UID: {uid}"
#     publish_message(subtopic="test", message=display_text)
#     display.display_image(display_text)
#     # Do something: update display, publish to MQTT, etc.

# rfid_reader = RC522Reader(cs_pin=7, on_new_uid=handle_new_uid)

# @app.on_event("startup")
# def startup_event():
#     start_mqtt()

# @app.get("/")
# def read_root():
#     return {"message": "Hello from FastAPI and MQTT!!"}

# @app.post("/publish/{subtopic:path}")
# def publish_message(
#     subtopic: str = Path(..., description="Subtopic under jukebox"),
#     message: str = Body(..., embed=True)
# ):
#     topic = f"{MQTT_ROOT}/{subtopic}"
#     mqtt_client.publish(topic, message)
#     return {"status": "Message published", "topic": topic, "message": message}

# @app.get("/mqtt_state/{subtopic:path}")
# def get_mqtt_state(subtopic: str = Path(..., description="Subtopic under jukebox")):
#     topic = f"{MQTT_ROOT}/{subtopic}"
#     with mqtt_message_lock:
#         state = latest_mqtt_messages.get(topic)
#     return {"topic": topic, "state": state}

# @app.post("/display/text")
# def display_text(text: str = Body(..., embed=True)):

#     display.display_image(text)
#     return {"status": "Text displayed"}

# @app.get("/rfid/read")
# def read_rfid():
#     uid = rfid_reader.get_latest_uid()
#     if uid:
#         return {"uid": uid}
#     else:
#         return {"status": "No card detected"}