"""
Quick verification test for Phase 1-2 components.
Run this to ensure MenuBuilder, MenuEventProcessor, and MenuDataService work correctly.

Usage:
    python test_phase_1_2.py
"""

import sys
import json
from pathlib import Path

# Add app to path
app_root = Path(__file__).parent
sys.path.insert(0, str(app_root))

def test_menu_builder():
    """Test MenuBuilder loads JSON and builds tree"""
    print("\n📦 Testing MenuBuilder...")
    
    try:
        from app.ui.menu.menu_builder import MenuBuilder
        
        # Create builder
        builder = MenuBuilder()
        
        # Load config
        config = builder.load_config()
        print(f"  ✅ Loaded config with {len(config)} sections")
        
        # Build tree
        root = builder.build_tree()
        print(f"  ✅ Built tree with root node: {root.id}")
        print(f"  ✅ Root has {len(root.children)} children")
        
        # Test node lookup
        node = builder.get_node_by_id("root")
        assert node is not None
        print(f"  ✅ Node lookup works: found {node.name}")
        
        return True
    except Exception as e:
        print(f"  ❌ MenuBuilder test failed: {e}")
        return False


def test_menu_node():
    """Test MenuNode hierarchy"""
    print("\n🌳 Testing MenuNode...")
    
    try:
        from app.ui.menu.menu_node import MenuNode
        
        # Create nodes
        root = MenuNode(id="root", name="Root")
        child = MenuNode(id="child1", name="Child 1", parent=root)
        grandchild = MenuNode(id="grandchild1", name="Grandchild 1", parent=child)
        
        # Add to hierarchy
        root.add_child(child)
        child.add_child(grandchild)
        
        print(f"  ✅ Created hierarchy: {root.name} -> {child.name} -> {grandchild.name}")
        
        # Test lookups
        found_child = root.get_child_by_id("child1")
        assert found_child == child
        print(f"  ✅ Child lookup works")
        
        # Test to_dict
        node_dict = child.to_dict()
        assert node_dict["id"] == "child1"
        assert node_dict["name"] == "Child 1"
        print(f"  ✅ to_dict() conversion works")
        
        return True
    except Exception as e:
        print(f"  ❌ MenuNode test failed: {e}")
        return False


def test_menu_event_processor():
    """Test MenuEventProcessor action extraction"""
    print("\n⚡ Testing MenuEventProcessor...")
    
    try:
        from app.ui.menu.menu_event_processor import MenuEventProcessor, ActionType
        from app.ui.menu.menu_node import MenuNode
        
        processor = MenuEventProcessor()
        
        # Create node with action
        node = MenuNode(
            id="test_action",
            name="Test Action",
            payload={
                "action": "browse_artists_in_range",
                "start_letter": "A",
                "end_letter": "D"
            }
        )
        
        # Process selection
        event = processor.process_node_selection(node)
        
        assert event is not None
        print(f"  ✅ Event created: {event}")
        
        assert event.action_type == ActionType.BROWSE_ARTISTS_IN_RANGE
        print(f"  ✅ Action type correctly identified: {event.action_type.value}")
        
        assert event.parameters["start_letter"] == "A"
        print(f"  ✅ Parameters extracted correctly")
        
        # Test navigation node (no payload)
        nav_node = MenuNode(id="nav", name="Navigation", children=[])
        nav_event = processor.process_node_selection(nav_node)
        assert nav_event.action_type == ActionType.NAVIGATE
        print(f"  ✅ Navigation node creates NAVIGATE event")
        
        return True
    except Exception as e:
        print(f"  ❌ MenuEventProcessor test failed: {e}")
        return False


def test_menu_data_service():
    """Test MenuDataService with tree"""
    print("\n📊 Testing MenuDataService...")
    
    try:
        from app.ui.menu.menu_data_service import MenuDataService
        
        service = MenuDataService()
        print(f"  ✅ MenuDataService initialized")
        
        # Check current node
        current = service.get_current_node()
        assert current is not None
        print(f"  ✅ Current node: {current.id}")
        
        # Check breadcrumb
        breadcrumb = service.get_breadcrumb_path()
        print(f"  ✅ Breadcrumb: {' > '.join(breadcrumb)}")
        
        # Check menu count
        count = service.get_menu_count()
        print(f"  ✅ Current menu has {count} items")
        
        # Navigate to first child if available
        if count > 0:
            items = service.get_current_menu_items()
            if items:
                first_child = items[0]
                service.navigate_to_node(first_child)
                print(f"  ✅ Navigation works, moved to: {service.get_current_node().name}")
                
                # Test go back
                service.go_back()
                print(f"  ✅ Go back works, returned to: {service.get_current_node().id}")
        
        return True
    except Exception as e:
        print(f"  ❌ MenuDataService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test all components working together"""
    print("\n🔗 Testing Integration...")
    
    try:
        from app.ui.menu.menu_builder import initialize_menu_tree, find_menu_node
        from app.ui.menu.menu_data_service import MenuDataService
        from app.ui.menu.menu_event_processor import get_menu_event_processor, ActionType
        
        # Initialize tree
        root = initialize_menu_tree()
        print(f"  ✅ Global tree initialized")
        
        # Find a specific node
        node = find_menu_node("root")
        assert node == root
        print(f"  ✅ Global node lookup works")
        
        # Use MenuDataService with tree
        service = MenuDataService()
        assert service.get_current_node() == root
        print(f"  ✅ MenuDataService uses global tree")
        
        # Use event processor
        processor = get_menu_event_processor()
        
        # Create a test action and process it
        children = root.children
        if children:
            first_child = children[0]
            event = processor.process_node_selection(first_child)
            print(f"  ✅ Event processor works: {event}")
        
        return True
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Phase 1-2 Component Verification Tests")
    print("=" * 60)
    
    results = {
        "MenuNode": test_menu_node(),
        "MenuBuilder": test_menu_builder(),
        "MenuEventProcessor": test_menu_event_processor(),
        "MenuDataService": test_menu_data_service(),
        "Integration": test_integration(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print("=" * 60)
    print(f"Overall: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 1-2 is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
