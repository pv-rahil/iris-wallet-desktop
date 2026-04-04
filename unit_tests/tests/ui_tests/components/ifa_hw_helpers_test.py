"""Unit tests for ifa_hw_helpers."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.views.components.ifa_hw_helpers import handle_utxo_error


def test_handle_utxo_error_returns_false_for_unrelated_error():
    """Test handle_utxo_error returns False for unrelated error message."""
    # Setup
    parent = MagicMock()
    utxo_viewmodel = MagicMock()

    # Execute
    handled, retry = handle_utxo_error(
        message='Some other error',
        parent_widget=parent,
        utxo_dialog_active=False,
        secondary_issuance=False,
        utxo_creation_view_model=utxo_viewmodel,
    )

    # Assert
    assert handled is False
    assert retry is False


@patch('src.views.components.ifa_hw_helpers.get_unspent_utxo_count')
@patch('src.views.components.ifa_hw_helpers.SettingRepository')
def test_handle_utxo_error_creates_utxos_for_multisig(mock_repo, mock_get_count):
    """Test handle_utxo_error creates UTXOs for multisig wallet."""
    # Setup
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
    mock_get_count.return_value = 0
    parent = MagicMock()
    utxo_viewmodel = MagicMock()

    with patch('src.views.components.ifa_hw_helpers.ConfirmationDialog') as mock_dialog:
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.exec.return_value = 1  # QDialog.Accepted
        mock_dialog.return_value = mock_dialog_instance

        # Execute
        handled, retry = handle_utxo_error(
            message='NoAvailableUtxos',
            parent_widget=parent,
            utxo_dialog_active=False,
            secondary_issuance=False,
            utxo_creation_view_model=utxo_viewmodel,
        )

        # Assert
        assert handled is True
        assert retry is False
        utxo_viewmodel.create_utxos_begin.assert_called_once()


@patch('src.views.components.ifa_hw_helpers.get_unspent_utxo_count')
@patch('src.views.components.ifa_hw_helpers.SettingRepository')
def test_handle_utxo_error_sets_retry_for_secondary_issuance(mock_repo, mock_get_count):
    """Test handle_utxo_error sets retry flag for secondary issuance."""
    # Setup
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
    mock_get_count.return_value = 0
    parent = MagicMock()
    utxo_viewmodel = MagicMock()

    # Execute
    handled, retry = handle_utxo_error(
        message='NoAvailableUtxos',
        parent_widget=parent,
        utxo_dialog_active=False,
        secondary_issuance=True,
        utxo_creation_view_model=utxo_viewmodel,
    )

    # Assert
    assert handled is True
    assert retry is True


def test_handle_utxo_error_returns_true_when_dialog_active():
    """Test handle_utxo_error returns True when dialog already active for multisig."""
    # Setup
    with patch('src.views.components.ifa_hw_helpers.SettingRepository') as mock_repo:
        mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
        mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
        parent = MagicMock()
        utxo_viewmodel = MagicMock()

        # Execute
        handled, retry = handle_utxo_error(
            message='NoAvailableUtxos',
            parent_widget=parent,
            utxo_dialog_active=True,
            secondary_issuance=False,
            utxo_creation_view_model=utxo_viewmodel,
        )

        # Assert
        assert handled is True
        assert retry is False
