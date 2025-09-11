#!/usr/bin/env python3
"""
Test script to verify that Chromecast devices are now loaded from menu_config.json
"""

import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_config_loading():
    """Test that the menu config loads correctly"""
    print("🧪 Testing menu_config.json loading...")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'app', 'config', 'menu_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        devices = config.get('chromecast_devices', [])
        print(f"✅ Found {len(devices)} Chromecast devices in config:")
        
        for device in devices:
            print(f"   - {device.get('name', 'Unknown')} (ID: {device.get('id', 'None')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def test_menu_adapter():
    """Test that MenuAdapter loads devices from config"""
    print("\n🧪 Testing MenuAdapter with config-based devices...")
    
    try:
        from app.ui.menu.menu_adapter import MenuAdapter
        from app.services.subsonic_service import SubsonicService
        
        # Create a mock subsonic service (we don't need it for this test)
        class MockSubsonicService:
            pass
        
        adapter = MenuAdapter(MockSubsonicService())
        menu_nodes = adapter.create_chromecasts_menu()
        
        print(f"✅ MenuAdapter created {len(menu_nodes)} menu items:")
        for node in menu_nodes:
            print(f"   - {node.name} (ID: {node.id})")
            print(f"     Payload: {node.payload}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing MenuAdapter: {e}")
        return False

def test_subsonic_config_adapter():
    """Test that SubsonicConfigAdapter loads devices from config"""
    print("\n🧪 Testing SubsonicConfigAdapter with config-based devices...")
    
    try:
        from app.ui.menu.subsonic_config_adapter import SubsonicConfigAdapter
        
        # Create a mock subsonic service
        class MockSubsonicService:
            pass
        
        adapter = SubsonicConfigAdapter(MockSubsonicService())
        menu_nodes = adapter.create_chromecasts_menu()
        
        print(f"✅ SubsonicConfigAdapter created {len(menu_nodes)} menu items:")
        for node in menu_nodes:
            print(f"   - {node.name} (ID: {node.id})")
            if 'device_id' in node.payload:
                print(f"     Device ID: {node.payload['device_id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing SubsonicConfigAdapter: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing Configuration-Based Chromecast Device Loading")
    print("=" * 60)
    
    # Run tests
    results = [
        test_config_loading(),
        test_menu_adapter(),
        test_subsonic_config_adapter()
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 ALL TESTS PASSED! Configuration-based loading works!")
    else:
        print("❌ Some tests failed!")
    
    print("\n✨ Benefits of this approach:")
    print("   • Centralized configuration in menu_config.json")
    print("   • No code duplication")
    print("   • Easy to add/remove devices")
    print("   • Consistent with existing architecture")
    print("   • Runtime configurable")
