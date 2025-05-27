"""Unit test for backup UI"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.data.repository.setting_repository import SettingRepository
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.ui_backup import Backup


@pytest.fixture
def mock_backup_view_model(mocker):
    """Fixture to create a mock MainViewModel."""
    return mocker.Mock()


@pytest.fixture
def backup_widget(qtbot, mock_backup_view_model):
    """Fixture to create the Backup widget."""
    widget = Backup(mock_backup_view_model)
    qtbot.addWidget(widget)
    return widget


def test_backup_initialization(backup_widget):
    """Test the initialization of the Backup widget."""
    assert backup_widget.backup_title_label.text() == 'backup'
    assert backup_widget.backup_close_btn.icon().isNull() is False
    assert backup_widget.backup_close_btn.isCheckable() is False


def test_backup_close_button(qtbot, backup_widget):
    """Test the close button click action."""
    qtbot.mouseClick(backup_widget.backup_close_btn, Qt.LeftButton)
    assert not backup_widget.isVisible()


def test_backup_layout(backup_widget):
    """Test the layout structure of the Backup widget."""
    assert backup_widget.grid_layout_backup_page is not None
    assert backup_widget.grid_layout is not None
    assert backup_widget.vertical_layout_backup_wallet_widget is not None
    assert backup_widget.title_layout is not None

    assert backup_widget.grid_layout_backup_page.count() > 0
    assert backup_widget.grid_layout.count() > 0
    assert backup_widget.vertical_layout_backup_wallet_widget.count() > 0
    assert backup_widget.title_layout.count() > 0


def test_backup_close_button_icon(backup_widget):
    """Test if the close button has the correct icon."""
    icon = backup_widget.backup_close_btn.icon()
    assert not icon.isNull()


def test_handle_mnemonic_visibility_hide(backup_widget, qtbot):
    """Test hiding the mnemonic visibility."""
    with patch.object(backup_widget, 'hide_mnemonic_widget'):
        # Set initial state to "Hide Mnemonic"
        backup_widget.show_mnemonic_button.setText(
            backup_widget.hide_mnemonic_text,
        )

        backup_widget.handle_mnemonic_visibility()

        # Verify that the widget's state has been updated
        assert backup_widget.hide_mnemonic_widget.called
        assert backup_widget.show_mnemonic_button.text() == backup_widget.show_mnemonic_text


def test_show_mnemonic_widget(backup_widget, qtbot):
    """Test that the mnemonic widget is shown and layout is adjusted."""
    backup_widget.show_mnemonic_widget()

    assert backup_widget.backup_widget.minimumSize() == QSize(499, 808)
    assert backup_widget.backup_widget.maximumSize() == QSize(499, 808)
    assert backup_widget.show_mnemonic_frame.minimumSize() == QSize(402, 370)
    assert backup_widget.show_mnemonic_frame.maximumSize() == QSize(402, 370)


def test_hide_mnemonic_widget(backup_widget, qtbot):
    """Test that the mnemonic widget is hidden and layout is adjusted."""
    backup_widget.hide_mnemonic_widget()

    assert not backup_widget.mnemonic_frame.isVisible()
    assert backup_widget.backup_widget.minimumSize() == QSize(499, 608)
    assert backup_widget.backup_widget.maximumSize() == QSize(499, 615)
    assert backup_widget.show_mnemonic_frame.minimumSize() == QSize(402, 194)
    assert backup_widget.show_mnemonic_frame.maximumSize() == QSize(402, 197)


def test_backup_data_with_keyring_enabled(backup_widget, qtbot):
    """Test the backup_data method when keyring is enabled."""
    with patch.object(SettingRepository, 'get_keyring_status', return_value=True), \
            patch('src.views.ui_restore_mnemonic.RestoreMnemonicWidget.exec') as mock_exec:

        backup_widget.backup_data()

        # Verify that the mnemonic dialog is shown
        assert mock_exec.called


def test_backup_data_with_keyring_disabled(backup_widget, qtbot):
    """Test the backup_data method when keyring is disabled."""
    with patch.object(SettingRepository, 'get_keyring_status', return_value=False), \
            patch.object(backup_widget._view_model.backup_view_model, 'backup') as mock_backup:

        backup_widget.backup_data()

        # Verify that the backup method is called
        assert mock_backup.called


def test_update_loading_state_loading(backup_widget, qtbot):
    """Test the update_loading_state method when is_loading is True."""
    with patch.object(backup_widget.backup_wallet_data_button, 'start_loading') as mock_start_loading:
        backup_widget.update_loading_state(True)

        # Verify that the loading starts
        assert mock_start_loading.called


def test_update_loading_state_not_loading(backup_widget, qtbot):
    """Test the update_loading_state method when is_loading is False."""
    with patch.object(backup_widget.backup_wallet_data_button, 'stop_loading') as mock_stop_loading:
        backup_widget.update_loading_state(False)

        # Verify that the loading stops
        assert mock_stop_loading.called


def test_close_button_navigation(backup_widget):
    """Test the close button navigation."""
    with patch.object(backup_widget._view_model, 'page_navigation') as mock_navigation:
        # Mock the originating page
        backup_widget.get_checked_button_translation_key = Mock(
            return_value='fungibles',
        )

        # Trigger the close button action
        backup_widget.close_button_navigation()

        # Assert the correct navigation method is called
        mock_navigation.fungibles_asset_page.assert_called_once()


def test_set_mnemonic_visibility_with_keyring(backup_widget):
    """Test mnemonic visibility based on keyring status."""
    with patch.object(SettingRepository, 'get_keyring_status', return_value=True):
        backup_widget.set_mnemonic_visibility()
        assert not backup_widget.show_mnemonic_frame.isVisible()


def test_configure_backup_success(backup_widget, qtbot):
    """Test the configure backup method on successful authentication."""
    with patch('src.views.ui_backup.authenticate', return_value=True):
        # Simulate successful backup configuration
        backup_widget.configure_backup()
        qtbot.waitExposed(backup_widget)
        backup_widget.repaint()
        backup_widget.update()

        assert backup_widget.configure_backup_button.isHidden()
        assert not backup_widget.backup_wallet_data_button.isHidden()


def test_configure_backup_failure(backup_widget):
    """Test the configure backup method when authentication fails."""
    with patch('src.views.ui_backup.authenticate', return_value=False), \
            patch.object(backup_widget.configure_backup_button, 'isHidden', return_value=False), \
            patch.object(backup_widget.backup_wallet_data_button, 'isHidden', return_value=True):
        # Simulate failed backup configuration
        backup_widget.configure_backup()

        assert not backup_widget.configure_backup_button.isHidden()
        assert backup_widget.backup_wallet_data_button.isHidden()


def test_is_already_configured_existing_token(backup_widget):
    """Test the Google Drive configuration when the token exists."""
    with patch('os.path.exists', return_value=True):
        # Simulate the configuration already being done (token exists)
        backup_widget.is_already_configured()

        assert not backup_widget.backup_wallet_data_button.isHidden()
        assert backup_widget.configure_backup_button.isHidden()


def test_is_already_configured_no_token(backup_widget):
    """Test the Google Drive configuration when the token doesn't exist."""
    with patch('os.path.exists', return_value=False):
        # Simulate that the configuration has not been done (no token)
        backup_widget.is_already_configured()

        assert backup_widget.backup_wallet_data_button.isHidden()
        assert not backup_widget.configure_backup_button.isHidden()


