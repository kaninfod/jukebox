#!/usr/bin/env python3
"""
Quick test to verify the renaming worked correctly
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_import():
    """Test that JsonMenuAdapter can be imported and works"""
    print("🧪 Testing JsonMenuAdapter import and basic functionality...")
    
    try:
        from app.ui.menu.json_menu_adapter import JsonMenuAdapter
        print("✅ Import successful")
        
        adapter = JsonMenuAdapter()
        print("✅ JsonMenuAdapter instance created")
        
        success = adapter.load_config()
        if success:
            print("✅ Config loaded successfully")
            
            # Test getting menu data
            root_items = adapter.get_menu_items('root')
            print(f"✅ Root menu has {len(root_items)} items")
            
            chromecasts_items = adapter.get_menu_items('chromecasts_menu')
            print(f"✅ Chromecasts menu has {len(chromecasts_items)} items")
            
            return True
        else:
            print("❌ Config failed to load")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing JsonMenuAdapter Rename")
    print("=" * 40)
    
    if test_import():
        print("\n🎉 RENAME SUCCESSFUL!")
        print("✅ JsonMenuAdapter is working properly")
    else:
        print("\n❌ Issues found")
