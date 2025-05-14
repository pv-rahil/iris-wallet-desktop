"""Unit tests for setting repository"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, protected-access, too-many-lines
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.setting_model import IsBackupConfiguredModel
from src.model.setting_model import IsNativeLoginIntoAppEnabled
from src.model.setting_model import IsWalletInitialized
from src.model.setting_model import NativeAuthenticationStatus
from src.model.setting_model import SetWalletInitialized
from src.utils.constant import IS_NATIVE_AUTHENTICATION_ENABLED
from src.utils.constant import NATIVE_LOGIN_ENABLED
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_KEYRING_STATUS


@pytest.fixture
def mock_local_store():
    """Fixture for mocking local_store"""
    with patch('src.data.repository.setting_repository.local_store') as mock:
        yield mock


@pytest.fixture
def mock_handle_exceptions():
    """Fixture for mocking handle_exceptions"""
    with patch('src.data.repository.setting_repository.handle_exceptions') as mock:
        mock.side_effect = lambda e: 'Error handled'
        yield mock


@pytest.fixture
def mock_get_value():
    """Fixture for mocking get_value"""
    with patch('src.data.repository.setting_repository.get_value') as mock:
        yield mock


@pytest.fixture
def mock_set_value():
    """Fixture for mocking set_value"""
    with patch('src.data.repository.setting_repository.set_value') as mock:
        yield mock


@patch('src.data.repository.setting_repository.bitcoin_network.__network__', NetworkEnumModel.TESTNET.value)
def test_get_wallet_network():
    """Test get_wallet_network method"""
    # Execute
    result = SettingRepository.get_wallet_network()

    # Assert
    assert result == NetworkEnumModel.TESTNET


def test_is_wallet_initialized_true(mock_local_store):
    """Test is_wallet_initialized when wallet is initialized"""
    # Setup
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.is_wallet_initialized()

    # Assert
    assert isinstance(result, IsWalletInitialized)
    assert result.is_wallet_initialized is True
    mock_local_store.get_value.assert_called_once_with('isWalletCreated')


def test_is_wallet_initialized_false(mock_local_store):
    """Test is_wallet_initialized when wallet is not initialized"""
    # Setup
    mock_local_store.get_value.return_value = False

    # Execute
    result = SettingRepository.is_wallet_initialized()

    # Assert
    assert isinstance(result, IsWalletInitialized)
    assert result.is_wallet_initialized is False
    mock_local_store.get_value.assert_called_once_with('isWalletCreated')


def test_is_wallet_initialized_none(mock_local_store):
    """Test is_wallet_initialized when value is None"""
    # Setup
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingRepository.is_wallet_initialized()

    # Assert
    assert isinstance(result, IsWalletInitialized)
    assert result.is_wallet_initialized is False
    mock_local_store.get_value.assert_called_once_with('isWalletCreated')


def test_is_wallet_initialized_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in is_wallet_initialized"""
    # Setup
    mock_local_store.get_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.is_wallet_initialized()

    # Assert
    assert result == 'Error handled'
    mock_local_store.get_value.assert_called_once_with('isWalletCreated')
    mock_handle_exceptions.assert_called_once()


def test_set_wallet_initialized_success(mock_local_store):
    """Test set_wallet_initialized success"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.set_wallet_initialized()

    # Assert
    assert isinstance(result, SetWalletInitialized)
    assert result.status is True
    mock_local_store.set_value.assert_called_once_with('isWalletCreated', True)
    mock_local_store.get_value.assert_called_once_with(
        'isWalletCreated', value_type=bool,
    )


def test_set_wallet_initialized_failure(mock_local_store):
    """Test set_wallet_initialized failure"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = False

    # Execute
    result = SettingRepository.set_wallet_initialized()

    # Assert
    assert isinstance(result, SetWalletInitialized)
    assert result.status is False
    mock_local_store.set_value.assert_called_once_with('isWalletCreated', True)
    mock_local_store.get_value.assert_called_once_with(
        'isWalletCreated', value_type=bool,
    )


def test_set_wallet_initialized_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in set_wallet_initialized"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.set_wallet_initialized()

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with('isWalletCreated', True)
    mock_handle_exceptions.assert_called_once()


