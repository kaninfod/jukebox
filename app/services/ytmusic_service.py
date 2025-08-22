import logging

from ytmusicapi import YTMusic, OAuthCredentials
from typing import List, Dict, Any
from app.config import config


class YTMusicService:
    def __init__(self):
        client_id = config.YTMUSIC_CLIENT_ID
        client_secret = config.YTMUSIC_CLIENT_SECRET
        oauth_file = 'oauth.json'
        self.ytmusic = YTMusic(oauth_file, oauth_credentials=OAuthCredentials(client_id=client_id, client_secret=client_secret))
        logging.info("YTMusicService initialized.")

    def search_song(self, query: str) -> Dict[str, Any]:
        results = self.ytmusic.search(query, filter="songs")
        if not results:
            raise Exception("No songs found.")
        return results[0]

    def get_album_tracks(self, yt_id: str) -> List[Dict[str, Any]]:
        browse_id = self.ytmusic.get_album_browse_id(yt_id)
        album_info = self.ytmusic.get_album(browse_id)
        tracks = album_info.get('tracks', [])
        return tracks

    def get_album_info(self, yt_id: str) -> Dict[str, Any]:
        browse_id = self.ytmusic.get_album_browse_id(yt_id)
        return self.ytmusic.get_album(browse_id)
