"""
DynamicLoader: Fetches runtime content from Subsonic API and creates MenuNode instances.

This class is responsible for:
1. Loading artists from Subsonic API filtered by alphabetical range
2. Loading albums for a specific artist
3. Creating MenuNode instances from the fetched data
4. Injecting dynamic content into the menu tree

Architecture:
- MenuBuilder: Loads static structure from JSON
- DynamicLoader: Loads dynamic content from API
- Both create MenuNode instances that are injected into the tree
"""

import logging
from typing import List, Optional, Dict, Any

from .menu_node import MenuNode
from app.services.subsonic_service import SubsonicService

logger = logging.getLogger(__name__)


class DynamicLoader:
    """Loads dynamic content from Subsonic API and creates MenuNode instances."""

    def __init__(self, subsonic_service: SubsonicService):
        """
        Initialize the DynamicLoader.

        Args:
            subsonic_service: Instance of SubsonicService for API calls.

        Raises:
            ValueError: If subsonic_service is None.
        """
        if not subsonic_service:
            raise ValueError("subsonic_service cannot be None")
        
        self.subsonic_service = subsonic_service
        self._artist_cache: Dict[str, List[MenuNode]] = {}  # Cache artists by range
        self._album_cache: Dict[str, List[MenuNode]] = {}   # Cache albums by artist_id
        
        logger.info("DynamicLoader initialized")

    def load_artists_in_range(
        self, 
        start_letter: str, 
        end_letter: str,
        use_cache: bool = True
    ) -> List[MenuNode]:
        """
        Load artists from Subsonic API filtered by alphabetical range.

        Args:
            start_letter: Starting letter (e.g., 'A')
            end_letter: Ending letter (e.g., 'D')
            use_cache: Whether to use cached results if available

        Returns:
            List of MenuNode instances representing artists in the range.

        Raises:
            Exception: If API call fails.
        """
        cache_key = f"{start_letter}_{end_letter}"
        
        # Check cache first
        if use_cache and cache_key in self._artist_cache:
            logger.debug(f"Using cached artists for range {start_letter}-{end_letter}")
            return self._artist_cache[cache_key]
        
        try:
            logger.info(f"Loading artists from Subsonic API for range {start_letter}-{end_letter}")
            
            # Call Subsonic service
            artists_data = self.subsonic_service.get_artists_in_range(start_letter, end_letter)
            
            # Convert to MenuNode instances
            nodes = []
            for artist in artists_data:
                artist_id = artist.get("id")
                artist_name = artist.get("name", "Unknown Artist")
                
                # Create a node for this artist
                node = MenuNode(
                    id=artist_id,
                    name=artist_name,
                    parent=None,  # Parent will be set when added to tree
                    payload={
                        "action": "load_dynamic",
                        "dynamic_type": "artist_albums",
                        "artist_id": artist_id,
                        "artist_name": artist_name
                    }
                )
                nodes.append(node)
            
            logger.info(f"Loaded {len(nodes)} artists for range {start_letter}-{end_letter}")
            
            # Cache the result
            self._artist_cache[cache_key] = nodes
            
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to load artists for range {start_letter}-{end_letter}: {e}")
            return []

    def load_artist_albums(
        self,
        artist_id: str,
        artist_name: str = "Unknown Artist",
        use_cache: bool = True
    ) -> List[MenuNode]:
        """
        Load all albums for a specific artist.

        Args:
            artist_id: The Subsonic artist ID
            artist_name: Display name of the artist (for logging)
            use_cache: Whether to use cached results if available

        Returns:
            List of MenuNode instances representing albums by the artist.

        Raises:
            Exception: If API call fails.
        """
        # Check cache first
        if use_cache and artist_id in self._album_cache:
            logger.debug(f"Using cached albums for artist {artist_id}")
            return self._album_cache[artist_id]
        
        try:
            logger.info(f"Loading albums from Subsonic API for artist {artist_name} (id: {artist_id})")
            
            # Call Subsonic service
            albums_data = self.subsonic_service.list_albums_for_artist(artist_id)
            
            # Convert to MenuNode instances
            nodes = []
            for album in albums_data:
                album_id = album.get("id")
                album_name = album.get("name", "Unknown Album")
                year = album.get("year", "")
                cover_url = album.get("cover_url", "")
                
                # Build display name with year if available
                display_name = album_name
                if year:
                    display_name = f"{album_name} ({year})"
                
                # Create a node for this album
                node = MenuNode(
                    id=album_id,
                    name=display_name,
                    parent=None,  # Parent will be set when added to tree
                    payload={
                        "action": "select_album",
                        "album_id": album_id,
                        "album_name": album_name,
                        "artist_id": artist_id,
                        "artist_name": artist_name,
                        "cover_url": cover_url
                    }
                )
                nodes.append(node)
            
            logger.info(f"Loaded {len(nodes)} albums for artist {artist_name}")
            
            # Cache the result
            self._album_cache[artist_id] = nodes
            
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to load albums for artist {artist_id}: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._artist_cache.clear()
        self._album_cache.clear()
        logger.info("DynamicLoader cache cleared")

    def clear_artist_cache(self, start_letter: str = None, end_letter: str = None) -> None:
        """
        Clear cached artist data.

        Args:
            start_letter: If provided, only clear cache for this range
            end_letter: If provided with start_letter, only clear cache for this range
        """
        if start_letter and end_letter:
            cache_key = f"{start_letter}_{end_letter}"
            if cache_key in self._artist_cache:
                del self._artist_cache[cache_key]
                logger.info(f"Cleared artist cache for range {start_letter}-{end_letter}")
        else:
            self._artist_cache.clear()
            logger.info("Cleared all artist cache")

    def clear_album_cache(self, artist_id: str = None) -> None:
        """
        Clear cached album data.

        Args:
            artist_id: If provided, only clear cache for this artist
        """
        if artist_id:
            if artist_id in self._album_cache:
                del self._album_cache[artist_id]
                logger.info(f"Cleared album cache for artist {artist_id}")
        else:
            self._album_cache.clear()
            logger.info("Cleared all album cache")


# Global instance
_dynamic_loader_instance: Optional[DynamicLoader] = None


def get_dynamic_loader() -> Optional[DynamicLoader]:
    """
    Get the global DynamicLoader instance.

    Returns:
        The DynamicLoader instance if initialized, None otherwise.
    """
    global _dynamic_loader_instance
    return _dynamic_loader_instance


def initialize_dynamic_loader(subsonic_service: SubsonicService) -> DynamicLoader:
    """
    Initialize the global DynamicLoader instance.

    Call this once at application startup after Subsonic service is available.

    Args:
        subsonic_service: Instance of SubsonicService for API calls.

    Returns:
        The initialized DynamicLoader instance.

    Raises:
        ValueError: If subsonic_service is None.
    """
    global _dynamic_loader_instance
    _dynamic_loader_instance = DynamicLoader(subsonic_service)
    return _dynamic_loader_instance
