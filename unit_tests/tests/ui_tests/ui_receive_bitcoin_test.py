"""Unit test for Receive bitcoin ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_receive_bitcoin import ReceiveBitcoinWidget


@pytest.fixture
def receive_bitcoin_widget(qtbot):
    """Fixture to create and return an instance of ReceiveBitcoinWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = ReceiveBitcoinWidget(view_model)
    qtbot.addWidget(widget)
    return widget


def test_show_receive_bitcoin_loading(receive_bitcoin_widget: ReceiveBitcoinWidget, qtbot):
    """Test that the loading screen is shown and elements are hidden."""
    receive_bitcoin_widget.show_receive_bitcoin_loading()

    assert receive_bitcoin_widget.receive_bitcoin_page.label.isHidden()
    assert receive_bitcoin_widget.receive_bitcoin_page.receiver_address.isHidden()

    assert receive_bitcoin_widget._loading_translucent_screen is not None


def test_close_button_navigation(receive_bitcoin_widget: ReceiveBitcoinWidget, qtbot):
    """Test that the close button triggers navigation."""
    receive_bitcoin_widget._view_model.page_navigation.bitcoin_page = MagicMock()

    receive_bitcoin_widget.close_button_navigation()

    receive_bitcoin_widget._view_model.page_navigation.bitcoin_page.assert_called_once()


def test_update_address(receive_bitcoin_widget: ReceiveBitcoinWidget, qtbot):
    """Test that the address is updated correctly."""
    new_address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
    receive_bitcoin_widget.receive_bitcoin_page.update_qr_and_address = MagicMock()

    receive_bitcoin_widget.update_address(new_address)

    receive_bitcoin_widget.receive_bitcoin_page.update_qr_and_address.assert_called_once_with(
        new_address,
    )


def test_hide_bitcoin_loading_screen(receive_bitcoin_widget: ReceiveBitcoinWidget):
    """Test the hide_bitcoin_loading_screen method."""

    # Mock necessary attributes on the widget
    receive_bitcoin_widget.receive_bitcoin_page = MagicMock()
    receive_bitcoin_widget.render_timer = MagicMock()
    receive_bitcoin_widget._loading_translucent_screen = MagicMock()

    # Call the method with is_loading=False
    receive_bitcoin_widget.hide_bitcoin_loading_screen(is_loading=False)

    # Assert that the UI elements are shown
    receive_bitcoin_widget.receive_bitcoin_page.label.show.assert_called_once()
    receive_bitcoin_widget.receive_bitcoin_page.receiver_address.show.assert_called_once()
    receive_bitcoin_widget.receive_bitcoin_page.copy_button.show.assert_called_once()

    # Assert that the render timer is stopped
    receive_bitcoin_widget.render_timer.stop.assert_called_once()

    # Assert that the loading translucent screen is stopped
    receive_bitcoin_widget._loading_translucent_screen.stop.assert_called_once()
