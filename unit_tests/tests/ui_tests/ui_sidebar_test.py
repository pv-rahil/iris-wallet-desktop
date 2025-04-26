"""Unit test for Sidebar."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_sidebar import Sidebar


@pytest.fixture
def sidebar_widget(qtbot):
    """Fixture to create and return an instance of Sidebar."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = Sidebar(view_model)
    qtbot.addWidget(widget)
    return widget


def test_get_checked_button_translation_key(sidebar_widget: Sidebar, mocker):
    """Test the get_checked_button_translation_key method."""

    # List of buttons that should be checked
    buttons = [
        sidebar_widget.backup,
        sidebar_widget.help,
        sidebar_widget.view_unspent_list,
        sidebar_widget.faucet,
        sidebar_widget.channel_management,
        sidebar_widget.my_fungibles,
        sidebar_widget.my_collectibles,
        sidebar_widget.settings,
        sidebar_widget.about,
    ]

    # Mock the isChecked and get_translation_key methods for each button
    for button in buttons:
        button.isChecked = mocker.Mock(return_value=False)
        button.get_translation_key = mocker.Mock(
            return_value=f"{button.objectName()}_key",
        )

    # Test when no button is checked
    assert sidebar_widget.get_checked_button_translation_key() is None

    # Test each button being checked individually
    for button in buttons:
        button.isChecked.return_value = True
        assert sidebar_widget.get_checked_button_translation_key() == f"{
            button.objectName()
        }_key"
        button.isChecked.return_value = False  # Reset after the check

    # Test when multiple buttons are checked (should return the first checked one)
    buttons[0].isChecked.return_value = True
    buttons[1].isChecked.return_value = True
    assert sidebar_widget.get_checked_button_translation_key() == f"{
        buttons[0].objectName()
    }_key"


def test_retranslate_ui(sidebar_widget: Sidebar, mocker):
    """Test the retranslation of UI elements based on network."""

    # Mock the QCoreApplication.translate function to simulate translation behavior
    mock_translate = mocker.patch.object(
        QCoreApplication, 'translate', return_value='translated_text',
    )

    # Create mock widgets for iris_wallet_text and receive_asset_button
    mock_iris_wallet_text = MagicMock()
    mock_receive_asset_button = MagicMock()
    sidebar_widget.iris_wallet_text = mock_iris_wallet_text
    sidebar_widget.receive_asset_button = mock_receive_asset_button

    # Test case 1: Network is MAINNET
    mocker.patch.object(
        SettingRepository, 'get_wallet_network',
        return_value=MagicMock(value=NetworkEnumModel.MAINNET.value),
    )

    # Call retranslate_ui for MAINNET
    sidebar_widget.retranslate_ui()

    # Test if the translate method is called with correct parameters
    mock_translate.assert_any_call(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'iris_wallet', None,
    )
    mock_translate.assert_any_call(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'receive_assets', None,
    )

    # Ensure that MAINNET results in just the translated text (without appending network)
    mock_iris_wallet_text.setText.assert_called_once_with('translated_text')

    # Reset the mocks before testing the next case
    mock_iris_wallet_text.reset_mock()
    mock_receive_asset_button.reset_mock()

    # Test case 2: Network is NOT MAINNET
    mock_network = 'test_network'
    mocker.patch.object(
        SettingRepository, 'get_wallet_network',
        return_value=MagicMock(value=mock_network),
    )

    # Call retranslate_ui for a non-MAINNET network
    sidebar_widget.retranslate_ui()

    # Ensure that QCoreApplication.translate is called again for 'iris_wallet' and 'receive_assets'
    mock_translate.assert_any_call(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'iris_wallet', None,
    )
    mock_translate.assert_any_call(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'receive_assets', None,
    )

    # Ensure that the text is now "translated_text {network}", where network is capitalized
    mock_iris_wallet_text.setText.assert_called_once_with(
        f"translated_text {mock_network.capitalize()}",
    )

    # Ensure that the receive_asset_button text is also set correctly
    mock_receive_asset_button.setText.assert_called_once_with(
        'translated_text',
    )
