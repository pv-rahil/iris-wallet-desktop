"""Unit test for welcome view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.viewmodels.welcome_view_model import WelcomeViewModel


@pytest.fixture
def mock_page_navigation():
    """Fixture for creating a mock page navigation object."""
    return Mock()


@pytest.fixture
def welcome_view_model(mock_page_navigation):
    """Fixture for creating an instance of WelcomeViewModel with a mock page navigation object."""
    return WelcomeViewModel(mock_page_navigation)


def test_initialization(welcome_view_model):
    """Test if the WelcomeViewModel is initialized correctly."""
    assert isinstance(welcome_view_model, WelcomeViewModel)
    assert welcome_view_model._page_navigation is not None


def test_on_create_click(welcome_view_model, mock_page_navigation, mocker):
    """Test if the on_create_click method works as expected."""
    mock_network = mocker.Mock()
    mock_network.value = 'testnet'
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_wallet_network',
        return_value=mock_network,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_wallet_signature_type',
        return_value=Mock(),
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.get_value',
        return_value='test_password',
    )
    welcome_view_model.on_create_click()
    mock_page_navigation.set_wallet_password_page.assert_called_once()


def test_restore_offline_wallet_schedules_sync_and_emits(welcome_view_model, mocker):
    """restore_offline_wallet should emit and schedule sync_from_usb with correct args."""
    slot = mocker.Mock()
    welcome_view_model.restore_button_clicked.connect(slot)
    welcome_view_model.run_in_thread = mocker.Mock()
    usb = Mock()
    data = Mock()

    welcome_view_model.restore_offline_wallet(usb, 'ff', data)

    slot.assert_called_once_with()
    welcome_view_model.run_in_thread.assert_called_once()


def test_handle_sync_completed_password_none_returns_early(welcome_view_model, mocker):
    """If password is None, should return early without side effects and still emit success at end."""
    data = Mock(password=None)
    # Spy Toast and navigation not called
    toast_success = mocker.patch(
        'src.viewmodels.welcome_view_model.ToastManager.success',
    )
    nav = welcome_view_model._page_navigation
    nav.enter_wallet_password_page = mocker.Mock()

    welcome_view_model.handle_sync_completed(data)

    toast_success.assert_not_called()
    nav.enter_wallet_password_page.assert_not_called()


def test_handle_sync_completed_success_sets_password_and_navigates(welcome_view_model, mocker):
    """When set_value True, should show success, set keyring status false, and navigate."""
    data = Mock(password='pwd')
    mock_network = mocker.Mock()
    mock_network.value = 'testnet'
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_wallet_network',
        return_value=mock_network,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.set_value',
        return_value=True,
    )
    toast_success = mocker.patch(
        'src.viewmodels.welcome_view_model.ToastManager.success',
    )
    set_status = mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.set_keyring_status',
    )
    nav = welcome_view_model._page_navigation
    nav.enter_wallet_password_page = mocker.Mock()

    welcome_view_model.handle_sync_completed(data)

    toast_success.assert_called_once()
    set_status.assert_called_once_with(status=False)
    nav.enter_wallet_password_page.assert_called_once_with()


def test_handle_sync_completed_keyring_dialog_hw_watch_only(welcome_view_model, mocker):
    """If set_value False and HW or WATCH_ONLY, open KeyringErrorDialog with xpubs path."""
    data = Mock(
        password='pwd', xpub_vanilla='vx', xpub_colored='cx',
        master_fingerprint='ff', mnemonic=None,
    )
    mock_network = mocker.Mock()
    mock_network.value = 'testnet'
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_wallet_network',
        return_value=mock_network,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.set_value',
        return_value=False,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    dlg_cls = mocker.patch(
        'src.viewmodels.welcome_view_model.KeyringErrorDialog',
    )

    welcome_view_model.handle_sync_completed(data)

    dlg_cls.assert_called_once()
    dlg_cls.return_value.exec.assert_called_once_with()


def test_handle_sync_completed_keyring_dialog_software(welcome_view_model, mocker):
    """If set_value False and software wallet, open KeyringErrorDialog with mnemonic path."""
    data = Mock(
        password='pwd', mnemonic='mn', xpub_vanilla=None,
        xpub_colored=None, master_fingerprint=None,
    )
    mock_network = mocker.Mock()
    mock_network.value = 'testnet'
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_wallet_network',
        return_value=mock_network,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.set_value',
        return_value=False,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_wallet_access_type', return_value=None,
    )
    mocker.patch(
        'src.viewmodels.welcome_view_model.SettingRepository.get_key_storage_type', return_value=None,
    )
    dlg_cls = mocker.patch(
        'src.viewmodels.welcome_view_model.KeyringErrorDialog',
    )

    welcome_view_model.handle_sync_completed(data)

    dlg_cls.assert_called_once()
    dlg_cls.return_value.exec.assert_called_once_with()


def test_handle_sync_error_emits_and_toast(welcome_view_model, mocker):
    """handle_sync_error should emit failed and show toast with error.message."""
    err = Mock(message='boom')
    slot = mocker.Mock()
    welcome_view_model.restore_process_failed.connect(slot)
    toast_error = mocker.patch(
        'src.viewmodels.welcome_view_model.ToastManager.error',
    )

    welcome_view_model.handle_sync_error(err)

    slot.assert_called_once_with()
    toast_error.assert_called_once_with('boom')
