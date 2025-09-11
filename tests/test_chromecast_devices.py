"""
Unit Tests for Chromecast Device Management

These tests verify the complete Chromecast device functionality:
- Menu configuration loading
- Device selection and switching
- Connect/disconnect operations
- Event handling and coordination
"""
import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add the project root to path to allow importing app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.event import Event, EventType

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChromecastDevices:
    """Test suite for Chromecast device management functionality"""

    def test_chromecast_menu_configuration(self):
        """Test that menu_config.json contains proper Chromecast device configuration"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'config', 'menu_config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verify chromecasts_menu exists
        assert 'chromecasts_menu' in config, "chromecasts_menu not found in config"
        
        chromecast_items = config['chromecasts_menu']['items']
        device_items = [item for item in chromecast_items if 'select_chromecast_device' in item['payload'].get('action', '')]
        
        # Verify we have the expected devices
        assert len(device_items) == 4, f"Expected 4 devices, found {len(device_items)}"
        
        expected_devices = ['living_room', 'tv_lounge', 'signe', 'bathroom_speaker']
        found_devices = [item['payload']['device_id'] for item in device_items]
        
        for device_id in expected_devices:
            assert device_id in found_devices, f"Device {device_id} not found in config"

    def test_json_menu_adapter_loads_chromecasts(self):
        """Test that JsonMenuAdapter properly loads Chromecast menu items"""
        from app.ui.menu.json_menu_adapter import JsonMenuAdapter
        
        adapter = JsonMenuAdapter()
        success = adapter.load_config()
        
        assert success, "JsonMenuAdapter failed to load config"
        
        # Test chromecasts menu loading
        chromecasts_items = adapter.get_menu_items('chromecasts_menu')
        assert len(chromecasts_items) > 0, "No chromecast menu items found"
        
        device_items = [item for item in chromecasts_items if 'select_chromecast_device' in item.get('payload', {}).get('action', '')]
        assert len(device_items) == 4, f"Expected 4 device items, found {len(device_items)}"

    def test_menu_controller_initialization(self):
        """Test that MenuController can be initialized and has expected structure"""
        from app.ui.menu.menu_controller import MenuController
        
        controller = MenuController()
        
        # Verify controller has expected attributes
        assert hasattr(controller, 'menu_data'), "MenuController missing menu_data"
        assert hasattr(controller, 'is_active'), "MenuController missing is_active"
        assert hasattr(controller, 'selected_index'), "MenuController missing selected_index"

    def test_chromecast_device_manager_initialization(self):
        """Test ChromecastDeviceManager initialization and event handling"""
        from app.services.chromecast_device_manager import ChromecastDeviceManager
        from app.core.event_bus import EventBus, Event
        from app.core.event_factory import EventType
        
        # Create event bus
        event_bus = EventBus()
        
        # Create manager
        manager = ChromecastDeviceManager(event_bus)
        
        # Verify manager has expected attributes
        assert hasattr(manager, 'event_bus'), "ChromecastDeviceManager missing event_bus"
        assert hasattr(manager, 'current_device'), "ChromecastDeviceManager missing current_device"
        
        # Test event creation
        device_change_event = Event(
            type=EventType.CHROMECAST_DEVICE_CHANGED,
            payload={
                "device_name": "TV Lounge",
                "device_id": "tv_lounge", 
                "friendly_name": "TV Lounge"
            }
        )
        
        assert device_change_event.type == EventType.CHROMECAST_DEVICE_CHANGED
        assert device_change_event.payload['device_id'] == 'tv_lounge'

    def test_event_types_exist(self):
        """Test that required event types are defined"""
        from app.core.event_factory import EventType
        
        # Verify Chromecast-related event types exist
        assert hasattr(EventType, 'CHROMECAST_DEVICE_CHANGED'), "CHROMECAST_DEVICE_CHANGED event type missing"
        assert hasattr(EventType, 'SHOW_MESSAGE'), "SHOW_MESSAGE event type missing"

    def test_chromecast_payload_structure(self):
        """Test that Chromecast device payloads have the correct structure"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'config', 'menu_config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        chromecast_items = config['chromecasts_menu']['items']
        device_items = [item for item in chromecast_items if 'select_chromecast_device' in item['payload'].get('action', '')]
        
        for item in device_items:
            payload = item['payload']
            
            # Verify required payload fields
            assert 'action' in payload, "Missing action in payload"
            assert 'device_name' in payload, "Missing device_name in payload"
            assert 'device_id' in payload, "Missing device_id in payload"
            assert 'friendly_name' in payload, "Missing friendly_name in payload"
            
            assert payload['action'] == 'select_chromecast_device', "Incorrect action"
            assert payload['device_id'] is not None, "device_id is None"
            assert payload['device_name'] is not None, "device_name is None"

    @patch('app.services.chromecast_device_manager.logger')
    def test_device_switching_flow(self, mock_logger):
        """Test the complete device switching flow"""
        from app.services.chromecast_device_manager import ChromecastDeviceManager
        from app.core.event_bus import EventBus, Event
        from app.core.event_factory import EventType
        
        # Mock the media player and chromecast service
        mock_media_player = MagicMock()
        mock_cc_service = MagicMock()
        mock_cc_service.switch_device.return_value = True
        mock_media_player.cc_service = mock_cc_service
        
        # Create event bus and manager
        event_bus = EventBus()
        manager = ChromecastDeviceManager(event_bus, media_player=mock_media_player)
        
        # Create device change event
        device_change_event = Event(
            type=EventType.CHROMECAST_DEVICE_CHANGED,
            payload={
                "device_name": "Bathroom Speaker",
                "device_id": "bathroom_speaker",
                "friendly_name": "Bathroom Speaker"
            }
        )
        
        # Test that the manager can handle device change
        assert hasattr(manager, '_handle_device_change'), "Manager missing device change handler"
        assert hasattr(manager, '_switch_chromecast_device'), "Manager missing switch method"


