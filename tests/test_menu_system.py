#!/usr/bin/env python3
"""
Comprehensive test suite for the new menu system (Phase 1 & 2)

Tests:
1. MenuBuilder - JSON loading and tree construction
2. Node lookup - Finding nodes by ID
3. Tree navigation - Moving through hierarchy
4. Event extraction - ActionType identification
5. MenuDataService - Navigation layer
6. MenuController integration - Full flow

Run on RPi: python test_menu_system.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ui.menu.menu_builder import (
    initialize_menu_tree, 
    get_menu_root, 
    find_menu_node,
    get_menu_builder
)
from app.ui.menu.menu_event_processor import (
    get_menu_event_processor,
    ActionType
)
from app.ui.menu.menu_data_service import MenuDataService
from app.ui.menu.menu_node import MenuNode


def print_header(test_num, test_name):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"Test {test_num}: {test_name}")
    print(f"{'='*70}")


def print_result(passed, message):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {message}")
    return passed


def test_1_menu_builder_loads_json():
    """Test 1: MenuBuilder loads JSON and creates tree"""
    print_header(1, "MenuBuilder Loads JSON and Creates Tree")
    
    try:
        root = initialize_menu_tree()
        
        # Verify root exists
        if not root:
            return print_result(False, "Root node is None")
        
        if root.id != "root":
            return print_result(False, f"Root ID is '{root.id}', expected 'root'")
        
        if root.name != "Root":
            return print_result(False, f"Root name is '{root.name}', expected 'Root'")
        
        print(f"  Root ID: {root.id}")
        print(f"  Root name: {root.name}")
        print(f"  Root direct children: {len(root.children)}")
        for child in root.children:
            print(f"    - {child.name} (id: {child.id}, children: {len(child.children)})")
            if child.children:
                for subchild in child.children[:3]:
                    print(f"        - {subchild.name} (id: {subchild.id})")
                if len(child.children) > 3:
                    print(f"        ... and {len(child.children) - 3} more")
        
        # Debug: Show all registered nodes
        builder = get_menu_builder()
        print(f"  Total nodes registered: {len(builder._nodes_by_id)}")
        
        # Verify children exist
        if len(root.children) < 2:
            return print_result(False, f"Root has {len(root.children)} children, expected at least 2")
        
        return print_result(True, "Root tree created successfully")
        
    except Exception as e:
        import traceback
        print(f"  Exception traceback: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def test_2_node_lookup_by_id():
    """Test 2: Find nodes by ID"""
    print_header(2, "Node Lookup by ID")
    
    try:
        # Test finding specific nodes (match actual node IDs in tree)
        tests = [
            ("root", "Root"),
            ("music", "🎵 Music"),
            ("artists_menu", "Artists"),
            ("artists_a_d", "A - D"),
            ("chromecasts", "🔊 Chromecasts"),
        ]
        
        all_passed = True
        for node_id, expected_name in tests:
            node = find_menu_node(node_id)
            if node is None:
                print(f"  ✗ Node '{node_id}' not found")
                # Try to find what nodes actually exist
                all_nodes = []
                builder = get_menu_builder()
                for nid in builder._nodes_by_id.keys():
                    all_nodes.append(nid)
                print(f"    Available nodes: {all_nodes}")
                all_passed = False
            elif node.name != expected_name:
                print(f"  ✗ Node '{node_id}' name is '{node.name}', expected '{expected_name}'")
                all_passed = False
            else:
                print(f"  ✓ Found: {node_id} = {node.name}")
        
        return print_result(all_passed, "All node lookups successful")
        
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")


def test_3_tree_navigation():
    """Test 3: Navigate through tree"""
    print_header(3, "Tree Navigation")
    
    try:
        root = get_menu_root()
        
        # Navigate: root → music
        music = root.get_child_by_id("music")
        if not music:
            return print_result(False, "Cannot find 'music' node")
        print(f"  ✓ root → {music.name}")
        
        # Navigate: music → browse_artists
        browse_artists = music.get_child_by_id("browse_artists")
        if not browse_artists:
            return print_result(False, "Cannot find 'browse_artists' node")
        print(f"  ✓ {music.name} → {browse_artists.name}")
        
        # Navigate: browse_artists → artists_menu (which should be a target reference)
        artists = find_menu_node("artists_menu")
        if not artists:
            return print_result(False, "Cannot find 'artists_menu' node")
        print(f"  ✓ Found {artists.name} node")
        
        # Verify artist groups exist
        artist_groups = [child for child in artists.children]
        if len(artist_groups) < 6:
            return print_result(False, f"Found {len(artist_groups)} artist groups, expected at least 6")
        print(f"  ✓ Found {len(artist_groups)} artist groups")
        
        # List artist groups
        for group in artist_groups:
            print(f"    - {group.name} (id: {group.id})")
        
        return print_result(True, "All navigation tests passed")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def test_4_event_extraction():
    """Test 4: Extract ActionType from nodes"""
    print_header(4, "Event Extraction and ActionType")
    
    try:
        processor = get_menu_event_processor()
        
        # Test 1: Load dynamic action (browse_artists_in_range)
        artists_a_d = find_menu_node("artists_a_d")
        if not artists_a_d:
            return print_result(False, "Cannot find artists_a_d node")
        
        event = processor.process_node_selection(artists_a_d)
        # The action is "load_dynamic" with dynamic_type="artists_in_range"
        if event.action_type != ActionType.LOAD_DYNAMIC:
            return print_result(False, f"Expected LOAD_DYNAMIC, got {event.action_type}")
        
        if event.parameters.get("start_letter") != "A":
            return print_result(False, f"Expected start_letter=A, got {event.parameters.get('start_letter')}")
        
        print(f"  ✓ Event 1: {event.action_type.value}")
        print(f"    Parameters: {event.parameters}")
        
        # Test 2: Navigate action (music node with children)
        music = find_menu_node("music")
        if not music:
            return print_result(False, "Cannot find music node")
        
        event = processor.process_node_selection(music)
        if event.action_type != ActionType.NAVIGATE:
            return print_result(False, f"Expected NAVIGATE, got {event.action_type}")
        
        print(f"  ✓ Event 2: {event.action_type.value} (has {len(music.children)} children)")
        
        # Test 3: Select device action (has explicit action in payload)
        device_node = find_menu_node("device_living_room")
        if not device_node:
            return print_result(False, "Cannot find device node")
        
        event = processor.process_node_selection(device_node)
        if event.action_type != ActionType.SELECT_DEVICE:
            return print_result(False, f"Expected SELECT_DEVICE, got {event.action_type}")
        
        print(f"  ✓ Event 3: {event.action_type.value}")
        print(f"    Parameters: {event.parameters}")
        
        return print_result(True, "All event extraction tests passed")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def test_5_menu_data_service():
    """Test 5: MenuDataService navigation"""
    print_header(5, "MenuDataService Navigation")
    
    try:
        service = MenuDataService()
        
        # Test 1: Start at root
        current = service.get_current_node()
        if current.id != "root":
            return print_result(False, f"Expected root, got {current.id}")
        print(f"  ✓ Start at: {current.name}")
        
        # Test 2: Get menu items (children)
        items = service.get_current_menu_items()
        if len(items) < 2:
            return print_result(False, f"Root has {len(items)} items, expected at least 2")
        print(f"  ✓ Root items: {len(items)}")
        for item in items:
            print(f"    - {item.name}")
        
        # Test 3: Navigate to node
        music_node = find_menu_node("music")
        if not service.navigate_to_node(music_node):
            return print_result(False, "Cannot navigate to Music")
        
        current = service.get_current_node()
        if current.id != "music":
            return print_result(False, f"Expected music, got {current.id}")
        print(f"  ✓ Navigate to: {current.name}")
        
        # Test 4: Get music submenu items
        items = service.get_current_menu_items()
        print(f"  ✓ Music items: {len(items)}")
        for item in items:
            print(f"    - {item.name}")
        
        # Test 5: Go back
        if not service.go_back():
            return print_result(False, "Cannot go back from Music")
        
        current = service.get_current_node()
        if current.id != "root":
            return print_result(False, f"Expected root after go_back, got {current.id}")
        print(f"  ✓ Go back to: {current.name}")
        
        return print_result(True, "All MenuDataService tests passed")
        
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")


def test_6_full_integration():
    """Test 6: Full integration flow"""
    print_header(6, "Full Integration Flow")
    
    try:
        service = MenuDataService()
        processor = get_menu_event_processor()
        
        # Simulate user navigating: root → Music → Artists → A-D
        print(f"  Step 1: Start at {service.get_current_node().name}")
        
        # Get root's first child (Music)
        root_items = service.get_current_menu_items()
        music_item = next((item for item in root_items if item.id == "music"), None)
        if not music_item:
            return print_result(False, "Cannot find Music in root items")
        
        # Navigate to Music
        if not service.navigate_to_node(music_item):
            return print_result(False, "Cannot navigate to Music")
        print(f"  Step 2: Navigate to {service.get_current_node().name}")
        
        # Get Music's children and find Browse Artists
        music_items = service.get_current_menu_items()
        browse_artists_item = next((item for item in music_items if item.id == "browse_artists"), None)
        if not browse_artists_item:
            return print_result(False, "Cannot find Browse Artists in Music items")
        
        # Process the browse_artists item - it should have a target to artists_menu
        event = processor.process_node_selection(browse_artists_item)
        print(f"  Step 3: Select {browse_artists_item.name}")
        print(f"         Action: {event.action_type.value}, Payload: {browse_artists_item.payload}")
        
        # Navigate to the artists menu directly
        artists_menu = find_menu_node("artists_menu")
        if not artists_menu:
            return print_result(False, "Cannot find artists_menu")
        
        if not service.navigate_to_node(artists_menu):
            return print_result(False, "Cannot navigate to artists_menu")
        print(f"  Step 4: Navigate to {service.get_current_node().name}")
        
        # Get artist groups
        artists_items = service.get_current_menu_items()
        a_d_item = next((item for item in artists_items if item.id == "artists_a_d"), None)
        if not a_d_item:
            return print_result(False, "Cannot find A-D artist group")
        
        # Process selection on A-D
        event = processor.process_node_selection(a_d_item)
        if event.action_type != ActionType.LOAD_DYNAMIC:
            return print_result(False, f"Expected LOAD_DYNAMIC, got {event.action_type}")
        print(f"  Step 5: Select {a_d_item.name} → Action: {event.action_type.value}")
        print(f"         Parameters: {event.parameters}")
        
        # Navigate back to root
        if not service.go_back():
            return print_result(False, "Cannot go back from artists_menu")
        if not service.go_back():
            return print_result(False, "Cannot go back from music")
        print(f"  Step 6: Go back twice to {service.get_current_node().name}")
        
        return print_result(True, "Full integration flow successful")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("MENU SYSTEM TEST SUITE - Phase 1 & 2 Verification")
    print("="*70)
    
    results = []
    
    # Run all tests
    results.append(("MenuBuilder Loads JSON", test_1_menu_builder_loads_json()))
    results.append(("Node Lookup by ID", test_2_node_lookup_by_id()))
    results.append(("Tree Navigation", test_3_tree_navigation()))
    results.append(("Event Extraction", test_4_event_extraction()))
    results.append(("MenuDataService", test_5_menu_data_service()))
    results.append(("Full Integration", test_6_full_integration()))
    
    # Summary
    print(f"\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 1 & 2 implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
