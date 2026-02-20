from __future__ import annotations

import logging

from app.config import config
from app.services.chromecast_service import get_chromecast_service
from app.services.mpv_service import get_mpv_service


logger = logging.getLogger(__name__)


def get_playback_backend_by_name(backend_name: str, device_name: str | None = None):
    backend = (backend_name or "chromecast").strip().lower()

    if backend == "mpv":
        logger.info("Using MPV playback backend")
        return get_mpv_service()

    if backend != "chromecast":
        logger.warning("Unknown PLAYBACK_BACKEND '%s', falling back to chromecast", backend)

    logger.info("Using Chromecast playback backend")
    return get_chromecast_service(device_name or config.DEFAULT_CHROMECAST_DEVICE)


def get_playback_backend():
    return get_playback_backend_by_name(config.PLAYBACK_BACKEND)