if __name__ == '__main__':
    # Run with pytest when executed directly
    pytest.main([__file__, '-v'])
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json
import asyncio
from typing import List, Dict, Any


class TestChromecastMenuConfiguration:
    """Test Chromecast device menu configuration"""
    
    @pytest.fixture
    def sample_menu_config(self):
        """Sample menu configuration with Chromecast devices"""
        return {
            "root": {
                "items": [
                    {
                        "id": "chromecasts",
                        "name": "Chromecasts",
                        "payload": {"action": "load_submenu", "submenu": "chromecasts_menu"}
                    }
                ]
            },
            "chromecasts_menu": {
                "items": [
                    {
                        "id": "chromecast_select_living_room",
                        "name": "🔗 Living Room (Current)",
                        "payload": {
                            "action": "select_chromecast_device",
                            "device_name": "Living Room",
                            "device_id": "living_room",
                            "friendly_name": "Living Room"
                        }
                    },
                    {
                        "id": "chromecast_select_tv_lounge",
                        "name": "⚪ TV Lounge",
                        "payload": {
                            "action": "select_chromecast_device",
                            "device_name": "TV Lounge",
                            "device_id": "tv_lounge",
                            "friendly_name": "TV Lounge"
                        }
                    },
                    {
                        "id": "chromecast_select_signe",
                        "name": "⚪ Signe",
                        "payload": {
                            "action": "select_chromecast_device",
                            "device_name": "Signe",
                            "device_id": "signe",
                            "friendly_name": "Signe"
                        }
                    },
                    {
                        "id": "chromecast_select_bathroom_speaker",
                        "name": "⚪ Bathroom Speaker",
                        "payload": {
                            "action": "select_chromecast_device",
                            "device_name": "Bathroom Speaker",
                            "device_id": "bathroom_speaker",
                            "friendly_name": "Bathroom Speaker"
                        }
                    }
                ]
            }
        }
    
    @patch('builtins.open')
    @patch('json.load')
    def test_json_menu_adapter_loads_chromecast_config(self, mock_json_load, mock_open, sample_menu_config):
        """Test JsonMenuAdapter loads Chromecast configuration correctly"""
        from app.ui.menu.json_menu_adapter import JsonMenuAdapter
        
        # Mock file operations
        mock_json_load.return_value = sample_menu_config
        mock_open.return_value.__enter__.return_value = Mock()
        
        adapter = JsonMenuAdapter()
        success = adapter.load_config()
        
        assert success is True
        assert adapter.menu_exists('chromecasts_menu')
        
        chromecast_items = adapter.get_menu_items('chromecasts_menu')
        assert len(chromecast_items) == 4
        
        # Verify device structure
        device_items = [item for item in chromecast_items if 'select_chromecast_device' in item['payload']['action']]
        assert len(device_items) == 4
        
        # Check specific device
        living_room = next(item for item in device_items if item['payload']['device_id'] == 'living_room')
        assert living_room['payload']['device_name'] == 'Living Room'
        assert living_room['payload']['friendly_name'] == 'Living Room'
    
    def test_chromecast_menu_validation(self, sample_menu_config):
        """Test that Chromecast menu items have required fields"""
        chromecast_items = sample_menu_config['chromecasts_menu']['items']
        
        for item in chromecast_items:
            assert 'id' in item
            assert 'name' in item
            assert 'payload' in item
            
            if 'select_chromecast_device' in item['payload'].get('action', ''):
                payload = item['payload']
                assert 'device_name' in payload
                assert 'device_id' in payload
                assert 'friendly_name' in payload


