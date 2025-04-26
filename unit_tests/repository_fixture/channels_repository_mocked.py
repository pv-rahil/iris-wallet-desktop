""""
Mocked function for channel repository.
"""
from __future__ import annotations

import pytest
# Mock for close_channel method


@pytest.fixture
def mock_close_channel(mocker):
    """Mocked close_channel function."""
    def _mock_close_channel(value):
        return mocker.patch(
            'src.data.repository.channels_repository.ChannelRepository.close_channel',
            return_value=value,
        )
    return _mock_close_channel

# Mock for open_channel method


@pytest.fixture
def mock_open_channel(mocker):
    """Mocked open_channel function."""
    def _mock_open_channel(value):
        return mocker.patch(
            'src.data.repository.channels_repository.ChannelRepository.open_channel',
            return_value=value,
        )
    return _mock_open_channel

# Mock for list_channel method


@pytest.fixture
def mock_list_channel(mocker):
    """Mocked list_channel function."""
    def _mock_list_channel(value):
        return mocker.patch(
            'src.data.repository.channels_repository.ChannelRepository.list_channel',
            return_value=value,
        )
    return _mock_list_channel