def test_is_backup_configured_true(mock_local_store):
    """Test is_backup_configured when backup is configured"""
    # Setup
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.is_backup_configured()

    # Assert
    assert isinstance(result, IsBackupConfiguredModel)
    assert result.is_backup_configured is True
    mock_local_store.get_value.assert_called_once_with('isBackupConfigured')


def test_is_backup_configured_false(mock_local_store):
    """Test is_backup_configured when backup is not configured"""
    # Setup
    mock_local_store.get_value.return_value = False

    # Execute
    result = SettingRepository.is_backup_configured()

    # Assert
    assert isinstance(result, IsBackupConfiguredModel)
    assert result.is_backup_configured is False
    mock_local_store.get_value.assert_called_once_with('isBackupConfigured')


def test_is_backup_configured_none(mock_local_store):
    """Test is_backup_configured when value is None"""
    # Setup
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingRepository.is_backup_configured()

    # Assert
    assert isinstance(result, IsBackupConfiguredModel)
    assert result.is_backup_configured is False
    mock_local_store.get_value.assert_called_once_with('isBackupConfigured')


def test_is_backup_configured_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in is_backup_configured"""
    # Setup
    mock_local_store.get_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.is_backup_configured()

    # Assert
    assert result == 'Error handled'
    mock_local_store.get_value.assert_called_once_with('isBackupConfigured')
    mock_handle_exceptions.assert_called_once()


def test_set_backup_configured_success(mock_local_store):
    """Test set_backup_configured success"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.set_backup_configured(True)

    # Assert
    assert isinstance(result, IsBackupConfiguredModel)
    assert result.is_backup_configured is True
    mock_local_store.set_value.assert_called_once_with(
        'isBackupConfigured', True,
    )
    mock_local_store.get_value.assert_called_once_with(
        'isBackupConfigured', value_type=bool,
    )


def test_set_backup_configured_failure(mock_local_store):
    """Test set_backup_configured failure"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = False

    # Execute
    result = SettingRepository.set_backup_configured(True)

    # Assert
    assert isinstance(result, IsBackupConfiguredModel)
    assert result.is_backup_configured is False
    mock_local_store.set_value.assert_called_once_with(
        'isBackupConfigured', True,
    )
    mock_local_store.get_value.assert_called_once_with(
        'isBackupConfigured', value_type=bool,
    )


def test_set_backup_configured_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in set_backup_configured"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.set_backup_configured(True)

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with(
        'isBackupConfigured', True,
    )
    mock_handle_exceptions.assert_called_once()


def test_unset_wallet_initialized_success(mock_local_store):
    """Test unset_wallet_initialized success"""
    # Setup
    mock_local_store.set_value.return_value = None

    # Execute
    result = SettingRepository.unset_wallet_initialized()

    # Assert
    assert result is True
    mock_local_store.set_value.assert_called_once_with(
        'isWalletCreated', False,
    )


def test_unset_wallet_initialized_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in unset_wallet_initialized"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.unset_wallet_initialized()

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with(
        'isWalletCreated', False,
    )
    mock_handle_exceptions.assert_called_once()


def test_set_keyring_status_success(mock_local_store):
    """Test set_keyring_status success"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.set_keyring_status(True)

    # Assert
    assert result is None
    mock_local_store.set_value.assert_called_once_with(
        'isKeyringDisable', True,
    )
    mock_local_store.get_value.assert_called_once_with('isKeyringDisable')


