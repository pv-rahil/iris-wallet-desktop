"""Unit test for welcome view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
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

    slot.assert_called_once()
    toast_error.assert_called_once_with('boom')


def test_on_create_click_multisig(welcome_view_model, mock_page_navigation, mocker):
    """Test on_create_click for multisig path."""
    mock_network = mocker.Mock(value='testnet')
    mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.get_wallet_network', return_value=mock_network)
    mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.MULTI_SIG_WALLET)
    mocker.patch('src.viewmodels.welcome_view_model.get_value', return_value='pwd')
    
    mock_run = mocker.patch.object(welcome_view_model, 'run_in_thread')
    slot = mocker.Mock()
    welcome_view_model.create_button_clicked.connect(slot)
    
    welcome_view_model.on_create_click()
    
    slot.assert_called_once_with(True)
    mock_run.assert_called_once()


def test_on_multisig_wallet_initialized(welcome_view_model, mock_page_navigation, mocker):
    """Test _on_multisig_wallet_initialized callback."""
    set_init = mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.set_wallet_initialized')
    set_ver = mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.set_rgb_lib_version')
    slot = mocker.Mock()
    welcome_view_model.create_button_clicked.connect(slot)
    
    welcome_view_model._on_multisig_wallet_initialized(None)
    
    slot.assert_called_once_with(False)
    set_init.assert_called_once()
    set_ver.assert_called_once()
    mock_page_navigation.fungibles_asset_page.assert_called_once()


def test_on_multisig_init_error(welcome_view_model, mocker):
    """Test _on_multisig_init_error callback."""
    toast_error = mocker.patch('src.viewmodels.welcome_view_model.ToastManager.error')
    slot = mocker.Mock()
    welcome_view_model.create_button_clicked.connect(slot)
    
    err = mocker.Mock(message='failed')
    welcome_view_model._on_multisig_init_error(err)
    
    slot.assert_called_once_with(False)
    toast_error.assert_called_once_with('failed')


def test_handle_sync_completed_multisig_restore(welcome_view_model, mocker, tmp_path):
    """Test handle_sync_completed restores multisig config if file exists."""
    data = Mock(password='pwd')
    mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.get_wallet_network', return_value=Mock(value='testnet'))
    mocker.patch('src.viewmodels.welcome_view_model.set_value', return_value=True)
    mocker.patch('src.viewmodels.welcome_view_model.ToastManager.success')
    mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.set_keyring_status')
    
    ap = mocker.Mock(multisig_cosigners_file_path=str(tmp_path / 'cosigners.json'))
    mocker.patch('src.viewmodels.welcome_view_model.app_paths', ap)
    
    import json
    with open(ap.multisig_cosigners_file_path, 'w') as f:
        json.dump({'required_signers': 2, 'total_signers': 3, 'cosigners': ['c1', 'c2']}, f)
        
    set_sig = mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.set_wallet_signature_type')
    set_conf = mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.set_multisig_config')
    set_cos = mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.set_cosigners')
    set_th = mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.set_threshold_confirmed')
    
    welcome_view_model.handle_sync_completed(data)
    
    set_sig.assert_called_once_with(WalletSignatureType.MULTI_SIG_WALLET)
    set_conf.assert_called_once_with(2, 3)
    set_cos.assert_called_once_with(['c1', 'c2'])
    set_th.assert_called_once_with(True)


def test_handle_sync_completed_multisig_restore_fail(welcome_view_model, mocker, tmp_path):
    """Test handle_sync_completed logs error if cosigners file is invalid."""
    data = Mock(password='pwd')
    mocker.patch('src.viewmodels.welcome_view_model.SettingRepository.get_wallet_network', return_value=Mock(value='testnet'))
    mocker.patch('src.viewmodels.welcome_view_model.set_value', return_value=True)
    
    ap = mocker.Mock(multisig_cosigners_file_path=str(tmp_path / 'invalid.json'))
    mocker.patch('src.viewmodels.welcome_view_model.app_paths', ap)
    with open(ap.multisig_cosigners_file_path, 'w') as f:
        f.write('invalid json')
        
    mock_logger = mocker.patch('src.viewmodels.welcome_view_model.logger.error')
    
    welcome_view_model.handle_sync_completed(data)
    
    mock_logger.assert_called()
