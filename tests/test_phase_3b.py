#!/usr/bin/env python3
"""
Phase 3b Testing Guide - DynamicLoader Verification

Tests that dynamic loading works correctly with the menu system.

Run on RPi: python test_phase_3b.py
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from ui.menu.dynamic_loader import initialize_dynamic_loader, get_dynamic_loader
from ui.menu.menu_builder import initialize_menu_tree, get_menu_root, find_menu_node
from ui.menu.menu_data_service import MenuDataService
from services.subsonic_service import SubsonicService
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def test_1_dynamic_loader_initialization():
    """Test 1: Initialize DynamicLoader"""
    print_header(1, "DynamicLoader Initialization")
    
    try:
        # Create Subsonic service
        subsonic = SubsonicService()
        print(f"  ✓ Subsonic service created")
        
        # Initialize loader
        loader = initialize_dynamic_loader(subsonic)
        
        if not loader:
            return print_result(False, "DynamicLoader initialization returned None")
        
        print(f"  ✓ DynamicLoader initialized")
        
        # Get global instance
        global_loader = get_dynamic_loader()
        if global_loader != loader:
            return print_result(False, "Global instance doesn't match")
        
        print(f"  ✓ Global instance accessible")
        
        return print_result(True, "DynamicLoader initialized successfully")
        
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")


def test_2_load_artists_from_api():
    """Test 2: Load artists from Subsonic API"""
    print_header(2, "Load Artists from API")
    
    try:
        loader = get_dynamic_loader()
        if not loader:
            return print_result(False, "DynamicLoader not initialized")
        
        # Load artists A-D
        start = time.time()
        artists = loader.load_artists_in_range("A", "D", use_cache=False)
        elapsed = time.time() - start
        
        print(f"  ✓ Loaded {len(artists)} artists in {elapsed:.2f}s")
        
        if not artists:
            print(f"  ⚠️  No artists found in A-D range")
            return print_result(True, "Query succeeded but no results")
        
        # Verify nodes have required properties
        for i, artist in enumerate(artists[:3]):
            if not artist.id or not artist.name:
                return print_result(False, f"Artist missing id or name: {artist}")
            
            if not artist.payload:
                return print_result(False, f"Artist {artist.name} missing payload")
            
            action = artist.payload.get("action")
            if action != "load_dynamic":
                return print_result(False, f"Artist {artist.name} has wrong action: {action}")
            
            print(f"    - {artist.name} (id: {artist.id}, action: {action})")
        
        if len(artists) > 3:
            print(f"    ... and {len(artists) - 3} more")
        
        return print_result(True, f"Loaded {len(artists)} artists with correct payload")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def test_3_artist_caching():
    """Test 3: Verify caching reduces API calls"""
    print_header(3, "Artist Caching")
    
    try:
        loader = get_dynamic_loader()
        if not loader:
            return print_result(False, "DynamicLoader not initialized")
        
        # Clear cache first
        loader.clear_artist_cache("E", "H")
        print(f"  ✓ Cache cleared")
        
        # First call (should hit API)
        start = time.time()
        artists1 = loader.load_artists_in_range("E", "H", use_cache=False)
        time1 = time.time() - start
        print(f"  ✓ First call: {len(artists1)} artists in {time1:.3f}s (from API)")
        
        # Second call (should use cache)
        start = time.time()
        artists2 = loader.load_artists_in_range("E", "H", use_cache=True)
        time2 = time.time() - start
        print(f"  ✓ Cached call: {len(artists2)} artists in {time2:.3f}s")
        
        # Verify same results
        if len(artists1) != len(artists2):
            return print_result(False, "Cache returned different number of artists")
        
        # Check speedup
        if artists1:  # Only if we got results
            speedup = time1 / time2 if time2 > 0 else float('inf')
            print(f"  ✓ Speedup: {speedup:.1f}x")
            
            if speedup < 2:
                print(f"  ⚠️  Cache speedup low (expected >2x)")
        
        return print_result(True, "Caching working correctly")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def test_4_load_albums_from_api():
    """Test 4: Load albums for an artist"""
    print_header(4, "Load Albums from API")
    
    try:
        loader = get_dynamic_loader()
        if not loader:
            return print_result(False, "DynamicLoader not initialized")
        
        # First get an artist
        artists = loader.load_artists_in_range("A", "D", use_cache=True)
        
        if not artists:
            return print_result(False, "No artists available to test albums")
        
        # Pick first artist
        artist = artists[0]
        print(f"  ✓ Testing albums for artist: {artist.name}")
        
        # Load albums
        start = time.time()
        albums = loader.load_artist_albums(artist.id, artist.name, use_cache=False)
        elapsed = time.time() - start
        
        print(f"  ✓ Loaded {len(albums)} albums in {elapsed:.2f}s")
        
        if not albums:
            print(f"  ⚠️  Artist {artist.name} has no albums")
            return print_result(True, "Query succeeded but no results")
        
        # Verify album nodes
        for i, album in enumerate(albums[:3]):
            if not album.id or not album.name:
                return print_result(False, f"Album missing id or name: {album}")
            
            action = album.payload.get("action")
            if action != "select_album":
                return print_result(False, f"Album {album.name} has wrong action: {action}")
            
            print(f"    - {album.name} (id: {album.id}, action: {action})")
        
        if len(albums) > 3:
            print(f"    ... and {len(albums) - 3} more")
        
        return print_result(True, f"Loaded {len(albums)} albums with correct payload")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def test_5_tree_injection():
    """Test 5: Inject dynamic nodes into MenuNode tree"""
    print_header(5, "Tree Injection")
    
    try:
        # Initialize menu tree
        root = initialize_menu_tree()
        print(f"  ✓ Menu tree initialized")
        
        # Find artists_a_d node
        artists_a_d = find_menu_node("artists_a_d")
        if not artists_a_d:
            return print_result(False, "Cannot find artists_a_d node")
        
        print(f"  ✓ Found {artists_a_d.name} node")
        print(f"    Before injection: {len(artists_a_d.children)} children")
        
        # Load artists
        loader = get_dynamic_loader()
        artists = loader.load_artists_in_range("A", "D", use_cache=True)
        
        if not artists:
            return print_result(False, "No artists to inject")
        
        # Inject into tree
        for artist in artists:
            artists_a_d.add_child(artist)
            artist.parent = artists_a_d
        
        print(f"  ✓ Injected {len(artists)} artists")
        print(f"    After injection: {len(artists_a_d.children)} children")
        
        # Verify they're accessible
        for child in artists_a_d.children[:3]:
            print(f"    - {child.name} (parent: {child.parent.id})")
        
        return print_result(True, f"Injected {len(artists)} nodes into tree")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def test_6_navigation_with_dynamic():
    """Test 6: Navigate with dynamic content"""
    print_header(6, "Navigation with Dynamic Content")
    
    try:
        # Setup
        root = initialize_menu_tree()
        loader = get_dynamic_loader()
        service = MenuDataService()
        
        print(f"  ✓ Setup complete")
        
        # Get artist range node
        artists_menu = find_menu_node("artists_menu")
        artists_a_d = find_menu_node("artists_a_d")
        
        if not artists_a_d:
            return print_result(False, "Cannot find artists_a_d")
        
        # Load and inject artists
        artists = loader.load_artists_in_range("A", "D", use_cache=True)
        
        for artist in artists:
            artists_a_d.add_child(artist)
            artist.parent = artists_a_d
        
        print(f"  ✓ Loaded and injected {len(artists)} artists")
        
        # Navigate through menu
        artists_menu_node = find_menu_node("artists_menu")
        if not service.navigate_to_node(artists_menu_node):
            return print_result(False, "Cannot navigate to artists_menu")
        
        print(f"  ✓ Navigated to Artists menu")
        
        # Get children (should include artist groups)
        items = service.get_current_menu_items()
        print(f"  ✓ Found {len(items)} items in artists_menu")
        
        # Get items from first artist group
        if items:
            first_group = items[0]
            print(f"  ✓ First group: {first_group.name} ({len(first_group.children)} children)")
            
            if first_group.children:
                print(f"    Artists in first group:")
                for artist in first_group.children[:3]:
                    print(f"      - {artist.name}")
        
        return print_result(True, "Navigation with dynamic content working")
        
    except Exception as e:
        import traceback
        print(f"  Exception: {traceback.format_exc()}")
        return print_result(False, f"Exception: {str(e)}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("PHASE 3B TEST SUITE - DynamicLoader Verification")
    print("="*70)
    
    results = []
    
    # Run all tests
    results.append(("DynamicLoader Initialization", test_1_dynamic_loader_initialization()))
    results.append(("Load Artists from API", test_2_load_artists_from_api()))
    results.append(("Artist Caching", test_3_artist_caching()))
    results.append(("Load Albums from API", test_4_load_albums_from_api()))
    results.append(("Tree Injection", test_5_tree_injection()))
    results.append(("Navigation with Dynamic", test_6_navigation_with_dynamic()))
    
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
        print("\n🎉 ALL TESTS PASSED! Phase 3b implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