def test_set_keyring_status_failure(mock_local_store):
    """Test set_keyring_status failure"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = False  # Different from what was set

    # Execute
    with pytest.raises(CommonException) as exc_info:
        SettingRepository.set_keyring_status(True)

    # Assert
    assert str(exc_info.value) == ERROR_KEYRING_STATUS
    mock_local_store.set_value.assert_called_once_with(
        'isKeyringDisable', True,
    )
    mock_local_store.get_value.assert_called_once_with('isKeyringDisable')


def test_get_keyring_status_true(mock_local_store):
    """Test get_keyring_status when status is True"""
    # Setup
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.get_keyring_status()

    # Assert
    assert result is True
    mock_local_store.get_value.assert_called_once_with('isKeyringDisable')


def test_get_keyring_status_false(mock_local_store):
    """Test get_keyring_status when status is False"""
    # Setup
    mock_local_store.get_value.return_value = False

    # Execute
    result = SettingRepository.get_keyring_status()

    # Assert
    assert result is False
    mock_local_store.get_value.assert_called_once_with('isKeyringDisable')


def test_get_keyring_status_string(mock_local_store):
    """Test get_keyring_status when status is a string"""
    # Setup
    mock_local_store.get_value.return_value = 'true'

    # Execute
    with patch.object(SettingRepository, 'str_to_bool', return_value=True) as mock_str_to_bool:
        result = SettingRepository.get_keyring_status()

    # Assert
    assert result is True
    mock_local_store.get_value.assert_called_once_with('isKeyringDisable')
    mock_str_to_bool.assert_called_once_with('true')


def test_get_keyring_status_none(mock_local_store):
    """Test get_keyring_status when status is None"""
    # Setup
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingRepository.get_keyring_status()

    # Assert
    assert result is False
    mock_local_store.get_value.assert_called_once_with('isKeyringDisable')


def test_get_native_authentication_status_enabled(mock_get_value):
    """Test get_native_authentication_status when enabled"""
    # Setup
    with patch.object(SettingRepository, 'get_keyring_status', return_value=False):
        mock_get_value.return_value = 'true'
        with patch.object(SettingRepository, 'str_to_bool', return_value=True) as mock_str_to_bool:
            # Execute
            result = SettingRepository.get_native_authentication_status()

    # Assert
    assert isinstance(result, NativeAuthenticationStatus)
    assert result.is_enabled is True
    mock_get_value.assert_called_once_with(IS_NATIVE_AUTHENTICATION_ENABLED)
    mock_str_to_bool.assert_called_once_with('true')


def test_get_native_authentication_status_disabled(mock_get_value):
    """Test get_native_authentication_status when disabled"""
    # Setup
    with patch.object(SettingRepository, 'get_keyring_status', return_value=True):
        # Execute
        result = SettingRepository.get_native_authentication_status()

    # Assert
    assert isinstance(result, NativeAuthenticationStatus)
    assert result.is_enabled is False
    mock_get_value.assert_not_called()


def test_get_native_authentication_status_exception(mock_handle_exceptions):
    """Test exception handling in get_native_authentication_status"""
    # Setup
    with patch.object(SettingRepository, 'get_keyring_status', side_effect=Exception('Test exception')):
        # Execute
        result = SettingRepository.get_native_authentication_status()

    # Assert
    assert result == 'Error handled'
    mock_handle_exceptions.assert_called_once()


def test_set_native_authentication_status_success(mock_set_value):
    """Test set_native_authentication_status success"""
    # Setup
    mock_set_value.return_value = True

    # Execute
    with patch.object(SettingRepository, 'bool_to_str', return_value='true') as mock_bool_to_str:
        result = SettingRepository.set_native_authentication_status(True)

    # Assert
    assert result is True
    mock_set_value.assert_called_once_with(
        IS_NATIVE_AUTHENTICATION_ENABLED, 'true',
    )
    mock_bool_to_str.assert_called_once_with(True)


def test_set_native_authentication_status_exception(mock_set_value, mock_handle_exceptions):
    """Test exception handling in set_native_authentication_status"""
    # Setup
    mock_set_value.side_effect = Exception('Test exception')

    # Execute
    with patch.object(SettingRepository, 'bool_to_str', return_value='true'):
        result = SettingRepository.set_native_authentication_status(True)

    # Assert
    assert result == 'Error handled'
    mock_set_value.assert_called_once()
    mock_handle_exceptions.assert_called_once()


def test_native_login_enabled_true(mock_get_value):
    """Test native_login_enabled when enabled"""
    # Setup
    with patch.object(SettingRepository, 'get_keyring_status', return_value=False):
        mock_get_value.return_value = 'true'
        with patch.object(SettingRepository, 'str_to_bool', return_value=True) as mock_str_to_bool:
            # Execute
            result = SettingRepository.native_login_enabled()

    # Assert
    assert isinstance(result, IsNativeLoginIntoAppEnabled)
    assert result.is_enabled is True
    mock_get_value.assert_called_once_with(NATIVE_LOGIN_ENABLED)
    mock_str_to_bool.assert_called_once_with('true')


def test_native_login_enabled_false(mock_get_value):
    """Test native_login_enabled when disabled"""
    # Setup
    with patch.object(SettingRepository, 'get_keyring_status', return_value=True):
        # Execute
        result = SettingRepository.native_login_enabled()

    # Assert
    assert isinstance(result, IsNativeLoginIntoAppEnabled)
    assert result.is_enabled is False
    mock_get_value.assert_not_called()


def test_native_login_enabled_exception(mock_handle_exceptions):
    """Test exception handling in native_login_enabled"""
    # Setup
    with patch.object(SettingRepository, 'get_keyring_status', side_effect=Exception('Test exception')):
        # Execute
        result = SettingRepository.native_login_enabled()

    # Assert
    assert result == 'Error handled'
    mock_handle_exceptions.assert_called_once()


def test_enable_logging_native_authentication_success(mock_set_value):
    """Test enable_logging_native_authentication when successful"""
    # Setup
    mock_set_value.return_value = True

    # Execute
    with patch.object(SettingRepository, 'bool_to_str', return_value='true'):
        result = SettingRepository.enable_logging_native_authentication(True)

    # Assert
    assert result is True
    mock_set_value.assert_called_once_with(NATIVE_LOGIN_ENABLED, 'true')


def test_enable_logging_native_authentication_exception(mock_set_value, mock_handle_exceptions):
    """Test exception handling in enable_logging_native_authentication"""
    # Setup
    mock_set_value.side_effect = Exception('Test exception')

    # Execute
    with patch.object(SettingRepository, 'bool_to_str', return_value='true'):
        result = SettingRepository.enable_logging_native_authentication(True)

    # Assert
    assert result == 'Error handled'
    mock_set_value.assert_called_once_with(NATIVE_LOGIN_ENABLED, 'true')
    mock_handle_exceptions.assert_called_once()


def test_is_show_hidden_assets_enabled_true(mock_local_store):
    """Test is_show_hidden_assets_enabled when enabled"""
    # Setup
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.is_show_hidden_assets_enabled()

    # Assert
    assert result.is_enabled is True
    mock_local_store.get_value.assert_called_once_with(
        'isShowHiddenAssetEnable',
    )


def test_is_show_hidden_assets_enabled_none(mock_local_store):
    """Test is_show_hidden_assets_enabled when value is None"""
    # Setup
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingRepository.is_show_hidden_assets_enabled()

    # Assert
    assert result.is_enabled is False
    mock_local_store.get_value.assert_called_once_with(
        'isShowHiddenAssetEnable',
    )


def test_is_show_hidden_assets_enabled_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in is_show_hidden_assets_enabled"""
    # Setup
    mock_local_store.get_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.is_show_hidden_assets_enabled()

    # Assert
    assert result == 'Error handled'
    mock_local_store.get_value.assert_called_once_with(
        'isShowHiddenAssetEnable',
    )
    mock_handle_exceptions.assert_called_once()


