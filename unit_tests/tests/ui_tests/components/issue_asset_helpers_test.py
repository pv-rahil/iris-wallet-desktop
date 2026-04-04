"""Unit tests for issue_asset_helpers."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.views.components.issue_asset_helpers import compute_needed_utxos
from src.views.components.issue_asset_helpers import create_utxos_for_issue
from src.views.components.issue_asset_helpers import get_wallet_type_flags
from src.views.components.issue_asset_helpers import show_multisig_psbt_toast_and_close
from src.views.components.issue_asset_helpers import show_utxo_confirmation_dialog


def test_get_wallet_type_flags_returns_multisig_and_offline():
    """Test get_wallet_type_flags returns correct flags."""
    # Setup
    with patch('src.views.components.issue_asset_helpers.SettingRepository') as mock_repo:
        mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
        mock_repo.get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET

        # Execute
        is_multisig, is_offline = get_wallet_type_flags()

        # Assert
        assert is_multisig is True
        assert is_offline is True


def test_get_wallet_type_flags_returns_standard_and_online():
    """Test get_wallet_type_flags returns standard wallet flags."""
    # Setup
    with patch('src.views.components.issue_asset_helpers.SettingRepository') as mock_repo:
        mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
        mock_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET

        # Execute
        is_multisig, is_offline = get_wallet_type_flags()

        # Assert
        assert is_multisig is False
        assert is_offline is False


@patch('src.views.components.issue_asset_helpers.ToastManager.success')
@patch('src.views.components.issue_asset_helpers.QCoreApplication.translate')
def test_show_multisig_psbt_toast_and_close(mock_translate, mock_toast):
    """Test show_multisig_psbt_toast_and_close shows toast and calls callback."""
    # Setup
    mock_translate.return_value = 'PSBT created successfully'
    close_callback = MagicMock()

    # Execute
    show_multisig_psbt_toast_and_close(close_callback)

    # Assert
    mock_toast.assert_called_once()
    close_callback.assert_called_once()


def test_show_utxo_confirmation_dialog_returns_false_when_active():
    """Test show_utxo_confirmation_dialog returns False when dialog already active."""
    # Setup
    parent = MagicMock()
    set_dialog_active = MagicMock()

    # Execute
    should_proceed, dialog_shown = show_utxo_confirmation_dialog(
        parent, dialog_active=True, set_dialog_active=set_dialog_active,
    )

    # Assert
    assert should_proceed is False
    assert dialog_shown is False


@patch('src.views.components.issue_asset_helpers.SettingRepository')
def test_show_utxo_confirmation_dialog_returns_true_for_standard_wallet(mock_repo):
    """Test show_utxo_confirmation_dialog returns True for standard wallet."""
    # Setup
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
    parent = MagicMock()
    set_dialog_active = MagicMock()

    # Execute
    should_proceed, dialog_shown = show_utxo_confirmation_dialog(
        parent, dialog_active=False, set_dialog_active=set_dialog_active,
    )

    # Assert
    assert should_proceed is True
    assert dialog_shown is False


def test_create_utxos_for_issue_returns_false_when_not_accepted():
    """Test create_utxos_for_issue returns False when dialog not accepted."""
    # Setup
    parent = MagicMock()
    utxo_viewmodel = MagicMock()
    set_dialog_active = MagicMock()

    with patch(
        'src.views.components.issue_asset_helpers.show_utxo_confirmation_dialog',
        return_value=(False, True),
    ):
        # Execute
        result = create_utxos_for_issue(
            parent, 'issue_asset_cfa', utxo_viewmodel, False, set_dialog_active,
        )

        # Assert
        assert result is False
        utxo_viewmodel.create_utxos_begin.assert_not_called()


def test_create_utxos_for_issue_creates_utxos_when_accepted():
    """Test create_utxos_for_issue creates UTXOs when accepted."""
    # Setup
    parent = MagicMock()
    utxo_viewmodel = MagicMock()
    set_dialog_active = MagicMock()

    with patch(
        'src.views.components.issue_asset_helpers.show_utxo_confirmation_dialog',
        return_value=(True, True),
    ):
        # Execute
        result = create_utxos_for_issue(
            parent, 'issue_asset_cfa', utxo_viewmodel, False, set_dialog_active,
        )

        # Assert
        assert result is True
        utxo_viewmodel.create_utxos_begin.assert_called_once_with(
            'issue_asset_cfa', 1,
        )


def test_compute_needed_utxos_returns_correct_value():
    """Test compute_needed_utxos returns correct value."""
    # Execute & Assert
    assert compute_needed_utxos(0, 1) == 1
    assert compute_needed_utxos(0, 3) == 3
    assert compute_needed_utxos(2, 3) == 1
    assert compute_needed_utxos(3, 3) == 1  # minimum 1
    assert compute_needed_utxos(5, 3) == 1  # minimum 1
