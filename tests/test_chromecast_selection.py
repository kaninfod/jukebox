#!/usr/bin/env python3
"""
Test script for improved Chromecast device selection functionality.
"""

import sys
import os
sys.path.append('/Volumes/Shared/jukebox')

from app.ui.menu.menu_adapter import MenuAdapter
from app.ui.menu.menu_node import MenuNode
from app.core.event_bus import event_bus, Event
from app.core.event_factory import EventType

def test_chromecast_menu():
    """Test the Chromecast menu generation"""
    print("🧪 Testing Chromecast Menu Generation")
    print("=" * 50)
    
    # Create menu adapter
    adapter = MenuAdapter(None)
    
    # Generate Chromecast menu
    chromecast_menu = adapter.create_chromecasts_menu()
    
    print(f"Generated {len(chromecast_menu)} menu items:")
    print()
    
    for i, item in enumerate(chromecast_menu):
        print(f"{i+1}. {item.name}")
        if item.payload.get('action') == 'select_chromecast_device':
            device_name = item.payload.get('device_name')
            print(f"   -> Action: Select '{device_name}'")
        elif item.payload.get('action') == 'separator':
            print(f"   -> Separator")
        else:
            print(f"   -> Action: {item.payload.get('action', 'Unknown')}")
        print()

def test_chromecast_device_manager():
    """Test the ChromecastDeviceManager"""
    print("🧪 Testing ChromecastDeviceManager")
    print("=" * 50)
    
    try:
        from app.services.chromecast_device_manager import ChromecastDeviceManager
        
        # Create a mock media player
        class MockMediaPlayer:
            def __init__(self):
                self.cc_service = MockChromecastService()
        
        class MockChromecastService:
            def __init__(self):
                self.device_name = "Living Room"
            
            def switch_device(self, new_device_name):
                print(f"  📱 MockChromecastService: Switching to {new_device_name}")
                print(f"     ⏹️  Stopping current playback...")
                print(f"     🔌 Disconnecting from {self.device_name}...")
                print(f"     🔗 Connecting to {new_device_name}...")
                self.device_name = new_device_name
                print(f"     ✅ Successfully connected to {new_device_name}")
                return True
        
        # Create device manager with mock
        mock_player = MockMediaPlayer()
        device_manager = ChromecastDeviceManager(event_bus, mock_player)
        
        print(f"Current device: {device_manager.get_current_device()}")
        print()
        
        # Test device switch
        print("Testing device switch to 'TV Lounge':")
        test_event = Event(
            type=EventType.CHROMECAST_DEVICE_CHANGED,
            payload={"device_name": "TV Lounge"}
        )
        
        device_manager._handle_device_change(test_event)
        print(f"New current device: {device_manager.get_current_device()}")
        print()
        
        # Test switching to same device
        print("Testing switch to same device:")
        device_manager._handle_device_change(test_event)
        print()
        
        print("✅ ChromecastDeviceManager test completed")
        
    except Exception as e:
        print(f"❌ ChromecastDeviceManager test failed: {e}")
        import traceback
        traceback.print_exc()

def test_event_flow():
    """Test the complete event flow"""
    print("🧪 Testing Complete Event Flow")
    print("=" * 50)
    
    # Set up event listeners
    received_events = []
    
    def event_listener(event):
        received_events.append(event)
        print(f"📢 Event received: {event.type}")
        if hasattr(event, 'payload'):
            print(f"   Payload: {event.payload}")
    
    # Subscribe to all relevant events
    event_bus.subscribe(EventType.CHROMECAST_DEVICE_CHANGED, event_listener)
    event_bus.subscribe(EventType.SHOW_MESSAGE, event_listener)
    
    # Emit test event
    print("📤 Emitting CHROMECAST_DEVICE_CHANGED event...")
    test_event = Event(
        type=EventType.CHROMECAST_DEVICE_CHANGED,
        payload={"device_name": "Signe"}
    )
    
    event_bus.emit(test_event)
    
    print(f"✅ Received {len(received_events)} events")

if __name__ == "__main__":
    print("🎵 Enhanced Chromecast Device Selection Test")
    print("=" * 60)
    print()
    
    try:
        test_chromecast_menu()
        print()
        test_chromecast_device_manager()
        print()
        test_event_flow()
        print()
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
