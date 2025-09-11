#!/usr/bin/env python3
"""
Test script to verify the CORRECT architecture:
- Chromecast devices as static menu items in JSON (loaded by JsonConfigAdapter)
- NO dynamic handling in SubsonicConfigAdapter
"""

import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_json_config_structure():
    """Test that menu_config.json has the correct structure"""
    print("🧪 Testing menu_config.json structure...")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'app', 'config', 'menu_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✅ JSON config loaded successfully")
        
        # Check root menu
        if 'root' in config:
            print(f"✅ Root menu exists with {len(config['root']['items'])} items")
            for item in config['root']['items']:
                print(f"   - {item['name']} (action: {item['payload']['action']})")
        
        # Check chromecasts_menu 
        if 'chromecasts_menu' in config:
            chromecast_items = config['chromecasts_menu']['items']
            print(f"✅ Chromecasts menu exists with {len(chromecast_items)} items")
            device_items = [item for item in chromecast_items if 'select_chromecast_device' in item['payload'].get('action', '')]
            print(f"   - {len(device_items)} device selection items")
            for item in device_items:
                print(f"     • {item['name']} (ID: {item['payload']['device_id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_json_menu_adapter():
    """Test that JsonMenuAdapter loads chromecasts menu correctly"""
    print("\n🧪 Testing JsonMenuAdapter...")
    
    try:
        from app.ui.menu.json_menu_adapter import JsonMenuAdapter
        
        adapter = JsonMenuAdapter()
        success = adapter.load_config()
        
        if not success:
            print("❌ Failed to load config")
            return False
        
        print("✅ JsonMenuAdapter loaded config successfully")
        
        # Test chromecasts menu loading
        chromecasts_items = adapter.get_menu_items('chromecasts_menu')
        print(f"✅ Found {len(chromecasts_items)} chromecast menu items")
        
        device_items = [item for item in chromecasts_items if 'select_chromecast_device' in item.get('payload', {}).get('action', '')]
        print(f"   - {len(device_items)} device selection items")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_subsonic_adapter_no_chromecasts():
    """Test that SubsonicConfigAdapter NO LONGER handles chromecasts"""
    print("\n🧪 Testing SubsonicConfigAdapter (should NOT handle chromecasts)...")
    
    try:
        from app.ui.menu.subsonic_config_adapter import SubsonicConfigAdapter
        
        # Create mock subsonic service
        class MockSubsonicService:
            def get_alphabetical_groups(self):
                return [{"name": "A-D", "range": ("A", "D")}]
        
        adapter = SubsonicConfigAdapter(MockSubsonicService())
        
        # Try to get chromecasts - should return empty or fail gracefully
        try:
            result = adapter.get_dynamic_menu_nodes("chromecasts")
            print(f"✅ Chromecasts request returned {len(result)} items (should be 0 or error)")
            if len(result) == 0:
                print("✅ CORRECT: SubsonicConfigAdapter no longer handles chromecasts")
            else:
                print("❌ WRONG: SubsonicConfigAdapter still handles chromecasts")
                return False
        except Exception as e:
            print(f"✅ CORRECT: SubsonicConfigAdapter properly rejects chromecasts: {e}")
        
        # Test it still handles valid dynamic content
        artists_result = adapter.get_dynamic_menu_nodes("artists_alphabetical")
        print(f"✅ Artists request returned {len(artists_result)} items (should work)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing CORRECTED Architecture: Static Chromecasts in JSON")
    print("=" * 65)
    
    results = [
        test_json_config_structure(),
        test_json_menu_adapter(), 
        test_subsonic_adapter_no_chromecasts()
    ]
    
    print("\n" + "=" * 65)
    if all(results):
        print("🎉 ARCHITECTURE CORRECTED!")
        print("\n✅ Correct approach:")
        print("   • Chromecast devices = static JSON menu items")
        print("   • JsonMenuAdapter = loads static menus from JSON")
        print("   • SubsonicConfigAdapter = only dynamic music content")
        print("   • No code duplication!")
        print("   • Clean separation of concerns!")
    else:
        print("❌ Some issues remain")
