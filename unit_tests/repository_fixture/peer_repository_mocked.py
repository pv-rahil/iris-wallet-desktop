""""
Mocked function for reer repository.
"""
from __future__ import annotations

import pytest

# Mock for connect_peer method


@pytest.fixture
def mock_connect_peer(mocker):
    """Mocked connect_peer function."""
    def _mock_connect_peer(value):
        return mocker.patch(
            'src.data.repository.peer_repository.PeerRepository.connect_peer',
            return_value=value,
        )
    return _mock_connect_peer

# Mock for disconnect_peer method


@pytest.fixture
def mock_disconnect_peer(mocker):
    """Mocked disconnect_peer function."""
    def _mock_disconnect_peer(value):
        return mocker.patch(
            'src.data.repository.peer_repository.PeerRepository.disconnect_peer',
            return_value=value,
        )
    return _mock_disconnect_peer

# Mock for list_peer method


@pytest.fixture
def mock_list_peer(mocker):
    """Mocked list_peer function."""
    def _mock_list_peer(value):
        return mocker.patch(
            'src.data.repository.peer_repository.PeerRepository.list_peer',
            return_value=value,
        )
    return _mock_list_peer