def test_enable_show_hidden_asset_success_true(mock_local_store):
    """Test enable_show_hidden_asset when successful and enabled"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.enable_show_hidden_asset(True)

    # Assert
    assert result.is_enabled is True
    mock_local_store.set_value.assert_called_once_with(
        'isShowHiddenAssetEnable', True,
    )
    mock_local_store.get_value.assert_called_once_with(
        'isShowHiddenAssetEnable', value_type=bool,
    )


def test_enable_show_hidden_asset_success_false(mock_local_store):
    """Test enable_show_hidden_asset when successful but disabled"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = False

    # Execute
    result = SettingRepository.enable_show_hidden_asset(True)

    # Assert
    assert result.is_enabled is False
    mock_local_store.set_value.assert_called_once_with(
        'isShowHiddenAssetEnable', True,
    )
    mock_local_store.get_value.assert_called_once_with(
        'isShowHiddenAssetEnable', value_type=bool,
    )


def test_enable_show_hidden_asset_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in enable_show_hidden_asset"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.enable_show_hidden_asset(True)

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with(
        'isShowHiddenAssetEnable', True,
    )
    mock_handle_exceptions.assert_called_once()


def test_is_exhausted_asset_enabled_true(mock_local_store):
    """Test is_exhausted_asset_enabled when enabled"""
    # Setup
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.is_exhausted_asset_enabled()

    # Assert
    assert result.is_enabled is True
    mock_local_store.get_value.assert_called_once_with(
        'isExhaustedAssetEnable',
    )


