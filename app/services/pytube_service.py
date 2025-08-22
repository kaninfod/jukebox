

import logging
import requests
from pytubefix import YouTube


class PytubeService:
    def __init__(self):
        logging.info("PytubeService initialized.")

    def get_stream_url(self, video_id: str) -> str:
        try:
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            streams = yt.streams.filter(only_audio=True)
            if len(streams) > 0:
                stream_url = streams.order_by('abr').last().url
            else:
                stream_url = yt.streams.order_by('abr').last().url
            return stream_url
        except Exception as e:
            logging.error(f"Failed to get stream URL for video_id {video_id}: {e}")
            raise

    def is_stream_url_valid(self, stream_url: str) -> bool:
        logging.debug(f"[DEBUG] Checking stream_url: {stream_url}")
        try:
            resp = requests.get(stream_url, stream=True, timeout=10)
            logging.debug(f"[DEBUG] HTTP status: {resp.status_code}")
            logging.debug(f"[DEBUG] Content-Type: {resp.headers.get('Content-Type')}")
            logging.debug(f"[DEBUG] Content-Length: {resp.headers.get('Content-Length')}")
            if resp.status_code != 200:
                logging.debug(f"[DEBUG] Stream URL is not valid (status {resp.status_code}).")
                return False
            return True
        except Exception as e:
            logging.debug(f"[DEBUG] Error requesting stream_url: {e}")
            return False



