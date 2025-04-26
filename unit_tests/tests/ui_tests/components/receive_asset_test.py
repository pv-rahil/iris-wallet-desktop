"""Unit test for Receive asset component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.viewmodels.main_view_model import MainViewModel
from src.views.components.receive_asset import ReceiveAssetWidget


@pytest.fixture
def receive_asset_widget(qtbot):
    """Fixture to create and return an instance of ReceiveAssetWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = ReceiveAssetWidget(
        view_model, page_name='mock_page_name', address_info='mock_address_info',
    )
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(receive_asset_widget: ReceiveAssetWidget):
    """Test the retranslation of UI elements in ReceiveAssetWidget."""
    receive_asset_widget.retranslate_ui()

    assert receive_asset_widget.address_label.text() == 'address'
    assert receive_asset_widget.asset_title.text() == 'receive'


def test_update_qr_and_address(receive_asset_widget: ReceiveAssetWidget):
    """Test the update qr and address of UI ReceiveAssetWidget."""
    mock_address = 'mock_address'
    receive_asset_widget.update_qr_and_address(mock_address)

    assert receive_asset_widget.receiver_address.text() == mock_address
