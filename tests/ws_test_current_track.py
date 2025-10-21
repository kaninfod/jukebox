import asyncio
import websockets
import json

WS_URL = "ws://localhost:8000/ws/mediaplayer/current_track"

async def listen():
    async with websockets.connect(WS_URL) as websocket:
        print(f"Connected to {WS_URL}")
        try:
            while True:
                msg = await websocket.recv()
                try:
                    data = json.loads(msg)
                except Exception:
                    data = msg
                print("Received:", data)
        except websockets.ConnectionClosed:
            print("WebSocket connection closed.")

if __name__ == "__main__":
    asyncio.run(listen())
