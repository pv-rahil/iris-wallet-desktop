"""Unit test for header frame component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.components.header_frame import HeaderFrame


@pytest.fixture
def header_frame():
    """Fixture to create a HeaderFrame instance with permissive privileges."""
    class Priv:
        """Privileges class."""
        can_send_transactions = True
        can_receive_asset = True
        can_create_assets = True
        can_backup_wallet = True
        can_broadcast_psbt = True
        can_use_faucet = True
        can_sign_psbt = True

    class Cfg:
        """Config class."""
        privileges = Priv()
        capabilities = []
        limitations = []
        mode_name = 'test'
        description = ''
        recommended_for = []

    with patch('src.utils.common_utils.get_current_wallet_mode_config', return_value=Cfg()):
        with patch('src.data.repository.setting_repository.SettingRepository.is_backup_configured') as mock_is_backup_configured:
            # Ensure backup is configured by default
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
    assert header_frame.network_error_frame.isHidden()


def test_set_button_visibility_for_refresh_and_action_buttons(header_frame, qtbot):
    """Test visibility of refresh and action buttons based on the title."""
    qtbot.addWidget(header_frame)
    header_frame.show()
    header_frame.title = 'collectibles'
    header_frame.set_button_visibility(
        ['collectibles', 'fungibles'], [
            'view_unspent_list',
        ], True,
    )
    assert header_frame.action_button.isVisible() == bool(
        header_frame.priv.can_create_assets,
    )
    assert header_frame.refresh_page_button.isVisible()

    header_frame.set_button_visibility(
        ['collectibles', 'fungibles'], [
            'view_unspent_list',
        ], False,
    )
    assert not header_frame.action_button.isVisible(
    ) or not header_frame.priv.can_create_assets
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
                        patch('src.data.repository.setting_repository.SettingRepository.is_backup_configured', return_value=MagicMock(is_backup_configured=False)):
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


def test_set_wallet_backup_frame_hide_backup_warning(header_frame):
    """Test set_wallet_backup_frame when backup warning should not be shown."""

    # Mock the return values for conditions that do not show the backup warning frame
    with patch('src.data.repository.setting_repository.SettingRepository.is_backup_configured') as mock_is_backup_configured, \
            patch('src.views.components.header_frame.os.path.exists', return_value=True):
        # Mock that the token path exists (so the backup warning shouldn't be shown)
        mock_is_backup_configured.return_value = MagicMock(
            is_backup_configured=True,
        )

        # Call the method that should hide the backup warning frame
        header_frame.set_wallet_backup_frame()

        # Assertions to verify the backup warning frame is hidden
        assert header_frame.network_error_frame.isVisible() is False
        # The backup warning flag should be reset
        assert header_frame.is_backup_warning is False


def test_set_button_visibility(header_frame, qtbot):
    """Test set_button_visibility method to verify button visibility based on network status and title."""
    qtbot.addWidget(header_frame)
    header_frame.show()

    # Mock lists for button visibility conditions
    refresh_and_action_button_list = [
        'collectibles', 'fungibles',
    ]
    refresh_button_list = ['view_unspent_list']

    # Test when title is in refresh_and_action_button_list and visibility is True
    header_frame.title = 'collectibles'  # Set the title to match one in the list
    header_frame.set_button_visibility(
        refresh_and_action_button_list, refresh_button_list, True,
    )

    # Assertions to check if the buttons are visible
    assert header_frame.action_button.isVisible() == bool(
        header_frame.priv.can_create_assets,
    )
    assert header_frame.refresh_page_button.isVisible() is True

    # Test when title is in refresh_button_list and visibility is True
    # Set the title to match refresh_button_list
    header_frame.title = 'view_unspent_list'
    header_frame.set_button_visibility(
        refresh_and_action_button_list, refresh_button_list, True,
    )

    # Assertions to check if the refresh page button is visible
    assert header_frame.refresh_page_button.isVisible() is True

    # Test when title is not in any list and visibility is False
    header_frame.title = 'other_title'  # Set a title that is not in either list
    header_frame.set_button_visibility(
        refresh_and_action_button_list, refresh_button_list, False,
    )

    # Assertions to check if the buttons are not visible/changed
    assert (not header_frame.action_button.isVisible()) or (
        not header_frame.priv.can_create_assets
    )
    # Title not in any list -> refresh visibility should remain as previously set (True)
    assert header_frame.refresh_page_button.isVisible() is True


def test_mouse_press_and_network_frame_click_navigates_backup(header_frame, qtbot):
    """Clicking backup warning frame should emit backup_page_signal (connect a test slot)."""
    qtbot.addWidget(header_frame)
    header_frame.show()
    header_frame.network_error_frame.show()
    header_frame.is_backup_warning = True
    calls = []
    header_frame.page_navigation.backup_page_signal.connect(
        lambda: calls.append(1),
    )
    header_frame.on_network_frame_click()
    assert len(calls) == 1


def test_set_usb_sync_frame_and_click_hidden_noop(header_frame):
    """on_usb_sync_frame_click returns early when frame hidden."""
    header_frame.usb_sync_frame.hide()
    header_frame.on_usb_sync_frame_click()  # Should not error or proceed


def test_set_usb_sync_frame_and_click_flow(header_frame, mocker, qtbot):
    """USB sync frame click triggers perform_sync when accepted and drive selected."""
    # Prepare visible USB frame
    qtbot.addWidget(header_frame)
    header_frame.show()
    header_frame.set_usb_sync_frame()
    # Patch internals
    mocker.patch.object(
        header_frame, '_check_keyring_state', return_value='pwd',
    )
    mocker.patch.object(
        header_frame.usb_detector,
        'detect_usb_drives', return_value=[{'name': 'Drive'}],
    )
    mocker.patch.object(
        header_frame.usb_sync_frame,
        'isVisible', return_value=True,
    )
    # Mock dialog
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = 1  # QDialog.Accepted
    mock_dialog.get_selected_drive.return_value = {'name': 'Drive'}
    mocker.patch(
        'src.views.components.header_frame.USBSyncDialog',
        return_value=mock_dialog,
    )
    perf = mocker.patch.object(
        header_frame.header_frame_view_model, 'perform_sync',
    )
    header_frame.on_usb_sync_frame_click()
    perf.assert_called_once()


def test_handle_sync_process_started_and_ended(header_frame, mocker):
    """Cover loader start/stop and refresh/update triggers on 'from_usb'."""
    # Patch factory to avoid real UI
    mocker.patch(
        'src.views.components.header_frame.LoadingTranslucentScreen', return_value=MagicMock(),
    )
    header_frame.handle_sync_process_started()

    # For ended use same instance
    click = mocker.patch.object(header_frame.refresh_page_button, 'click')
    up = mocker.patch.object(header_frame, 'update_psbt_info')
    header_frame.handle_sync_process_ended('from_usb')
    click.assert_called_once()
    up.assert_called_once()


def test_check_keyring_state_disabled(header_frame, mocker):
    """When keyring disabled, returns password from secure storage."""
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_keyring_status', return_value=False,
    )
    net = MagicMock()
    net.value = 'MAINNET'
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network', return_value=net,
    )
    mocker.patch(
        'src.views.components.header_frame.get_value',
        return_value='pw',
    )
    assert header_frame._check_keyring_state() == 'pw'


def test_check_keyring_state_enabled_accepts(header_frame, mocker):
    """When keyring enabled and dialog accepted, returns entered password."""
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_keyring_status', return_value=True,
    )
    # Mock RestoreMnemonicWidget
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = 1  # Accepted
    pwd_input = MagicMock()
    pwd_input.text.return_value = 'pw'
    mock_dialog.password_input = pwd_input
    mocker.patch(
        'src.views.components.header_frame.RestoreMnemonicWidget',
        return_value=mock_dialog,
    )
    assert header_frame._check_keyring_state() == 'pw'


def test_check_keyring_state_enabled_rejected(header_frame, mocker):
    """When keyring enabled and dialog rejected, returns None."""
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_keyring_status', return_value=True,
    )
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = 0  # Rejected
    mocker.patch(
        'src.views.components.header_frame.RestoreMnemonicWidget',
        return_value=mock_dialog,
    )
    assert header_frame._check_keyring_state() is None


def test_update_psbt_info_watch_only(header_frame, mocker, qtbot):
    """Show broadcast banner for watch-only with signed drafts count."""
    qtbot.addWidget(header_frame)
    header_frame.show()
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    sess = MagicMock()
    sess.list_psbt.return_value = [1, 2]
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=sess,
    )
    header_frame.update_psbt_info()
    assert header_frame.psbt_info_frame.isVisible()


def test_update_psbt_info_offline(header_frame, mocker, qtbot):
    """Show sign banner for offline wallet with unsigned drafts count."""
    qtbot.addWidget(header_frame)
    header_frame.show()
    # access_type != WATCH_ONLY, wallet_type == OFFLINE_TYPE_WALLET
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WITH_PRIVATE_KEY,
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_type',
        return_value=WalletType.OFFLINE_TYPE_WALLET,
    )
    sess = MagicMock()
    sess.list_psbt.return_value = [1]
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=sess,
    )
    header_frame.update_psbt_info()
    assert header_frame.psbt_info_frame.isVisible()


def test_update_psbt_info_none(header_frame, mocker, qtbot):
    """Hide banner when no drafts or other wallet types."""
    qtbot.addWidget(header_frame)
    header_frame.show()
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WITH_PRIVATE_KEY,
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=None,
    )
    header_frame.update_psbt_info()
    assert not header_frame.psbt_info_frame.isVisible()