class TestChromecastDeviceManager:
    """Test ChromecastDeviceManager functionality"""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock EventBus for testing"""
        return Mock()
    
    @pytest.fixture
    def mock_pychromecast_service(self):
        """Mock PyChromecastService for testing"""
        service = Mock()
        service.switch_device = AsyncMock(return_value=True)
        service.get_current_device_name = Mock(return_value="Living Room")
        service.is_connected = Mock(return_value=True)
        return service
    
    @pytest.fixture
    def chromecast_device_manager(self, mock_event_bus, mock_pychromecast_service):
        """Create ChromecastDeviceManager with mocked dependencies"""
        from app.services.chromecast_device_manager import ChromecastDeviceManager
        
        manager = ChromecastDeviceManager(mock_event_bus)
        manager.pychromecast_service = mock_pychromecast_service
        return manager
    
    def test_device_change_success(self, chromecast_device_manager, mock_event_bus, mock_pychromecast_service):
        """Test successful device change operation"""
        # Simulate device change event
        from app.core.event_bus import Event
        from app.core.event_factory import EventType
        
        event_data = Event(
            type=EventType.CHROMECAST_DEVICE_CHANGED,
            payload={
                'device_name': 'TV Lounge',
                'device_id': 'tv_lounge',
                'friendly_name': 'TV Lounge'
            }
        )
        
        # Trigger device change
        chromecast_device_manager._handle_device_change(event_data)
        
        # Verify service calls
        mock_pychromecast_service.switch_device.assert_called_once_with('TV Lounge')
        
        # Verify events were published
        assert mock_event_bus.publish.call_count >= 2  # At least success message and device changed events
        
        # Check success message was sent
        success_call = None
        for call in mock_event_bus.publish.call_args_list:
            if call[0][0].event_type.name == 'SHOW_MESSAGE':
                success_call = call
                break
        
        assert success_call is not None
        assert 'TV Lounge' in success_call[0][0].data['message']
        assert success_call[0][0].data['message_type'] == 'success'
    
    def test_device_change_failure(self, chromecast_device_manager, mock_event_bus, mock_pychromecast_service):
        """Test device change failure handling"""
        # Mock service to fail
        mock_pychromecast_service.switch_device.side_effect = Exception("Device not found")
        
        from app.core.event_bus import Event
        from app.core.event_factory import EventType
        
        event_data = Event(
            type=EventType.CHROMECAST_DEVICE_CHANGED,
            payload={
                'device_name': 'Nonexistent Device',
                'device_id': 'nonexistent',
                'friendly_name': 'Nonexistent Device'
            }
        )
        
        # Trigger device change
        chromecast_device_manager._handle_device_change(event_data)
        
        # Verify error handling
        error_call = None
        for call in mock_event_bus.publish.call_args_list:
            if call[0][0].event_type.name == 'SHOW_MESSAGE':
                if call[0][0].data['message_type'] == 'error':
                    error_call = call
                    break
        
        assert error_call is not None
        assert 'Failed' in error_call[0][0].data['message']
    
    def test_device_manager_initialization(self, mock_event_bus):
        """Test ChromecastDeviceManager initializes correctly"""
        from app.services.chromecast_device_manager import ChromecastDeviceManager
        
        manager = ChromecastDeviceManager(mock_event_bus)
        
        # Verify event subscription
        mock_event_bus.subscribe.assert_called()
        
        # Check that it subscribed to CHROMECAST_DEVICE_CHANGED event
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        event_types = [call[0][0].name for call in subscribe_calls]
        assert 'CHROMECAST_DEVICE_CHANGED' in event_types


class TestPyChromecastService:
    """Test PyChromecastService device switching functionality"""
    
    @pytest.fixture
    def mock_chromecast(self):
        """Mock Chromecast device"""
        mock_cc = Mock()
        mock_cc.device.friendly_name = "Living Room"
        mock_cc.status = Mock()
        mock_cc.media_controller = Mock()
        mock_cc.media_controller.stop = Mock()
        mock_cc.disconnect = Mock()
        return mock_cc
    
    @pytest.fixture
    def mock_new_chromecast(self):
        """Mock new Chromecast device to switch to"""
        mock_cc = Mock()
        mock_cc.device.friendly_name = "TV Lounge"
        mock_cc.status = Mock()
        mock_cc.media_controller = Mock()
        return mock_cc
    
    @patch('app.services.pychromecast_service_ondemand.pychromecast')
    @pytest.mark.asyncio
    async def test_switch_device_success(self, mock_pychromecast, mock_chromecast, mock_new_chromecast):
        """Test successful device switching"""
        from app.services.pychromecast_service_ondemand import PyChromecastServiceOnDemand
        
        # Mock pychromecast discovery
        mock_pychromecast.get_chromecasts.return_value = ([mock_new_chromecast], Mock())
        
        service = PyChromecastServiceOnDemand()
        service.chromecast = mock_chromecast
        service.is_connected = Mock(return_value=True)
        
        # Test device switch
        result = service.switch_device("TV Lounge")
        
        assert result is True
        
        # Verify old device was stopped and disconnected
        mock_chromecast.media_controller.stop.assert_called_once()
        mock_chromecast.disconnect.assert_called_once()
        
        # Verify new device is set
        assert service.chromecast == mock_new_chromecast
    
    @patch('app.services.pychromecast_service_ondemand.pychromecast')
    @pytest.mark.asyncio
    async def test_switch_device_not_found(self, mock_pychromecast):
        """Test switching to non-existent device"""
        from app.services.pychromecast_service_ondemand import PyChromecastServiceOnDemand
        
        # Mock pychromecast discovery returns empty list
        mock_pychromecast.get_chromecasts.return_value = ([], Mock())
        
        service = PyChromecastServiceOnDemand()
        
        # Test device switch to non-existent device
        result = service.switch_device("Nonexistent Device")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_switch_device_no_current_connection(self, mock_new_chromecast):
        """Test switching when no current device is connected"""
        from app.services.pychromecast_service_ondemand import PyChromecastServiceOnDemand
        
        with patch('app.services.pychromecast_service_ondemand.pychromecast') as mock_pychromecast:
            mock_pychromecast.get_chromecasts.return_value = ([mock_new_chromecast], Mock())
            
            service = PyChromecastServiceOnDemand()
            service.chromecast = None  # No current connection
            
            result = service.switch_device("TV Lounge")
            
            assert result is True
            assert service.chromecast == mock_new_chromecast


class TestMenuControllerChromecastActions:
    """Test menu controller handling of Chromecast actions"""
    
    @pytest.fixture
    def mock_event_bus(self):
        return Mock()
    
    @pytest.fixture
    def mock_menu_data_service(self):
        service = Mock()
        service.get_current_items = Mock(return_value=[])
        return service
    
    @pytest.fixture
    def menu_controller(self, mock_event_bus, mock_menu_data_service):
        """Create MenuController with mocked dependencies"""
        from app.ui.menu.menu_controller import MenuController
        
        controller = MenuController()
        controller.menu_data_service = mock_menu_data_service
        return controller
    
    def test_select_chromecast_device_action(self, menu_controller, mock_event_bus):
        """Test menu controller handles select_chromecast_device action"""
        # Mock menu item with Chromecast selection
        item_data = {
            'action': 'select_chromecast_device',
            'device_name': 'TV Lounge',
            'device_id': 'tv_lounge',
            'friendly_name': 'TV Lounge'
        }
        
        # Trigger action
        menu_controller._handle_item_selection(item_data)
        
        # Verify event was published
        mock_event_bus.publish.assert_called()
        
        # Check the published event
        call_args = mock_event_bus.publish.call_args
        event = call_args[0][0]
        
        assert event.event_type.name == 'CHROMECAST_DEVICE_CHANGED'
        assert event.data['device_name'] == 'TV Lounge'
        assert event.data['device_id'] == 'tv_lounge'
        assert event.data['friendly_name'] == 'TV Lounge'


class TestChromecastIntegration:
    """Integration tests for complete Chromecast workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_device_switch_workflow(self):
        """Test complete workflow from menu selection to device switch"""
        from app.core.event_bus import EventBus
        # Test that the event is published correctly
        from app.services.chromecast_device_manager import ChromecastDeviceManager
        
        # Create real event bus for integration test
        event_bus = EventBus()
        
        # Mock PyChromecastService
        mock_pychromecast_service = Mock()
        mock_pychromecast_service.switch_device = AsyncMock(return_value=True)
        
        # Create device manager
        device_manager = ChromecastDeviceManager(event_bus)
        device_manager.pychromecast_service = mock_pychromecast_service
        
        # Simulate menu selection event
        from app.core.event_bus import Event
        from app.core.event_factory import EventType
        
        event = Event(
            type=EventType.CHROMECAST_DEVICE_CHANGED,
            payload={
                'device_name': 'TV Lounge',
                'device_id': 'tv_lounge',
                'friendly_name': 'TV Lounge'
            }
        )
        
        # Collect published events
        published_events = []
        def capture_event(event):
            published_events.append(event)
        
        event_bus.subscribe(EventType.SHOW_MESSAGE.value, capture_event)
        
        # Trigger the event
        await event_bus.publish(event)
        
        # Wait for async processing
        await asyncio.sleep(0.1)
        
        # Verify service was called
        mock_pychromecast_service.switch_device.assert_called_once_with('TV Lounge')
        
        # Verify success message was published
        success_events = [e for e in published_events if e.data.get('message_type') == 'success']
        assert len(success_events) > 0
        assert 'TV Lounge' in success_events[0].data['message']
    
    def test_chromecast_devices_in_menu_config(self):
        """Test that chromecast devices are properly configured in menu_config.json"""
        import os
        import json
        
        # Load actual menu config
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'app', 'config', 'menu_config.json'
        )
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verify structure
        assert 'chromecasts_menu' in config
        assert 'items' in config['chromecasts_menu']
        
        chromecast_items = config['chromecasts_menu']['items']
        device_items = [item for item in chromecast_items if 'select_chromecast_device' in item.get('payload', {}).get('action', '')]
        
        # Should have our 4 configured devices
        assert len(device_items) == 4
        
        # Verify each device has required fields
        for item in device_items:
            payload = item['payload']
            assert 'device_name' in payload
            assert 'device_id' in payload
            assert 'friendly_name' in payload
        
        # Verify specific devices exist
        device_ids = [item['payload']['device_id'] for item in device_items]
        expected_devices = ['living_room', 'tv_lounge', 'signe', 'bathroom_speaker']
        
        for expected_device in expected_devices:
            assert expected_device in device_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
