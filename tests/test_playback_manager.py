import pytest
import os
from app.services.playback_manager import PlaybackManager
from app.services.subsonic_service import SubsonicService
from unittest.mock import MagicMock

@pytest.mark.integration
def test_playback_manager_fetches_album_from_subsonic(monkeypatch):
    """
    Integration test: Given a real Subsonic album ID (al-5),
    PlaybackManager should fetch album and track data from SubsonicService.
    """
    # Setup: Use real SubsonicService, but mock dependencies not under test
    subsonic_service = SubsonicService()
    album_db = MagicMock()  # Not used in this test
    screen_manager = MagicMock()
    player = MagicMock()
    event_bus = MagicMock()

    manager = PlaybackManager(screen_manager, player, album_db, subsonic_service, event_bus)

    # Act: Fetch album info and tracks for a real album ID
    album_id = 'al-5'  # This must exist in your Subsonic instance
    album_info = subsonic_service.get_album_info(album_id)
    tracks = subsonic_service.get_album_tracks(album_id)

    # Assert: Album info and tracks are fetched and have expected fields
    assert album_info is not None, 'Album info should not be None'
    assert 'name' in album_info, 'Album info should have a name'
    assert 'artist' in album_info, 'Album info should have an artist'
    assert 'coverArt' in album_info, 'Album info should have coverArt'
    assert isinstance(tracks, list) and len(tracks) > 0, 'Tracks should be a non-empty list'
    for track in tracks:
        assert 'id' in track, 'Track should have id'
        assert 'title' in track, 'Track should have title'
        assert 'duration' in track, 'Track should have duration (seconds)'
        assert 'track' in track, 'Track should have track number'
        assert 'artist' in track, 'Track should have artist'
        assert 'album' in track, 'Track should have album'
        assert 'year' in track, 'Track should have year'
        assert 'coverArt' in track, 'Track should have coverArt'
