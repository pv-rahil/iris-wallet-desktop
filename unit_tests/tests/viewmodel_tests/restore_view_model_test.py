"""Tests for the RestoreViewModel class.
"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletAccessType
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_GOOGLE_CONFIGURE_FAILED
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.error_message import ERROR_WHILE_RESTORE
from src.utils.info_message import INFO_RESTORE_COMPLETED
from src.viewmodels.restore_view_model import RestoreViewModel


@pytest.fixture
def restore_view_model():
    """Fixture that creates a RestoreViewModel instance with mocked page navigation."""
    page_navigation = MagicMock()
    return RestoreViewModel(page_navigation)


def test_forward_to_fungibles_page(restore_view_model):
    """Test navigation to fungibles page."""
    # Arrange
    mock_sidebar = MagicMock()
    restore_view_model._page_navigation.sidebar.return_value = mock_sidebar

    # Act
    restore_view_model.forward_to_fungibles_page()

    # Assert
    mock_sidebar.my_fungibles.setChecked.assert_called_once_with(True)
    restore_view_model._page_navigation.enter_wallet_password_page.assert_called_once()


def test_on_success_restore_successful(restore_view_model, mocker):
    """Test successful restore with keyring storage working and password set correctly."""
    # Arrange
    restore_view_model.is_loading = MagicMock()
    restore_view_model.message = MagicMock()
    restore_view_model.forward_to_fungibles_page = MagicMock()
    restore_view_model.splash_view_model = MagicMock()

    restore_view_model.mnemonic = 'test mnemonic'
    restore_view_model.password = 'test password'

    # Mock SettingRepository methods
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_wallet_initialized',
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_backup_configured',
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )

    # Mock encryption and file write
    mocker.patch(
        'src.viewmodels.restore_view_model.mnemonic_store.encrypt',
        return_value=b'encrypted_data',
    )
    mocker.patch('src.viewmodels.restore_view_model.local_store.write_to_file')

    # Mock restore_keys and xpub set
    mock_keys = MagicMock(account_xpub='mock_xpub')
    mocker.patch(
        'src.data.repository.common_operations_repository.CommonOperationRepository.restore_keys', return_value=mock_keys,
    )
    mocker.patch('src.viewmodels.restore_view_model.local_store.set_value')

    # Mock password storage returns True
    mocker.patch(
        'src.viewmodels.restore_view_model.set_value',
        return_value=True,
    )

    # Act
    restore_view_model.on_success(True)

    # Assert
    restore_view_model.is_loading.emit.assert_called_once_with(False)
    restore_view_model.message.emit.assert_called_once_with(
        ToastPreset.SUCCESS, INFO_RESTORE_COMPLETED,
    )
    restore_view_model.forward_to_fungibles_page.assert_called_once()


def test_on_success_restore_failed(restore_view_model):
    """Test failed restore."""
    # Arrange
    restore_view_model.is_loading = MagicMock()
    restore_view_model.message = MagicMock()

    # Act
    restore_view_model.on_success(False)

    # Assert
    restore_view_model.is_loading.emit.assert_called_once_with(False)
    restore_view_model.message.emit.assert_called_once_with(
        ToastPreset.ERROR, ERROR_WHILE_RESTORE,
    )


def test_on_error_common_exception(restore_view_model):
    """Test error handling with CommonException."""
    # Arrange
    restore_view_model.is_loading = MagicMock()
    restore_view_model.message = MagicMock()
    error_message = 'Test error'
    error = CommonException(error_message)

    # Act
    restore_view_model.on_error(error)

    # Assert
    restore_view_model.is_loading.emit.assert_called_once_with(False)
    restore_view_model.message.emit.assert_called_once_with(
        ToastPreset.ERROR, error_message,
    )


def test_on_error_generic_exception(restore_view_model):
    """Test error handling with generic Exception."""
    # Arrange
    restore_view_model.is_loading = MagicMock()
    restore_view_model.message = MagicMock()
    error = Exception('Test error')

    # Act
    restore_view_model.on_error(error)

    # Assert
    restore_view_model.is_loading.emit.assert_called_once_with(False)
    restore_view_model.message.emit.assert_called_once_with(
        ToastPreset.ERROR, ERROR_SOMETHING_WENT_WRONG,
    )


def test_restore_google_auth_failed(restore_view_model, mocker):
    """Test restore when Google authentication fails."""
    # Arrange
    restore_view_model.is_loading = MagicMock()
    restore_view_model.message = MagicMock()
    mock_authenticate = mocker.patch(
        'src.viewmodels.restore_view_model.authenticate', return_value=False,
    )
    mock_app = MagicMock()
    mocker.patch(
        'PySide6.QtWidgets.QApplication.instance',
        return_value=mock_app,
    )

    # Act
    restore_view_model.restore('test mnemonic', 'test password')

    # Assert
    restore_view_model.is_loading.emit.assert_has_calls([
        mocker.call(True),
        mocker.call(False),
    ])
    mock_authenticate.assert_called_once_with(mock_app)
    restore_view_model.message.emit.assert_called_once_with(
        ToastPreset.ERROR,
        ERROR_GOOGLE_CONFIGURE_FAILED,
    )


def test_restore_success(restore_view_model, mocker):
    """Test successful restore flow."""
    # Arrange
    restore_view_model.is_loading = MagicMock()
    restore_view_model.run_in_thread = MagicMock()
    mock_authenticate = mocker.patch(
        'src.viewmodels.restore_view_model.authenticate', return_value=True,
    )
    mock_app = MagicMock()
    mocker.patch(
        'PySide6.QtWidgets.QApplication.instance',
        return_value=mock_app,
    )
    test_mnemonic = 'test mnemonic'
    test_password = 'test password'

    # Act
    restore_view_model.restore(test_password, test_mnemonic)

    # Assert
    restore_view_model.is_loading.emit.assert_called_once_with(True)
    mock_authenticate.assert_called_once_with(mock_app)
    assert restore_view_model.mnemonic == test_mnemonic
    assert restore_view_model.password == test_password
    restore_view_model.run_in_thread.assert_called_once()


def test_restore_generic_exception(restore_view_model, mocker):
    """Test restore handling of generic exception."""
    # Arrange
    restore_view_model.is_loading = MagicMock()
    restore_view_model.message = MagicMock()
    mocker.patch(
        'src.viewmodels.restore_view_model.authenticate',
        return_value=True,
    )
    mock_app = MagicMock()
    mocker.patch(
        'PySide6.QtWidgets.QApplication.instance',
        return_value=mock_app,
    )
    error = Exception('Unexpected error')
    restore_view_model.run_in_thread = MagicMock(side_effect=error)

    # Act
    restore_view_model.restore('test mnemonic', 'test password')

    # Assert
    restore_view_model.is_loading.emit.assert_has_calls([
        mocker.call(True),
        mocker.call(False),
    ])
    restore_view_model.message.emit.assert_called_once_with(
        ToastPreset.ERROR,
        ERROR_SOMETHING_WENT_WRONG,
    )


def test_store_software_wallet_data_writes_and_sets_keys(restore_view_model, mocker):
    """_store_software_wallet_data should encrypt mnemonic, write file, derive and save keys."""
    restore_view_model.password = 'pwd'
    restore_view_model.mnemonic = 'mn'
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.mnemonic_store.encrypt',
        return_value=b'encrypted',
    )
    write_file = mocker.patch(
        'src.viewmodels.restore_view_model.local_store.write_to_file',
    )
    keys = mocker.Mock(
        account_xpub_vanilla='vx',
        account_xpub_colored='cx', master_fingerprint='ff',
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.CommonOperationRepository.restore_keys', return_value=keys,
    )
    set_value_mock = mocker.patch(
        'src.viewmodels.restore_view_model.local_store.set_value',
    )

    restore_view_model._store_software_wallet_data()

    write_file.assert_called_once()
    assert set_value_mock.call_count == 3


def test_store_hardware_wallet_data_sets_values(restore_view_model, mocker):
    """_store_hardware_wallet_data should set xpubs and fingerprint."""
    restore_view_model.xpub_vanilla = 'vx'
    restore_view_model.xpub_colored = 'cx'
    restore_view_model.fingerprint = 'ff'
    set_value_mock = mocker.patch(
        'src.viewmodels.restore_view_model.local_store.set_value',
    )

    restore_view_model._store_hardware_wallet_data()

    assert set_value_mock.call_count == 3


def test_on_success_keyring_dialog_hw_watch_only_branch(mocker, restore_view_model):
    """When set_value returns False for HW/WatchOnly, open KeyringErrorDialog with xpubs."""
    # Arrange base state
    restore_view_model.password = 'pwd'
    restore_view_model.mnemonic = 'mn'
    restore_view_model.xpub_vanilla = 'vx'
    restore_view_model.xpub_colored = 'cx'
    restore_view_model.fingerprint = 'ff'
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.get_bitcoin_network_from_enum',
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch.object(restore_view_model, '_store_hardware_wallet_data')
    mocker.patch(
        'src.viewmodels.restore_view_model.set_value',
        return_value=False,
    )
    dlg_cls = mocker.patch(
        'src.viewmodels.restore_view_model.KeyringErrorDialog',
    )

    # Act
    restore_view_model.on_success(True)

    # Assert
    dlg_cls.assert_called_once()
    dlg_cls.return_value.exec.assert_called_once_with()


def test_on_success_keyring_dialog_software_branch(mocker, restore_view_model):
    """When set_value returns False for software wallet, open KeyringErrorDialog with mnemonic."""
    restore_view_model.password = 'pwd'
    restore_view_model.mnemonic = 'mn'
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.get_bitcoin_network_from_enum',
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_key_storage_type', return_value=None,
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_wallet_access_type', return_value=None,
    )
    mocker.patch.object(restore_view_model, '_store_software_wallet_data')
    mocker.patch(
        'src.viewmodels.restore_view_model.set_value',
        return_value=False,
    )
    dlg_cls = mocker.patch(
        'src.viewmodels.restore_view_model.KeyringErrorDialog',
    )

    restore_view_model.on_success(True)

    dlg_cls.assert_called_once()
    dlg_cls.return_value.exec.assert_called_once_with()


def test_handle_rgb_lib_incompatibility_close_app(mocker, restore_view_model):
    """Handle close button path: application exits."""
    dlg = mocker.Mock()
    dlg.rgb_lib_incompatibility_dialog.clickedButton.return_value = 'close'
    dlg.close_button = 'close'
    dlg.delete_app_data_button = 'del'
    mocker.patch(
        'src.viewmodels.restore_view_model.RgbLibIncompatibilityDialog', return_value=dlg,
    )
    app = mocker.Mock()
    mocker.patch(
        'src.viewmodels.restore_view_model.QApplication.instance', return_value=app,
    )

    restore_view_model.handle_rgb_lib_incompatibility()

    app.exit.assert_called_once_with()


def test_handle_rgb_lib_incompatibility_delete_data_confirm(mocker, restore_view_model):
    """Delete data flow with confirm should call on_delete_app_data."""
    dlg = mocker.Mock()
    dlg.rgb_lib_incompatibility_dialog.clickedButton.return_value = 'del'
    dlg.close_button = 'close'
    dlg.delete_app_data_button = 'del'
    dlg.confirmation_dialog.clickedButton.return_value = 'confirm'
    dlg.confirm_delete_button = 'confirm'
    dlg.cancel = 'cancel'
    mocker.patch(
        'src.viewmodels.restore_view_model.RgbLibIncompatibilityDialog', return_value=dlg,
    )
    restore_view_model.on_delete_app_data = MagicMock()

    restore_view_model.handle_rgb_lib_incompatibility()

    dlg.show_confirmation_dialog.assert_called_once_with()
    restore_view_model.on_delete_app_data.assert_called_once_with()


def test_handle_rgb_lib_incompatibility_delete_cancel_recurses(mocker, restore_view_model):
    """Cancel after delete should show confirm then re-open dialog once more."""
    # First dialog: choose delete then cancel confirmation
    dlg1 = mocker.Mock()
    dlg1.rgb_lib_incompatibility_dialog.clickedButton.return_value = 'del'
    dlg1.close_button = 'close'
    dlg1.delete_app_data_button = 'del'
    dlg1.confirmation_dialog.clickedButton.return_value = 'cancel'
    dlg1.confirm_delete_button = 'confirm'
    dlg1.cancel = 'cancel'
    # Second dialog: choose close to end flow
    dlg2 = mocker.Mock()
    dlg2.rgb_lib_incompatibility_dialog.clickedButton.return_value = 'close'
    dlg2.close_button = 'close'
    dlg2.delete_app_data_button = 'del'
    app = mocker.Mock()
    mocker.patch(
        'src.viewmodels.restore_view_model.QApplication.instance', return_value=app,
    )
    dlg_patch = mocker.patch(
        'src.viewmodels.restore_view_model.RgbLibIncompatibilityDialog', side_effect=[dlg1, dlg2],
    )

    restore_view_model.handle_rgb_lib_incompatibility()

    assert dlg_patch.call_count == 2
    dlg1.show_confirmation_dialog.assert_called_once_with()


def test_restore_uses_xpub_when_mnemonic_missing(restore_view_model, mocker):
    """restore should pass xpub to service when mnemonic is None."""
    mocker.patch(
        'src.viewmodels.restore_view_model.authenticate',
        return_value=True,
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.QApplication.instance',
        return_value=MagicMock(),
    )
    restore_view_model.run_in_thread = MagicMock()

    restore_view_model.restore('pwd', mnemonic=None, xpub_vanilla='xv')

    args = restore_view_model.run_in_thread.call_args[0][1]['args']
    assert args[0] == 'xv'


def test_on_delete_app_data_calls_delete(restore_view_model, mocker):
    """on_delete_app_data should call delete_app_data with base path and network."""
    mocker.patch(
        'src.viewmodels.restore_view_model.local_store.get_path',
        return_value='/tmp/base',
    )
    mocker.patch(
        'src.viewmodels.restore_view_model.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )
    delete = mocker.patch('src.viewmodels.restore_view_model.delete_app_data')
    log = mocker.patch('src.viewmodels.restore_view_model.logger.info')

    restore_view_model.on_delete_app_data()

    delete.assert_called_once()
    log.assert_called_once()
