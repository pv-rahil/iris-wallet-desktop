"""Unit tests for ui_helpers."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import patch

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.views.components.ui_helpers import create_empty_state_widget
from src.views.components.ui_helpers import get_wallet_type_flags
from src.views.components.ui_helpers import WalletTypeFlags


@patch('src.views.components.ui_helpers.SettingRepository')
def test_get_wallet_type_flags_returns_correct_flags(mock_repo):
    """Test get_wallet_type_flags returns correct WalletTypeFlags."""
    # Setup
    mock_repo.get_key_storage_type.return_value = KeyStorageType.HARDWARE_WALLET
    mock_repo.get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WATCH_ONLY
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET

    # Execute
    flags = get_wallet_type_flags()

    # Assert
    assert isinstance(flags, WalletTypeFlags)
    assert flags.is_hardware_wallet is True
    assert flags.is_offline_wallet is True
    assert flags.is_watch_only is True
    assert flags.is_multisig is True


@patch('src.views.components.ui_helpers.SettingRepository')
def test_get_wallet_type_flags_returns_false_for_standard_wallet(mock_repo):
    """Test get_wallet_type_flags returns False flags for standard wallet."""
    # Setup
    mock_repo.get_key_storage_type.return_value = KeyStorageType.ON_DEVICE
    mock_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET

    # Execute
    flags = get_wallet_type_flags()

    # Assert
    assert flags.is_hardware_wallet is False
    assert flags.is_offline_wallet is False
    assert flags.is_watch_only is False
    assert flags.is_multisig is False


@patch('src.views.components.ui_helpers.QCoreApplication.translate')
def test_create_empty_state_widget_creates_frame(mock_translate):
    """Test create_empty_state_widget creates frame and button."""
    # Setup
    mock_translate.return_value = 'translated_text'

    # Execute
    frame, button = create_empty_state_widget(
        button_text_key='issue_asset',
        button_accessible_name='issue_button',
        parent=None,
        transparent=False,
    )

    # Assert
    assert frame is not None
    assert button is not None
    assert frame.minimumWidth() == 680
    assert button.minimumWidth() == 200
