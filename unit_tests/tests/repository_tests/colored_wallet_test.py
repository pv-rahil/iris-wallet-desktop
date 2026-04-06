# pylint: disable=redefined-outer-name,protected-access,unused-argument
"""Unit tests for the ColoredWallet class and colored_wallet singleton."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import BitcoinNetwork
from rgb_lib import MultisigWallet
from rgb_lib import Online
from rgb_lib import RgbLibError
from rgb_lib import Wallet

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.colored_wallet import ColoredWallet
from src.model.enums.enums_model import WalletSignatureType
from src.utils.custom_exception import CommonException


@pytest.fixture
def mock_wallet():
    """Fixture providing a mock RGB wallet."""
    return MagicMock(spec=Wallet)


@pytest.fixture
def mock_online():
    """Fixture providing a mock online session."""
    return MagicMock(spec=Online)


def test_colored_wallet_initialization():
    """Test that colored_wallet is properly initialized as a singleton."""
    assert isinstance(colored_wallet, ColoredWallet)
    assert colored_wallet._wallet is None
    assert colored_wallet.online_wallet is None


def test_set_wallet(mock_wallet):
    """Test setting the wallet instance."""
    colored_wallet.set_wallet(mock_wallet)
    assert colored_wallet._wallet == mock_wallet


def test_wallet_property_not_initialized():
    """Test accessing wallet property before initialization raises exception."""
    colored_wallet._wallet = None
    with pytest.raises(CommonException, match='Wallet not initialized'):
        _ = colored_wallet.wallet


def test_wallet_property_initialized(mock_wallet):
    """Test accessing wallet property after initialization."""
    colored_wallet.set_wallet(mock_wallet)
    assert colored_wallet.wallet == mock_wallet


@patch('src.data.repository.colored_wallet.SettingRepository')
@patch('src.data.repository.colored_wallet.get_bitcoin_config')
@patch('src.data.repository.colored_wallet.get_bitcoin_network_from_enum')
def test_online_property_initialization(
    mock_get_network,
    mock_get_config,
    mock_setting_repo,
    mock_wallet,
    mock_online,
):
    """Test online property initialization."""
    # Setup mocks
    mock_setting_repo.get_wallet_network.return_value = BitcoinNetwork.TESTNET
    mock_get_network.return_value = BitcoinNetwork.TESTNET
    mock_get_config.return_value = MagicMock(indexer_url='http://test-indexer')
    mock_wallet.go_online.return_value = mock_online

    # Set wallet and test online property
    colored_wallet.set_wallet(mock_wallet)
    online = colored_wallet.online

    # Verify
    assert online == mock_online
    mock_wallet.go_online.assert_called_once_with(False, 'http://test-indexer')
    assert colored_wallet.online_wallet == mock_online


def test_go_online_again_success(mock_wallet, mock_online):
    """Test successful go_online_again call."""
    # Setup
    colored_wallet.set_wallet(mock_wallet)
    mock_wallet.go_online.return_value = mock_online

    # Execute
    colored_wallet.go_online_again('http://new-indexer')

    # Verify
    mock_wallet.go_online.assert_called_once_with(False, 'http://new-indexer')
    assert colored_wallet.online_wallet == mock_online


def test_go_online_again_error(mock_wallet):
    """Test error handling in go_online_again."""
    # Setup
    colored_wallet.set_wallet(mock_wallet)
    mock_wallet.go_online.side_effect = Exception('Test error')

    # Execute and verify
    with pytest.raises(CommonException) as exc_info:
        colored_wallet.go_online_again('http://new-indexer')

    assert 'Failed to go online again' in str(exc_info.value)
    mock_wallet.go_online.assert_called_once_with(False, 'http://new-indexer')


def test_go_online_again_no_wallet():
    """Test go_online_again when wallet is not initialized."""
    colored_wallet._wallet = None
    # Should not raise exception
    colored_wallet.go_online_again('http://new-indexer')


@patch('src.data.repository.colored_wallet.SettingRepository')
def test_online_property_no_wallet(mock_setting_repo):
    """Test online property when wallet is not initialized."""
    colored_wallet._wallet = None
    colored_wallet.online_wallet = None
    with pytest.raises(CommonException, match='Wallet must be initialized before going online.'):
        _ = colored_wallet.online


@patch('src.data.repository.colored_wallet.generate_and_store_token')
@patch('src.data.repository.colored_wallet.SettingRepository')
@patch('src.data.repository.colored_wallet.get_bitcoin_config')
@patch('src.data.repository.colored_wallet.get_bitcoin_network_from_enum')
def test_online_property_multisig(
    mock_get_network,
    mock_get_config,
    mock_setting_repo,
    mock_generate_token,
    mock_online,
):
    """Test online property for multisig wallet."""
    # Setup mocks
    mock_setting_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_setting_repo.get_wallet_network.return_value = BitcoinNetwork.TESTNET
    mock_get_network.return_value = BitcoinNetwork.TESTNET
    mock_get_config.return_value = MagicMock(indexer_url='http://test-indexer')
    mock_generate_token.return_value = 'test-token'

    # Mock MultisigWallet
    mock_multisig_wallet = MagicMock(spec=MultisigWallet)
    mock_multisig_wallet.go_online.return_value = mock_online

    # Set wallet and test online property
    colored_wallet.set_wallet(mock_multisig_wallet)
    colored_wallet.online_wallet = None
    online = colored_wallet.online

    # Verify
    assert online == mock_online
    mock_generate_token.assert_called_once()
    mock_multisig_wallet.go_online.assert_called_once()
    assert colored_wallet.online_wallet == mock_online


@patch('src.data.repository.colored_wallet.SettingRepository')
def test_online_property_exception(mock_setting_repo):
    """Test exception handling in online property."""
    mock_wallet = MagicMock(spec=Wallet)
    mock_setting_repo.get_wallet_network.side_effect = Exception(
        'Unexpected error',
    )

    colored_wallet.set_wallet(mock_wallet)
    colored_wallet.online_wallet = None
    with pytest.raises(CommonException, match='Failed to initialize online session'):
        _ = colored_wallet.online


@patch('src.data.repository.colored_wallet.generate_and_store_token')
def test_go_online_again_multisig(mock_generate_token, mock_online):
    """Test go_online_again for multisig wallet."""
    mock_multisig_wallet = MagicMock(spec=MultisigWallet)
    mock_multisig_wallet.go_online.return_value = mock_online
    mock_generate_token.return_value = 'test-token'

    colored_wallet.set_wallet(mock_multisig_wallet)
    # mock is_multisig check
    with patch.object(ColoredWallet, 'is_multisig', return_value=True):
        colored_wallet.go_online_again('http://new-indexer')

    mock_generate_token.assert_called_once()
    mock_multisig_wallet.go_online.assert_called_once()


@patch('src.data.repository.colored_wallet.generate_and_store_token')
def test_go_online_again_multisig_no_token(mock_generate_token):
    """Test go_online_again for multisig when token generation fails."""
    mock_multisig_wallet = MagicMock(spec=MultisigWallet)
    mock_generate_token.return_value = None

    colored_wallet.set_wallet(mock_multisig_wallet)
    # mock is_multisig check
    with patch.object(ColoredWallet, 'is_multisig', return_value=True):
        with pytest.raises(CommonException, match='Failed to go online again') as exc_info:
            colored_wallet.go_online_again('http://new-indexer')
        assert 'Failed to generate bridge token' in str(
            exc_info.value.__cause__,
        )


def test_go_online_again_invalid_indexer():
    """Test go_online_again with InvalidIndexer exception."""
    mock_wallet = MagicMock(spec=Wallet)
    mock_wallet.go_online.side_effect = RgbLibError.InvalidIndexer(
        'Invalid indexer',
    )

    colored_wallet.set_wallet(mock_wallet)
    with pytest.raises(RgbLibError.InvalidIndexer):
        colored_wallet.go_online_again('http://invalid-indexer')


@patch('src.data.repository.colored_wallet.SettingRepository')
def test_is_multisig_logic(mock_setting_repo):
    """Test is_multisig property logic."""
    # Case 1: Wallet is set and is standard Wallet
    mock_wallet = MagicMock(spec=Wallet)
    colored_wallet.set_wallet(mock_wallet)
    assert colored_wallet.is_multisig is False

    # Case 2: Wallet is set and is MultisigWallet
    mock_multisig_wallet = MagicMock(spec=MultisigWallet)
    colored_wallet.set_wallet(mock_multisig_wallet)
    assert colored_wallet.is_multisig is True

    # Case 3: Wallet is NOT set, check SettingRepository
    colored_wallet._wallet = None
    mock_setting_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    assert colored_wallet.is_multisig is True

    mock_setting_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    assert colored_wallet.is_multisig is False
