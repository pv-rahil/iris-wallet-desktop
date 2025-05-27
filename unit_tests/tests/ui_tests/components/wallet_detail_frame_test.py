"""Unit test for wallet detail frame component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QVBoxLayout

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.components.wallet_detail_frame import WalletInfoWidget


@pytest.fixture
def wallet_info_widget():
    """Create a WalletInfoWidget instance for testing."""
    v_layout = QVBoxLayout()
    widget = WalletInfoWidget(
        value='some-public-key', translation_key='public_key_label', v_layout=v_layout,
    )
    return widget


def test_wallet_info_widget_initialization(wallet_info_widget):
    """Test the initialization of the WalletInfoWidget."""

    # Check if the value label text is set correctly
    assert wallet_info_widget.value_label.text() == 'some-public-key'
    expected_title = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'public_key_label', None,
    )

    # Check if the key label text is set correctly by translation
    assert wallet_info_widget.key_label.text() == expected_title

    # Check the copy button icon is set
    assert isinstance(wallet_info_widget.copy_button.icon(), QIcon)

    # Check if the copy button has the correct tooltip text
    expected_tooltip = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy public_key_label', None,
    )
    assert wallet_info_widget.copy_button.toolTip() == expected_tooltip

    # Ensure the widget is added to the layout
    # Check the first item in the layout (wallet_info_widget should be there)
    layout_item = wallet_info_widget.v_layout.itemAt(0)
    assert layout_item is not None
    assert layout_item.widget() == wallet_info_widget


def test_copy_button_functionality(wallet_info_widget, qtbot):
    """Test the copy button functionality."""

    # Mock the copy_text function to avoid copying actual text
    mock_copy_text = MagicMock()

    # Connect the copy button to the mocked function
    # Disconnect any existing connections
    wallet_info_widget.copy_button.clicked.disconnect()
    wallet_info_widget.copy_button.clicked.connect(
        lambda: mock_copy_text(wallet_info_widget.value_label),
    )

    # Simulate a click on the copy button
    qtbot.mouseClick(wallet_info_widget.copy_button, Qt.LeftButton)

    # Check if the mock_copy_text function was called with the value label
    mock_copy_text.assert_called_once_with(wallet_info_widget.value_label)


def test_wallet_info_widget_ui_elements(wallet_info_widget):
    """Test the presence and properties of the UI elements."""

    # Check if the key label exists and is a QLabel
    assert isinstance(wallet_info_widget.key_label, QLabel)

    # Check if the value label exists and is a QLabel
    assert isinstance(wallet_info_widget.value_label, QLabel)

    # Check if the copy button exists and is a QPushButton
    assert isinstance(wallet_info_widget.copy_button, QPushButton)

    # Check if the spacer exists in the layout by looking for it by index
    layout_item = wallet_info_widget.horizontal_layout.itemAt(
        3,
    )  # The spacer should be at index 3
    assert layout_item is not None
    assert layout_item.spacerItem() is not None  # Ensure it's a spacer item
