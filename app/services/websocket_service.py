import json
import asyncio
import websockets
import threading
import signal
from typing import Any, Dict, Optional
from app.config import config
import logging
from app.services.jukebox_mediaplayer import JukeboxMediaPlayer, PlayerStatus

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        self.websocket_connection = None
        self.websocket_task = None
        self.is_websocket_running = False
        self.websocket_lock = threading.Lock()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"WebSocket: Received signal {signum}, shutting down...")
        self.stop()

    async def handle_state_change(self, event_data: Dict[str, Any]) -> None:
        try:
            entity_id = event_data.get("entity_id")
            media_player_entity_id = getattr(config, "MEDIA_PLAYER_ENTITY_ID", None)
            if entity_id != media_player_entity_id:
                return
            new_state = event_data.get("new_state", {})
            old_state = event_data.get("old_state", {})
            state = new_state.get("state", "idle")
            old_status = old_state.get("state", None)
            ha_volume = new_state.get("attributes", {}).get("volume_level")
            old_volume = old_state.get("attributes", {}).get("volume_level") if old_state else None
            if old_status == "playing" and state == "idle":
                from app.core import event_bus, EventType, Event
                event_bus.emit(Event(
                    type=EventType.HA_STATE_CHANGED,
                    payload={"from": old_status, "to": state}
                ))

                # from app.core.event_bus import event_bus, Event
                # event_bus.emit(Event(type="ha_state_changed", payload={"from": old_status, "to": state}))
                logger.info("Emitted 'ha_state_changed' event.")
            if ha_volume is not None and ha_volume != old_volume:
                from app.core import event_bus, EventType, Event
                event_bus.emit(Event(
                    type=EventType.HA_VOLUME_CHANGED,
                    payload={"volume": ha_volume}
                ))

                # from app.core.event_bus import event_bus, Event
                # event_bus.emit(Event(type="ha_volume_changed", payload={"volume": ha_volume}))
                logger.info(f"Emitted 'ha_volume_changed' event: {ha_volume}")
        except Exception as e:
            logger.error(f"WebSocket: Error handling state change: {e}")

    async def websocket_client(self) -> None:
        backoff = 1
        max_backoff = 60
        while True:
            try:
                logger.info("WebSocket: Connecting to Home Assistant...")
                async with websockets.connect(config.HA_WS_URL) as websocket:
                    with self.websocket_lock:
                        self.websocket_connection = websocket
                        self.is_websocket_running = True
                    auth_required = await websocket.recv()
                    logger.debug(f"WebSocket: {auth_required}")
                    auth_message = {"type": "auth", "access_token": config.HA_TOKEN}
                    await websocket.send(json.dumps(auth_message))
                    auth_response = await websocket.recv()
                    logger.debug(f"WebSocket: {auth_response}")
                    subscribe_message = {"id": 1, "type": "subscribe_events", "event_type": "state_changed"}
                    await websocket.send(json.dumps(subscribe_message))
                    subscribe_response = await websocket.recv()
                    logger.debug(f"WebSocket: {subscribe_response}")
                    logger.info("WebSocket: Connected and subscribed to state changes")
                    async for message in websocket:
                        if not self.is_websocket_running:
                            logger.info("WebSocket: Shutdown requested, stopping message loop")
                            break
                        try:
                            data = json.loads(message)
                            if (data.get("type") == "event" and data.get("event", {}).get("event_type") == "state_changed"):
                                event_data = data.get("event", {}).get("data", {})
                                await self.handle_state_change(event_data)
                        except json.JSONDecodeError:
                            logger.warning(f"WebSocket: Invalid JSON received: {message}")
                        except Exception as e:
                            logger.error(f"WebSocket: Error processing message: {e}")
            except Exception as e:
                logger.error(f"WebSocket: Connection error: {e}")
                logger.info(f"WebSocket: Reconnecting in {backoff} seconds...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
            finally:
                with self.websocket_lock:
                    self.is_websocket_running = False
                    self.websocket_connection = None
                logger.info("WebSocket: Disconnected")
            if not self.is_websocket_running:
                break

    def start_background(self) -> bool:
        def run_websocket():
            asyncio.new_event_loop().run_until_complete(self.websocket_client())
        if not self.is_websocket_running:
            self.websocket_task = threading.Thread(target=run_websocket, daemon=True)
            self.websocket_task.start()
            return True
        return False

    def start(self) -> Dict[str, str]:
        try:
            if self.is_websocket_running:
                return {"status": "already_running", "message": "WebSocket is already connected"}
            success = self.start_background()
            if success:
                return {"status": "starting", "message": "WebSocket connection initiated"}
            else:
                return {"status": "failed", "message": "Failed to start WebSocket"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to start WebSocket: {str(e)}"}

    def status(self) -> Dict[str, Any]:
        with self.websocket_lock:
            return {
                "is_running": self.is_websocket_running,
                "connection_active": self.websocket_connection is not None
            }

    def stop(self) -> Dict[str, str]:
        logger.info("Stopping WebSocket connection...")
        with self.websocket_lock:
            self.is_websocket_running = False
            self.websocket_connection = None
        import time
        time.sleep(0.1)
        return {"status": "stopped", "message": "WebSocket connection terminated"}

    def cleanup(self):
        logger.info("WebSocketClient cleanup called")
        # Add any additional cleanup logic here if needed

# Singleton instance
websocket_service = WebSocketService()