def test_handle_mnemonic_visibility_show(backup_widget):
    """Test showing the mnemonic when the show_mnemonic_button is clicked."""
    mock_mnemonic_string = 'apple banana cherry date elderberry fig grape'
    with patch('src.views.ui_backup.mnemonic_store') as mock_store, \
            patch.object(backup_widget, 'show_mnemonic_widget') as mock_show_widget:

        # Mock the decrypted mnemonic
        mock_store.decrypted_mnemonic = mock_mnemonic_string

        # Set the button to initial "Show Mnemonic" state
        backup_widget.show_mnemonic_button.setText(
            QApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'show_mnemonic',
                'Show Mnemonic',
            ),
        )

        # Trigger visibility toggle
        backup_widget.handle_mnemonic_visibility()

        # Verify that the mnemonic labels are populated correctly
        mnemonic_list = mock_mnemonic_string.split()
        for i, word in enumerate(mnemonic_list, start=1):
            label = getattr(backup_widget, f'mnemonic_text_label_{i}')
            assert label.text() == f"{i}. {word}"

        # Verify that the button text and icon are updated
        assert backup_widget.show_mnemonic_button.text() == backup_widget.hide_mnemonic_text
        assert backup_widget.show_mnemonic_button.icon().isNull() is False

        # Verify that the show_mnemonic_widget method was called
        mock_show_widget.assert_called_once()
