
import os
import pytest
import logging
from app.services.playback_manager import PlaybackManager

logging.basicConfig(level=logging.DEBUG, format='%(message)s', force=True)
# These should be set to your actual OAuth credentials and token file


RFID = "2132126686"  # Known RFID in the database


@pytest.fixture(scope="module")
def playback_manager():
    # No cast_func for test
    return PlaybackManager()

def test_rfid_to_playlist_pipeline(playback_manager):
    # Configure logging to output to the screen
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Test the full pipeline: RFID -> DB -> YTMusic -> Pytube -> Playlist
    result = playback_manager.load_rfid(RFID)
    assert result is True, "PlaybackManager failed to load RFID pipeline"
    status = playback_manager.player.get_status()
    assert status['status'] == 'playing'
    current_track = status['current_track']
    assert current_track is not None
    assert 'stream_url' in current_track and current_track['stream_url']
    logging.info(f"Now playing: {current_track['title']} by {current_track['artist']}")

    # Output the full playlist through logging
    playlist = playback_manager.player.playlist if playback_manager.player else []
    logging.info("Playlist:")
    for idx, track in enumerate(playlist, 1):
        logging.info(f"{idx}. {track['title']} by {track['artist']} (video_id: {track['video_id']}) stream_url: {track['stream_url']}")
