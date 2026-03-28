# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""Unit tests for `src/utils/hardware_client_store.py`."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.utils.hardware_client_store import hardware_client_store
from src.utils.hardware_client_store import HardwareClientStore


@pytest.fixture
def store() -> HardwareClientStore:
    """Return a fresh `HardwareClientStore` instance for testing."""
    return HardwareClientStore()


def test_initial_state(store: HardwareClientStore):
    """New store should start with no client set."""
    assert store.client is None


def test_set_and_clear_client(store: HardwareClientStore):
    """Setting a client stores it; clearing removes it."""
    fake_client = object()
    store.set_client(fake_client)
    assert store.client is fake_client

    store.clear_client()
    assert store.client is None


def test_stop_client_closes_and_clears():
    """stop_client() should call stop() on the client and clear it."""
    mock_client = MagicMock()
    hardware_client_store.set_client(mock_client)

    hardware_client_store.stop_client()

    mock_client.stop.assert_called_once()
    assert hardware_client_store.client is None


def test_rgb_mode_controls(store: HardwareClientStore):
    """Test setting, getting, and clearing RGB mode."""
    # Default is False
    assert store.get_rgb_mode() is False

    # Set to True
    store.set_rgb_mode(True)
    assert store.get_rgb_mode() is True

    # Set to False
    store.set_rgb_mode(False)
    assert store.get_rgb_mode() is False

    # Clear back to None (which defaults to False in get_rgb_mode)
    store.clear_rgb_mode()
    assert store._is_rgb_mode is None
    assert store.get_rgb_mode() is False