def test_is_exhausted_asset_enabled_none(mock_local_store):
    """Test is_exhausted_asset_enabled when value is None"""
    # Setup
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingRepository.is_exhausted_asset_enabled()

    # Assert
    assert result.is_enabled is False
    mock_local_store.get_value.assert_called_once_with(
        'isExhaustedAssetEnable',
    )


def test_is_exhausted_asset_enabled_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in is_exhausted_asset_enabled"""
    # Setup
    mock_local_store.get_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.is_exhausted_asset_enabled()

    # Assert
    assert result == 'Error handled'
    mock_local_store.get_value.assert_called_once_with(
        'isExhaustedAssetEnable',
    )
    mock_handle_exceptions.assert_called_once()


def test_enable_exhausted_asset_success_true(mock_local_store):
    """Test enable_exhausted_asset when successful and enabled"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = True

    # Execute
    result = SettingRepository.enable_exhausted_asset(True)

    # Assert
    assert result.is_enabled is True
    mock_local_store.set_value.assert_called_once_with(
        'isExhaustedAssetEnable', True,
    )
    mock_local_store.get_value.assert_called_once_with(
        'isShowHiddenAssetEnable', value_type=bool,
    )


def test_enable_exhausted_asset_success_false(mock_local_store):
    """Test enable_exhausted_asset when successful but disabled"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = False

    # Execute
    result = SettingRepository.enable_exhausted_asset(True)

    # Assert
    assert result.is_enabled is False
    mock_local_store.set_value.assert_called_once_with(
        'isExhaustedAssetEnable', True,
    )
    mock_local_store.get_value.assert_called_once_with(
        'isShowHiddenAssetEnable', value_type=bool,
    )


def test_enable_exhausted_asset_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in enable_exhausted_asset"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.enable_exhausted_asset(True)

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with(
        'isExhaustedAssetEnable', True,
    )
    mock_handle_exceptions.assert_called_once()


@patch('src.data.repository.setting_repository.sys')
def test_native_authentication_logging_disabled(mock_sys):
    """Test native_authentication when logging is disabled"""
    # Setup
    mock_auth_type = MagicMock(spec=NativeAuthType)
    mock_auth_type.value = NativeAuthType.LOGGING_TO_APP.value

    with patch.object(SettingRepository, 'native_login_enabled') as mock_native_login:
        mock_native_login.return_value = MagicMock(is_enabled=False)

        # Execute
        result = SettingRepository.native_authentication(mock_auth_type)

        # Assert
        assert result is True
        mock_native_login.assert_called_once()
        mock_sys.platform.assert_not_called()


@patch('src.data.repository.setting_repository.sys')
def test_native_authentication_major_op_disabled(mock_sys):
    """Test native_authentication when major operation auth is disabled"""
    # Setup
    mock_auth_type = MagicMock(spec=NativeAuthType)
    mock_auth_type.value = NativeAuthType.MAJOR_OPERATION.value

    with patch.object(SettingRepository, 'get_native_authentication_status') as mock_get_status:
        mock_get_status.return_value = MagicMock(is_enabled=False)

        # Execute
        result = SettingRepository.native_authentication(mock_auth_type)

        # Assert
        assert result is True
        mock_get_status.assert_called_once()
        mock_sys.platform.assert_not_called()


@patch('src.data.repository.setting_repository.sys')
def test_native_authentication_linux(mock_sys):
    """Test native_authentication on Linux platform"""
    # Setup

    mock_auth_type = MagicMock(spec=NativeAuthType)
    mock_auth_type.value = NativeAuthType.MAJOR_OPERATION.value
    mock_sys.platform = 'linux'

    with patch.object(SettingRepository, 'get_native_authentication_status') as mock_get_status:
        mock_get_status.return_value = MagicMock(is_enabled=True)
        with patch.object(SettingRepository, '_linux_native_authentication') as mock_linux_auth:
            mock_linux_auth.return_value = True

            # Execute
            result = SettingRepository.native_authentication(mock_auth_type)

            # Assert
            assert result is True
            mock_get_status.assert_called_once()
            mock_linux_auth.assert_called_once()


@patch('src.data.repository.setting_repository.sys')
def test_native_authentication_macos(mock_sys):
    """Test native_authentication on macOS platform"""
    # Setup

    mock_auth_type = MagicMock(spec=NativeAuthType)
    mock_auth_type.value = NativeAuthType.MAJOR_OPERATION.value
    mock_sys.platform = 'darwin'

    with patch.object(SettingRepository, 'get_native_authentication_status') as mock_get_status:
        mock_get_status.return_value = MagicMock(is_enabled=True)
        with patch.object(SettingRepository, '_macos_native_authentication') as mock_macos_auth:
            mock_macos_auth.return_value = True

            # Execute
            result = SettingRepository.native_authentication(mock_auth_type)

            # Assert
            assert result is True
            mock_get_status.assert_called_once()
            mock_macos_auth.assert_called_once()


@patch('src.data.repository.setting_repository.sys')
@patch('src.data.repository.setting_repository.WindowNativeAuthentication')
def test_native_authentication_windows(mock_win_auth, mock_sys):
    """Test native_authentication on Windows platform"""
    # Setup

    mock_auth_type = MagicMock(spec=NativeAuthType)
    mock_auth_type.value = NativeAuthType.MAJOR_OPERATION.value
    mock_sys.platform = 'win32'

    mock_win_auth_instance = MagicMock()
    mock_win_auth_instance.start_windows_native_auth.return_value = True
    mock_win_auth.return_value = mock_win_auth_instance

    with patch.object(SettingRepository, 'get_native_authentication_status') as mock_get_status:
        mock_get_status.return_value = MagicMock(is_enabled=True)

        # Execute
        result = SettingRepository.native_authentication(
            mock_auth_type, 'Test message',
        )

        # Assert
        assert result is True
        mock_get_status.assert_called_once()
        mock_win_auth.assert_called_once_with('Test message')
        mock_win_auth_instance.start_windows_native_auth.assert_called_once()


@patch('src.data.repository.setting_repository.sys')
def test_native_authentication_unsupported_os(mock_sys):
    """Test native_authentication on unsupported OS"""
    # Setup

    mock_auth_type = MagicMock(spec=NativeAuthType)
    mock_auth_type.value = NativeAuthType.MAJOR_OPERATION.value
    mock_sys.platform = 'unknown'

    with patch.object(SettingRepository, 'get_native_authentication_status') as mock_get_status:
        mock_get_status.return_value = MagicMock(is_enabled=True)

        # Execute
        with pytest.raises(CommonException) as exc_info:
            SettingRepository.native_authentication(mock_auth_type)

        # Assert
        assert str(exc_info.value) == 'Unsupported operating system.'
        mock_get_status.assert_called_once()


@patch('src.data.repository.setting_repository.subprocess')
def test_linux_native_authentication_success(mock_subprocess):
    """Test _linux_native_authentication when successful"""
    # Setup
    mock_subprocess.run.return_value = MagicMock()

    # Execute
    result = SettingRepository._linux_native_authentication()

    # Assert
    assert result is True
    mock_subprocess.run.assert_called_once_with(['pkexec', 'true'], check=True)


@patch('src.data.repository.setting_repository.subprocess')
def test_macos_native_authentication_success(mock_subprocess):
    """Test _macos_native_authentication when successful"""
    # Setup
    mock_subprocess.run.return_value = MagicMock()

    # Execute
    result = SettingRepository._macos_native_authentication()

    # Assert
    assert result is True
    mock_subprocess.run.assert_called_once()
    # Check that osascript is called with the correct script
    assert mock_subprocess.run.call_args[0][0][0] == 'osascript'


def test_str_to_bool_true_values():
    """Test str_to_bool with various true values"""
    # Test all possible true values
    true_values = ['true', '1', 't', 'yes', 'y', 'TRUE', 'Yes', 'Y']

    for value in true_values:
        # Execute
        result = SettingRepository.str_to_bool(value)

        # Assert
        assert result is True


def test_str_to_bool_false_values():
    """Test str_to_bool with various false values"""
    # Test all possible false values
    false_values = ['false', '0', 'f', 'no', 'n', 'FALSE', 'No', 'N']

    for value in false_values:
        # Execute
        result = SettingRepository.str_to_bool(value)

        # Assert
        assert result is False


def test_str_to_bool_none():
    """Test str_to_bool with None value"""
    # Execute
    result = SettingRepository.str_to_bool(None)

    # Assert
    assert result is False


def test_str_to_bool_invalid():
    """Test str_to_bool with invalid value raises ValueError"""
    # Execute and Assert
    with pytest.raises(ValueError, match='Cannot convert string to boolean: invalid input'):
        SettingRepository.str_to_bool('invalid')


def test_bool_to_str_true():
    """Test bool_to_str with True value"""
    # Execute
    result = SettingRepository.bool_to_str(True)

    # Assert
    assert result == 'true'


def test_bool_to_str_false():
    """Test bool_to_str with False value"""
    # Execute
    result = SettingRepository.bool_to_str(False)

    # Assert
    assert result == 'false'


@patch('src.data.repository.setting_repository.sys')
@patch('src.data.repository.setting_repository.os')
def test_get_path_windows_native_executable_frozen(mock_os, mock_sys):
    """Test _get_path_windows_native_executable when frozen"""
    # Setup
    mock_sys.frozen = True
    mock_sys._MEIPASS = '/frozen/path'
    mock_os.path.join.return_value = '/frozen/path/binary/native_auth_windows.exe'

    # Execute
    result = SettingRepository._get_path_windows_native_executable()

    # Assert
    assert result == '/frozen/path/binary/native_auth_windows.exe'
    mock_os.path.join.assert_called_once_with(
        '/frozen/path', 'binary', 'native_auth_windows.exe',
    )


@patch('src.data.repository.setting_repository.sys')
@patch('src.data.repository.setting_repository.os')
def test_get_path_windows_native_executable_not_frozen(mock_os, mock_sys):
    """Test _get_path_windows_native_executable when not frozen"""
    # Setup
    mock_sys.frozen = False
    mock_os.path.dirname.return_value = '/current/dir'
    mock_os.path.abspath.side_effect = lambda x: x if isinstance(
        x, str,
    ) else '/current/dir'
    mock_os.path.join.return_value = '/current/dir/../../../binary/native_auth_windows.exe'

    # Execute
    result = SettingRepository._get_path_windows_native_executable()

    # Assert
    assert result == '/current/dir/../../../binary/native_auth_windows.exe'


def test_get_config_value_exists(mock_local_store):
    """Test get_config_value when value exists"""
    # Setup
    mock_local_store.get_value.return_value = 'existing_value'

    # Execute
    result = SettingRepository.get_config_value('test_key', 'default_value')

    # Assert
    assert result == 'existing_value'
    mock_local_store.get_value.assert_called_once_with(
        'test_key', value_type=None,
    )
    mock_local_store.set_value.assert_not_called()


def test_get_config_value_not_exists(mock_local_store):
    """Test get_config_value when value does not exist"""
    # Setup
    mock_local_store.get_value.side_effect = [None, 'default_value']

    # Execute
    result = SettingRepository.get_config_value('test_key', 'default_value')

    # Assert
    assert result == 'default_value'
    assert mock_local_store.get_value.call_count == 2
    mock_local_store.set_value.assert_called_once_with(
        'test_key', 'default_value',
    )


def test_get_config_value_set_fails(mock_local_store):
    """Test get_config_value when setting value fails"""
    # Setup
    mock_local_store.get_value.side_effect = [None, None]

    # Execute
    result = SettingRepository.get_config_value('test_key', 'default_value')

    # Assert
    assert result is None
    assert mock_local_store.get_value.call_count == 2
    mock_local_store.set_value.assert_called_once_with(
        'test_key', 'default_value',
    )


def test_get_config_value_with_type(mock_local_store):
    """Test get_config_value with specified value_type"""
    # Setup
    mock_local_store.get_value.return_value = '123'

    # Execute
    result = SettingRepository.get_config_value(
        'test_key', '456', value_type=int,
    )

    # Assert
    assert result == '123'
    mock_local_store.get_value.assert_called_once_with(
        'test_key', value_type=int,
    )


def test_get_config_value_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling in get_config_value"""
    # Setup
    mock_local_store.get_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingRepository.get_config_value('test_key', 'default_value')

    # Assert
    assert result == 'Error handled'
    mock_local_store.get_value.assert_called_once_with(
        'test_key', value_type=None,
    )
    mock_handle_exceptions.assert_called_once()
