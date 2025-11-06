"""
MenuEventProcessor: Extracts action data from MenuNodes and raises appropriate events.

This class is responsible for:
1. Taking a selected MenuNode
2. Extracting the action and parameters from its payload
3. Routing to the appropriate handler (or raising an event)
4. Providing a consistent interface for menu selection handling

The processor handles both:
- Static actions (defined in JSON payload)
- Dynamic content loading (e.g., "browse_artists_in_range" → load from API)
"""

from typing import Dict, Any, Optional, Callable
from enum import Enum

from .menu_node import MenuNode


class ActionType(Enum):
    """Types of actions that can be extracted from menu nodes."""
    
    # Navigation actions
    NAVIGATE = "navigate"  # Navigate to a submenu
    
    # Dynamic loading actions
    LOAD_DYNAMIC = "load_dynamic"  # Load dynamic content (e.g., artists from API)
    BROWSE_ARTISTS_IN_RANGE = "browse_artists_in_range"  # Load artists in alphabetical range
    BROWSE_ARTIST_ALBUMS = "browse_artist_albums"  # Load albums for an artist
    
    # Playback actions
    SELECT_DEVICE = "select_device"  # Select a Chromecast device
    SELECT_ALBUM = "select_album"  # Select an album to play
    PLAY = "play"  # Play selected item
    
    # System actions
    RESTART_APP = "restart_app"  # Restart the application
    REBOOT_SYSTEM = "reboot_system"  # Reboot the entire system
    SHUTDOWN_SYSTEM = "shutdown_system"  # Shutdown the entire system
    
    # Other
    UNKNOWN = "unknown"  # Unknown or unhandled action


class MenuEvent:
    """Represents a menu action event."""
    
    def __init__(
        self,
        action_type: ActionType,
        node: MenuNode,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a menu event.

        Args:
            action_type: The type of action.
            node: The MenuNode that was selected.
            parameters: Optional parameters for the action.
        """
        self.action_type = action_type
        self.node = node
        self.parameters = parameters or {}

    def __repr__(self) -> str:
        return (
            f"MenuEvent(action={self.action_type.value}, "
            f"node_id={self.node.id}, params={self.parameters})"
        )


class MenuEventProcessor:
    """Processes menu node selections and extracts action events."""

    def __init__(self):
        """Initialize the event processor."""
        self._handlers: Dict[ActionType, Callable] = {}

    def register_handler(self, action_type: ActionType, handler: Callable) -> None:
        """
        Register a handler for an action type.

        Args:
            action_type: The ActionType to handle.
            handler: Callable that takes MenuEvent and performs the action.
        """
        self._handlers[action_type] = handler

    def process_node_selection(self, node: MenuNode) -> Optional[MenuEvent]:
        """
        Process a selected menu node and extract the action.

        Args:
            node: The MenuNode that was selected.

        Returns:
            MenuEvent representing the action to take, or None if no action.
        """
        if not node:
            return None

        # Check if node has children (navigation)
        if node.children:
            # This is a submenu - event is just to navigate to it
            return MenuEvent(
                action_type=ActionType.NAVIGATE,
                node=node,
                parameters={}
            )

        # Check node's payload for explicit action
        if node.payload:
            action = node.payload.get("action")
            if action:
                # Create event with action type and parameters
                action_type = self._parse_action_type(action)
                parameters = {k: v for k, v in node.payload.items() if k != "action"}
                
                event = MenuEvent(
                    action_type=action_type,
                    node=node,
                    parameters=parameters
                )
                
                return event

        # No payload or children - treat as navigation to this node
        return MenuEvent(
            action_type=ActionType.NAVIGATE,
            node=node,
            parameters={}
        )

    def process_event(self, event: MenuEvent) -> Any:
        """
        Process a menu event by calling the registered handler.

        Args:
            event: The MenuEvent to process.

        Returns:
            The result from the handler, or None if no handler registered.
        """
        handler = self._handlers.get(event.action_type)
        if handler:
            return handler(event)
        
        # If no handler, just return the event
        return event

    def process_node_selection_and_handle(self, node: MenuNode) -> Any:
        """
        Process a node selection, create an event, and handle it.

        Convenience method that combines process_node_selection and process_event.

        Args:
            node: The MenuNode that was selected.

        Returns:
            The result from the event handler.
        """
        event = self.process_node_selection(node)
        if event:
            return self.process_event(event)
        return None

    @staticmethod
    def _parse_action_type(action_str: str) -> ActionType:
        """
        Parse an action string into ActionType.

        Args:
            action_str: The action string from node payload.

        Returns:
            The corresponding ActionType.
        """
        # Map action strings to ActionType enum values
        action_map = {
            "navigate": ActionType.NAVIGATE,
            "load_dynamic": ActionType.LOAD_DYNAMIC,
            "browse_artists_in_range": ActionType.BROWSE_ARTISTS_IN_RANGE,
            "browse_artist_albums": ActionType.BROWSE_ARTIST_ALBUMS,
            "select_device": ActionType.SELECT_DEVICE,
            "select_album": ActionType.SELECT_ALBUM,
            "play": ActionType.PLAY,
            "restart_app": ActionType.RESTART_APP,
            "reboot_system": ActionType.REBOOT_SYSTEM,
            "shutdown_system": ActionType.SHUTDOWN_SYSTEM
        }
        
        return action_map.get(action_str.lower(), ActionType.UNKNOWN)

    @staticmethod
    def extract_action_data(node: MenuNode) -> Dict[str, Any]:
        """
        Extract action and parameters from a node's payload.

        Args:
            node: The MenuNode to extract from.

        Returns:
            Dictionary with 'action' and other parameters.
        """
        if not node.payload:
            return {}
        
        # Payload is a dict with 'action' and parameters
        return dict(node.payload)

    @staticmethod
    def get_action_name(node: MenuNode) -> str:
        """
        Get the action name from a node.

        Args:
            node: The MenuNode.

        Returns:
            Action name string, or empty string if none.
        """
        if node.payload and "action" in node.payload:
            return node.payload["action"]
        return ""

    @staticmethod
    def get_action_parameters(node: MenuNode) -> Dict[str, Any]:
        """
        Get parameters for an action from a node.

        Args:
            node: The MenuNode.

        Returns:
            Dictionary of parameters (excludes 'action' key).
        """
        if not node.payload:
            return {}
        
        # Return payload minus the 'action' key
        return {k: v for k, v in node.payload.items() if k != "action"}


# Global instance
_event_processor_instance: Optional[MenuEventProcessor] = None


def get_menu_event_processor() -> MenuEventProcessor:
    """
    Get or create the global MenuEventProcessor instance.

    Returns:
        The singleton MenuEventProcessor instance.
    """
    global _event_processor_instance
    if _event_processor_instance is None:
        _event_processor_instance = MenuEventProcessor()
    return _event_processor_instance
