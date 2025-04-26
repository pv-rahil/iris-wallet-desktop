"""Unit test for wallet logo frame component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import patch

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLabel

from src.model.enums.enums_model import NetworkEnumModel
from src.views.components.wallet_logo_frame import WalletLogoFrame


@pytest.fixture
def wallet_logo_frame():
    """Create and return a WalletLogoFrame instance."""
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.MAINNET.value):
        widget = WalletLogoFrame()
        yield widget
        widget.deleteLater()


def test_wallet_logo_frame_initialization(wallet_logo_frame):
    """Test the initialization of WalletLogoFrame."""

    # Ensure the WalletLogoFrame has the correct object name
    assert wallet_logo_frame.objectName() == 'wallet_logo_frame'

    # Check if the logo label is created
    assert isinstance(wallet_logo_frame.logo_label, QLabel)
    assert wallet_logo_frame.logo_label.pixmap() is not None

    # Check if the logo text label is created
    assert isinstance(wallet_logo_frame.logo_text, QLabel)
    assert wallet_logo_frame.logo_text.text() != ''

    # Ensure that the logo label has the correct size
    assert wallet_logo_frame.logo_label.minimumSize() == QSize(64, 0)
    assert wallet_logo_frame.logo_label.maximumSize() == QSize(64, 64)

    # Check the network text in the logo text
    if wallet_logo_frame.network == NetworkEnumModel.MAINNET.value:
        # Expect no extra text for MAINNET
        assert wallet_logo_frame.logo_text.text() == 'iris_wallet'
    else:
        network_text = f" {wallet_logo_frame.network.capitalize()}"
        assert network_text in wallet_logo_frame.logo_text.text()

    # Verify the layout and components
    assert wallet_logo_frame.grid_layout is not None
    assert wallet_logo_frame.horizontal_layout is not None
    # Should contain the logo and the text label
    assert wallet_logo_frame.horizontal_layout.count() == 2
    assert wallet_logo_frame.horizontal_layout.itemAt(
        0,
    ).widget() == wallet_logo_frame.logo_label
    assert wallet_logo_frame.horizontal_layout.itemAt(
        1,
    ).widget() == wallet_logo_frame.logo_text


def test_wallet_logo_frame_network_change(wallet_logo_frame):
    """Test the WalletLogoFrame when network is changed."""

    # Mock a different network for the test
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET.value):
        wallet_logo_frame.set_logo()

    # Check if the network text changes to 'testnet'
    network_text = f" {NetworkEnumModel.TESTNET.value.capitalize()}"
    assert network_text in wallet_logo_frame.logo_text.text()
