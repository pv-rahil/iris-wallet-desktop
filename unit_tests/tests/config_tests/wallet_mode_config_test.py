# pylint: disable=redefined-outer-name, unused-argument
"""Unit tests for wallet mode configuration."""
from __future__ import annotations

from unittest.mock import patch

from src.config.wallet_mode_config import WalletModeConfiguration
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_online_watch_only(mock_get_sig_type):
    """Test configuration for Online Watch-Only Wallet."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.ONLINE_TYPE_WALLET,
        WalletAccessType.WATCH_ONLY,
        None,
        None,
    )
    assert config.mode_name == 'Online Watch-Only Wallet'
    assert config.privileges.can_sign_psbt is False


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_online_create_on_device(mock_get_sig_type):
    """Test configuration for Online Wallet - Create New (On Device)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.ONLINE_TYPE_WALLET,
        WalletAccessType.WITH_PRIVATE_KEY,
        WalletEntryType.CREATE,
        KeyStorageType.ON_DEVICE,
    )
    assert config.mode_name == 'Online Wallet - Create New (On Device)'
    assert config.privileges.can_sign_psbt is False

    mock_get_sig_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.ONLINE_TYPE_WALLET,
        WalletAccessType.WITH_PRIVATE_KEY,
        WalletEntryType.CREATE,
        KeyStorageType.ON_DEVICE,
    )
    assert config.privileges.can_sign_psbt is True


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_online_create_hardware(mock_get_sig_type):
    """Test configuration for Online Wallet - Create New (Hardware)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.ONLINE_TYPE_WALLET,
        WalletAccessType.WITH_PRIVATE_KEY,
        WalletEntryType.CREATE,
        KeyStorageType.HARDWARE_WALLET,
    )
    assert config.mode_name == 'Online Wallet - Create New (Hardware)'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_online_load_on_device(mock_get_sig_type):
    """Test configuration for Online Wallet - Load Existing (On Device)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.ONLINE_TYPE_WALLET,
        WalletAccessType.WITH_PRIVATE_KEY,
        WalletEntryType.LOAD,
        KeyStorageType.ON_DEVICE,
    )
    assert config.mode_name == 'Online Wallet - Load Existing (On Device)'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_online_load_hardware(mock_get_sig_type):
    """Test configuration for Online Wallet - Load Existing (Hardware)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.ONLINE_TYPE_WALLET,
        WalletAccessType.WITH_PRIVATE_KEY,
        WalletEntryType.LOAD,
        KeyStorageType.HARDWARE_WALLET,
    )
    assert config.mode_name == 'Online Wallet - Load Existing (Hardware)'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_offline_create_on_device(mock_get_sig_type):
    """Test configuration for Offline Wallet - Create New (On Device)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.OFFLINE_TYPE_WALLET,
        None,
        WalletEntryType.CREATE,
        KeyStorageType.ON_DEVICE,
    )
    assert config.mode_name == 'Offline Wallet - Create New (On Device)'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_offline_create_hardware(mock_get_sig_type):
    """Test configuration for Offline Wallet - Create New (Hardware)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.OFFLINE_TYPE_WALLET,
        None,
        WalletEntryType.CREATE,
        KeyStorageType.HARDWARE_WALLET,
    )
    assert config.mode_name == 'Offline Wallet - Create New (Hardware)'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_offline_load_on_device(mock_get_sig_type):
    """Test configuration for Offline Wallet - Load Existing (On Device)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.OFFLINE_TYPE_WALLET,
        None,
        WalletEntryType.LOAD,
        KeyStorageType.ON_DEVICE,
    )
    assert config.mode_name == 'Offline Wallet - Load Existing (On Device)'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_offline_load_hardware(mock_get_sig_type):
    """Test configuration for Offline Wallet - Load Existing (Hardware)."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        WalletType.OFFLINE_TYPE_WALLET,
        None,
        WalletEntryType.LOAD,
        KeyStorageType.HARDWARE_WALLET,
    )
    assert config.mode_name == 'Offline Wallet - Load Existing (Hardware)'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type')
def test_get_mode_config_default(mock_get_sig_type):
    """Test configuration for unknown or invalid wallet mode combinations."""
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    config = WalletModeConfiguration.get_mode_config(
        None, None, None, None,
    )
    assert config.mode_name == 'Unknown Mode'
