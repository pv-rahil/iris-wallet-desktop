"""Module containing ChannelRepository."""
from __future__ import annotations

from src.model.channels_model import ChannelsListResponseModel
from src.model.channels_model import CloseChannelRequestModel
from src.model.channels_model import CloseChannelResponseModel
from src.model.channels_model import OpenChannelResponseModel
from src.model.channels_model import OpenChannelsRequestModel
from src.utils.cache import Cache
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.unlock_required import unlock_required
from src.utils.endpoints import CLOSE_CHANNEL_ENDPOINT
from src.utils.endpoints import LIST_CHANNELS_ENDPOINT
from src.utils.endpoints import OPEN_CHANNEL_ENDPOINT
from src.utils.request import Request


class ChannelRepository:
    """Repository for handling channel operations."""

    @staticmethod
    @unlock_required
    def close_channel(channel: CloseChannelRequestModel) -> CloseChannelResponseModel:
        """Close a channel."""
        payload = channel.dict()
        with repository_custom_context():
            response = Request.post(CLOSE_CHANNEL_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return CloseChannelResponseModel(status=True)

    @staticmethod
    @unlock_required
    def open_channel(channel: OpenChannelsRequestModel) -> OpenChannelResponseModel:
        """Open a channel."""
        payload = channel.dict()
        with repository_custom_context():
            response = Request.post(OPEN_CHANNEL_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return OpenChannelResponseModel(**data)

    @staticmethod
    @unlock_required
    def list_channel() -> ChannelsListResponseModel:
        """List channels."""
        with repository_custom_context():
            response = Request.get(LIST_CHANNELS_ENDPOINT)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return ChannelsListResponseModel(**data)
