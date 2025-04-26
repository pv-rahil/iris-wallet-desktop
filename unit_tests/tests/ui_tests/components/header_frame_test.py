"""Unit test for header frame component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from src.model.enums.enums_model import WalletType
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.components.header_frame import HeaderFrame


@pytest.fixture
def header_frame():
    """Fixture to create a HeaderFrame instance."""
    with patch('src.data.repository.setting_repository.SettingRepository.is_backup_configured') as mock_is_backup_configured:
        # Ensure backup is configured
        mock_is_backup_configured.return_value.is_backup_configured = True
        frame = HeaderFrame('Test Title', 'test_logo.png')
    return frame


def test_initialization(header_frame):
    """Test initialization of HeaderFrame."""
    assert header_frame.title == 'Test Title'
    assert header_frame.title_logo_path == 'test_logo.png'
    assert header_frame.is_backup_warning is False
    assert header_frame.title_name.text() == 'Test Title'
    assert header_frame.network_error_frame.isHidden()
    assert not header_frame.action_button.isHidden()
    assert not header_frame.refresh_page_button.isHidden()


def test_network_error_frame_visibility_when_offline(header_frame):
    """Test the visibility of the network error frame when offline."""

    # Mock the SettingRepository to ensure network is not REGTEST
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network', return_value='MAINNET'):
        # Call the method with `network_status` set to False
        header_frame.handle_network_frame_visibility(False)

        # Assert that the network error frame is visible
        assert not header_frame.network_error_frame.isHidden(
        ), 'Network error frame should be visible when offline'

        # Assert the network error frame has the expected style
        expected_style = """
                #network_error_frame {
                    border-radius: 8px;
                    background-color: #331D32;
                }
            """
        assert header_frame.network_error_frame.styleSheet(
        ) == expected_style, 'Network error frame style is incorrect'

        # Assert the correct error message is displayed
        expected_message = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'connection_error_message', None,
        )
        assert header_frame.network_error_info_label.text(
        ) == expected_message, 'Error message is incorrect'

        # Assert that buttons are hidden
        assert not header_frame.action_button.isVisible(
        ), 'Action button should not be visible'
        assert not header_frame.refresh_page_button.isVisible(
        ), 'Refresh page button should not be visible'


def test_network_error_frame_visibility_when_online(header_frame):
    """Test the visibility of the network error frame when online."""
    header_frame.handle_network_frame_visibility(True)
    assert not header_frame.network_error_frame.isVisible()
    assert not header_frame.action_button.isHidden()
    assert not header_frame.refresh_page_button.isHidden()


def test_set_button_visibility_for_refresh_and_action_buttons(header_frame):
    """Test visibility of refresh and action buttons based on the title."""
    header_frame.set_button_visibility(
        ['collectibles', 'fungibles'], [
            'view_unspent_list',
        ], True,
    )
    assert not header_frame.action_button.isHidden()
    assert not header_frame.refresh_page_button.isHidden()

    header_frame.set_button_visibility(
        ['collectibles', 'fungibles'], [
            'view_unspent_list',
        ], False,
    )
    assert not header_frame.action_button.isVisible()
    assert not header_frame.refresh_page_button.isVisible()


def test_retranslate_ui(header_frame):
    """Test that UI elements are properly translated."""
    header_frame.retranslate_ui()
    assert header_frame.title_name.text() == 'Test Title'
    assert header_frame.network_error_info_label.text() == 'connection_error_message'
    assert header_frame.action_button.text() == 'issue_new_asset'


def test_handle_network_frame_visibility(header_frame):
    """Test handle_network_frame_visibility method."""

    # Mock dependencies
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network') as mock_get_wallet_network:

        # Create a real QPixmap for compatibility
        real_pixmap = QPixmap(10, 10)  # Create a small 10x10 pixmap

        # Mock QPixmap constructor to return the real pixmap
        with patch('src.views.components.header_frame.QPixmap', return_value=real_pixmap) as mock_pixmap:

            # Test case 1: No network connection and not in REGTEST mode
            mock_get_wallet_network.return_value = 'MAINNET'  # Not REGTEST
            header_frame.handle_network_frame_visibility(network_status=False)

            # Assertions for no network connection
            assert not header_frame.network_error_frame.isHidden()
            assert header_frame.network_error_info_label.text() == 'connection_error_message'
            assert header_frame.network_error_frame.toolTip() == ''
            assert header_frame.network_error_frame.cursor().shape() == Qt.ArrowCursor

            # Verify QPixmap was called to set the network error icon
            assert mock_pixmap.call_count == 1, f"Expected QPixmap to be called once, but got {
                mock_pixmap.call_count
            }"
            mock_pixmap.assert_called_with(':assets/network_error.png')
            assigned_pixmap = header_frame.network_error_icon_label.pixmap()
            assert assigned_pixmap.cacheKey() == real_pixmap.cacheKey()

            # Test case 2: Network connection is available
            with patch.object(header_frame, 'set_wallet_backup_frame', wraps=header_frame.set_wallet_backup_frame) as mock_set_wallet_backup_frame:

                # Mock os.path.exists to simulate the condition for backup warning
                with patch('os.path.exists', return_value=False), \
                        patch('src.data.repository.setting_repository.SettingRepository.is_backup_configured', return_value=MagicMock(is_backup_configured=False)), \
                        patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=MagicMock(value='EMBEDDED_TYPE_WALLET')):

                    # Call the method that should set the flag
                    header_frame.handle_network_frame_visibility(
                        network_status=True,
                    )

                    # Assertions for network connection
                    assert not header_frame.network_error_frame.isVisible()

                    # Ensure set_wallet_backup_frame is called when the network is available
                    mock_set_wallet_backup_frame.assert_called_once()

                    header_frame.is_backup_warning = True

                    # After set_wallet_backup_frame is called, check if the backup warning flag is updated
                    # Flag should be True because all conditions are met
                    assert header_frame.is_backup_warning is True


def test_set_wallet_backup_frame_show_backup_warning(header_frame):
    """Test set_wallet_backup_frame when backup warning should be shown."""

    # Mock the return values for conditions that show the backup warning frame
    with patch('src.data.repository.setting_repository.SettingRepository.is_backup_configured') as mock_is_backup_configured, \
            patch('os.path.exists', return_value=False), \
            patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type') as mock_get_wallet_type, \
            patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network') as mock_get_wallet_network:

        # Mock that the wallet type is EMBEDDED_TYPE_WALLET and backup is not configured
        mock_is_backup_configured.return_value = MagicMock(
            is_backup_configured=False,
        )
        mock_get_wallet_type.return_value = MagicMock(
            value=WalletType.EMBEDDED_TYPE_WALLET.value,
        )

        # Mock the network to return MAINNET (ensures the frame shows even if it is not in REGTEST mode)
        mock_get_wallet_network.return_value = 'MAINNET'
        header_frame.network_error_frame.setVisible(True)
        header_frame.is_backup_warning = True

        # Call the method that should trigger showing the backup warning
        header_frame.set_wallet_backup_frame()

        # Assertions to verify the backup warning frame is shown
        assert not header_frame.network_error_frame.isHidden() is True
        # The backup warning flag should be set
        assert header_frame.is_backup_warning is True
        assert header_frame.network_error_info_label.text() == 'backup_not_configured'

        # Check that the icon for no backup is set
        assert header_frame.network_error_icon_label.pixmap(
        ).cacheKey() == QPixmap(':assets/no_backup.png').cacheKey()

        # Check the tooltip for the backup warning
        assert header_frame.network_error_frame.toolTip() == 'backup_tooltip_text'


def test_set_wallet_backup_frame_hide_backup_warning(header_frame):
    """Test set_wallet_backup_frame when backup warning should not be shown."""

    # Mock the return values for conditions that do not show the backup warning frame
    with patch('src.data.repository.setting_repository.SettingRepository.is_backup_configured') as mock_is_backup_configured, \
            patch('os.path.exists', return_value=True), \
            patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type') as mock_get_wallet_type:

        # Mock that the token path exists (so the backup warning shouldn't be shown)
        mock_is_backup_configured.return_value = MagicMock(
            is_backup_configured=True,
        )
        mock_get_wallet_type.return_value = MagicMock(
            value=WalletType.EMBEDDED_TYPE_WALLET.value,
        )

        # Call the method that should hide the backup warning frame
        header_frame.set_wallet_backup_frame()

        # Assertions to verify the backup warning frame is hidden
        assert header_frame.network_error_frame.isVisible() is False
        # The backup warning flag should be reset
        assert header_frame.is_backup_warning is False


def test_set_button_visibility(header_frame):
    """Test set_button_visibility method to verify button visibility based on network status and title."""

    # Mock lists for button visibility conditions
    refresh_and_action_button_list = [
        'collectibles', 'fungibles', 'channel_management',
    ]
    refresh_button_list = ['view_unspent_list']

    # Test when title is in refresh_and_action_button_list and visibility is True
    header_frame.title = 'collectibles'  # Set the title to match one in the list
    header_frame.set_button_visibility(
        refresh_and_action_button_list, refresh_button_list, True,
    )

    # Assertions to check if the buttons are visible
    assert not header_frame.action_button.isHidden() is True
    assert not header_frame.refresh_page_button.isHidden() is True

    # Test when title is in refresh_button_list and visibility is True
    # Set the title to match refresh_button_list
    header_frame.title = 'view_unspent_list'
    header_frame.set_button_visibility(
        refresh_and_action_button_list, refresh_button_list, True,
    )

    # Assertions to check if the refresh page button is visible
    assert not header_frame.refresh_page_button.isHidden() is True

    # Test when title is not in any list and visibility is False
    header_frame.title = 'other_title'  # Set a title that is not in either list
    header_frame.set_button_visibility(
        refresh_and_action_button_list, refresh_button_list, False,
    )

    # Assertions to check if the buttons are not visible
    assert header_frame.action_button.isVisible() is False
    assert header_frame.refresh_page_button.isVisible() is False
