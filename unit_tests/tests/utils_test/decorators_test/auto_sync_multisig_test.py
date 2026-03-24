"""
Unit tests for `src/utils/decorators/auto_sync_multisig.py`.
"""
from unittest.mock import MagicMock
from unittest.mock import patch
import pytest

from src.utils.decorators.auto_sync_multisig import auto_sync_multisig
from src.utils.decorators.auto_sync_multisig import is_blocking_operation
from src.utils.custom_exception import CommonException
from src.model.enums.enums_model import WalletType

def test_is_blocking_operation():
    """Test is_blocking_operation helper function."""
    # Mock various Operation types
    op = MagicMock()
    
    # Test each branch
    op.is_CREATE_UTXOS_TO_REVIEW.return_value = True
    assert is_blocking_operation(op) is True
    op.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    
    op.is_CREATE_UTXOS_PENDING.return_value = True
    assert is_blocking_operation(op) is True
    op.is_CREATE_UTXOS_PENDING.return_value = False
    
    op.is_SEND_BTC_TO_REVIEW.return_value = True
    assert is_blocking_operation(op) is True
    op.is_SEND_BTC_TO_REVIEW.return_value = False
    
    op.is_SEND_BTC_PENDING.return_value = True
    assert is_blocking_operation(op) is True
    op.is_SEND_BTC_PENDING.return_value = False
    
    op.is_SEND_TO_REVIEW.return_value = True
    assert is_blocking_operation(op) is True
    op.is_SEND_TO_REVIEW.return_value = False
    
    op.is_SEND_PENDING.return_value = True
    assert is_blocking_operation(op) is True
    op.is_SEND_PENDING.return_value = False
    
    op.is_INFLATION_TO_REVIEW.return_value = True
    assert is_blocking_operation(op) is True
    op.is_INFLATION_TO_REVIEW.return_value = False
    
    op.is_INFLATION_PENDING.return_value = True
    assert is_blocking_operation(op) is True
    
    # All False
    op.is_INFLATION_PENDING.return_value = False
    assert is_blocking_operation(op) is False

@patch('src.utils.decorators.auto_sync_multisig.colored_wallet')
def test_decorator_not_multisig(mock_colored_wallet):
    """Test decorator when wallet is not multisig."""
    mock_colored_wallet.is_multisig = False
    
    @auto_sync_multisig()
    def my_method():
        return "success"
    
    assert my_method() == "success"
    mock_colored_wallet.wallet.sync_with_bridge.assert_not_called()

@patch('src.utils.decorators.auto_sync_multisig.SettingRepository')
@patch('src.utils.decorators.auto_sync_multisig.colored_wallet')
def test_decorator_multisig_offline(mock_colored_wallet, mock_setting_repo):
    """Test decorator when wallet is multisig but offline."""
    mock_colored_wallet.is_multisig = True
    mock_setting_repo.get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    
    @auto_sync_multisig()
    def my_method():
        return "success"
    
    assert my_method() == "success"
    mock_colored_wallet.wallet.sync_with_bridge.assert_not_called()

@patch('src.utils.decorators.auto_sync_multisig.SettingRepository')
@patch('src.utils.decorators.auto_sync_multisig.colored_wallet')
def test_decorator_multisig_online_success(mock_colored_wallet, mock_setting_repo):
    """Test decorator when wallet is multisig and online, sync succeeds."""
    mock_colored_wallet.is_multisig = True
    mock_setting_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_colored_wallet.online = True
    mock_colored_wallet.wallet.sync_with_bridge.return_value = None
    
    @auto_sync_multisig()
    def my_method():
        return "success"
    
    assert my_method() == "success"
    mock_colored_wallet.wallet.sync_with_bridge.assert_called_once_with(online=True)

@patch('src.utils.decorators.auto_sync_multisig.SettingRepository')
@patch('src.utils.decorators.auto_sync_multisig.colored_wallet')
def test_decorator_multisig_online_pending_blocking(mock_colored_wallet, mock_setting_repo):
    """Test decorator when wallet is multisig and online, but has pending operations."""
    mock_colored_wallet.is_multisig = True
    mock_setting_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    
    mock_sync_result = MagicMock()
    mock_colored_wallet.wallet.sync_with_bridge.return_value = mock_sync_result
    
    @auto_sync_multisig(check_pending_ops=True)
    def my_method():
        return "success"
    
    with pytest.raises(CommonException) as excinfo:
        my_method()
    
    assert "A multisig operation is already pending" in str(excinfo.value)

@patch('src.utils.decorators.auto_sync_multisig.SettingRepository')
@patch('src.utils.decorators.auto_sync_multisig.colored_wallet')
def test_decorator_sync_error(mock_colored_wallet, mock_setting_repo):
    """Test decorator when sync with bridge fails."""
    mock_colored_wallet.is_multisig = True
    mock_setting_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    
    mock_colored_wallet.wallet.sync_with_bridge.side_effect = Exception("sync failed")
    
    @auto_sync_multisig()
    def my_method():
        return "success"
    
    with pytest.raises(CommonException) as excinfo:
        my_method()
    
    assert "Failed to sync with bridge" in str(excinfo.value)

@patch('src.utils.decorators.auto_sync_multisig.SettingRepository')
@patch('src.utils.decorators.auto_sync_multisig.colored_wallet')
def test_decorator_common_exception_passthrough(mock_colored_wallet, mock_setting_repo):
    """Test decorator when CommonException is raised during sync."""
    mock_colored_wallet.is_multisig = True
    mock_setting_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    
    mock_colored_wallet.wallet.sync_with_bridge.side_effect = CommonException("specific error")
    
    @auto_sync_multisig()
    def my_method():
        return "success"
    
    with pytest.raises(CommonException) as excinfo:
        my_method()
    
    assert "specific error" in str(excinfo.value)
