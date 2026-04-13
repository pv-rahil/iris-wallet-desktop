"""Unit tests for ifa_hw_helpers."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.views.components.ifa_hw_helpers import close_hw_dialog_if_open
from src.views.components.ifa_hw_helpers import delete_active_secondary_draft_on_success
from src.views.components.ifa_hw_helpers import handle_success_dialog
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


@patch('src.views.components.ifa_hw_helpers.compute_needed_utxos_for_ifa')
@patch('src.views.components.ifa_hw_helpers.SettingRepository')
def test_handle_utxo_error_creates_utxos_for_multisig(mock_repo, mock_compute_utxos):
    """Test handle_utxo_error creates UTXOs for multisig wallet."""
    # Setup
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
    mock_compute_utxos.return_value = 2
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


@patch('src.views.components.ifa_hw_helpers.compute_needed_utxos_for_ifa')
@patch('src.views.components.ifa_hw_helpers.SettingRepository')
def test_handle_utxo_error_sets_retry_for_secondary_issuance(mock_repo, mock_compute_utxos):
    """Test handle_utxo_error sets retry flag for secondary issuance."""
    # Setup
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
    mock_compute_utxos.return_value = 3
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


@patch('src.views.components.ifa_hw_helpers.SettingRepository')
def test_handle_utxo_error_dialog_rejected(mock_repo):
    """Test handle_utxo_error when dialog is rejected."""
    mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
    parent = MagicMock()
    utxo_viewmodel = MagicMock()

    with patch('src.views.components.ifa_hw_helpers.ConfirmationDialog') as mock_dialog:
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.exec.return_value = 0  # QDialog.Rejected
        mock_dialog.return_value = mock_dialog_instance

        handled, retry = handle_utxo_error(
            message='NoAvailableUtxos',
            parent_widget=parent,
            utxo_dialog_active=False,
            secondary_issuance=False,
            utxo_creation_view_model=utxo_viewmodel,
        )

        assert handled is True
        assert retry is False
        utxo_viewmodel.create_utxos_begin.assert_not_called()


@patch('src.views.components.ifa_hw_helpers.WalletDataService')
def test_handle_success_dialog_visible(mock_wallet_service):
    """Test handle_success_dialog when dialog is visible."""
    mock_dialog = MagicMock()
    mock_dialog.isVisible.return_value = True

    params = MagicMock()
    params.asset_id = 'asset123'

    result = handle_success_dialog(
        ifa_hw_dialog=mock_dialog,
        secondary_issuance=False,
        params=params,
    )

    assert result is True
    mock_dialog.accept.assert_called_once()


@patch('src.views.components.ifa_hw_helpers.WalletDataService')
def test_handle_success_dialog_secondary_issuance(mock_wallet_service):
    """Test handle_success_dialog for secondary issuance."""
    mock_dialog = MagicMock()
    mock_dialog.isVisible.return_value = False

    mock_session = MagicMock()
    mock_session.get_active_secondary_draft_for_asset.return_value = {
        'id': '42',
    }
    mock_wallet_service.get_session.return_value = mock_session

    params = MagicMock()
    params.asset_id = 'asset123'

    result = handle_success_dialog(
        ifa_hw_dialog=mock_dialog,
        secondary_issuance=True,
        params=params,
    )

    assert result is True
    mock_session.delete_ifa_secondary_draft.assert_called_once_with(42)


@patch('src.views.components.ifa_hw_helpers.WalletDataService')
def test_handle_success_dialog_no_session(mock_wallet_service):
    """Test handle_success_dialog when no session available."""
    mock_dialog = MagicMock()
    mock_dialog.isVisible.return_value = False
    mock_wallet_service.get_session.return_value = None

    params = MagicMock()
    params.asset_id = 'asset123'

    result = handle_success_dialog(
        ifa_hw_dialog=mock_dialog,
        secondary_issuance=True,
        params=params,
    )

    assert result is True


@patch('src.views.components.ifa_hw_helpers.WalletDataService')
def test_handle_success_dialog_exception(mock_wallet_service):
    """Test handle_success_dialog handles exceptions gracefully."""
    mock_dialog = MagicMock()
    mock_dialog.isVisible.return_value = False
    mock_wallet_service.get_session.side_effect = Exception('test error')

    params = MagicMock()
    params.asset_id = 'asset123'

    result = handle_success_dialog(
        ifa_hw_dialog=mock_dialog,
        secondary_issuance=True,
        params=params,
    )

    assert result is True


@patch('src.views.components.ifa_hw_helpers.HardwareWalletOperationDialog')
def test_close_hw_dialog_if_open_visible(mock_hw_dialog_class):
    """Test close_hw_dialog_if_open when dialog is visible."""
    mock_dialog = MagicMock()
    mock_dialog.isVisible.return_value = True
    mock_hw_dialog_class.get_instance.return_value = mock_dialog

    parent = MagicMock()
    close_hw_dialog_if_open(parent)

    mock_dialog.accept.assert_called_once()


@patch('src.views.components.ifa_hw_helpers.HardwareWalletOperationDialog')
def test_close_hw_dialog_if_open_not_visible(mock_hw_dialog_class):
    """Test close_hw_dialog_if_open when dialog is not visible."""
    mock_dialog = MagicMock()
    mock_dialog.isVisible.return_value = False
    mock_hw_dialog_class.get_instance.return_value = mock_dialog

    parent = MagicMock()
    close_hw_dialog_if_open(parent)

    mock_dialog.accept.assert_not_called()


@patch('src.views.components.ifa_hw_helpers.WalletDataService')
def test_delete_active_secondary_draft_on_success(mock_wallet_service):
    """Test delete_active_secondary_draft_on_success deletes draft."""
    mock_session = MagicMock()
    mock_session.get_active_secondary_draft_for_asset.return_value = {
        'id': '99',
    }
    mock_wallet_service.get_session.return_value = mock_session

    params = MagicMock()
    params.asset_id = 'asset123'

    delete_active_secondary_draft_on_success(
        secondary_issuance=True,
        params=params,
    )

    mock_session.delete_ifa_secondary_draft.assert_called_once_with(99)


def test_delete_active_secondary_draft_on_success_not_secondary():
    """Test delete_active_secondary_draft_on_success returns early if not secondary."""
    params = MagicMock()

    delete_active_secondary_draft_on_success(
        secondary_issuance=False,
        params=params,
    )


def test_delete_active_secondary_draft_on_success_no_params():
    """Test delete_active_secondary_draft_on_success returns early if no params."""
    delete_active_secondary_draft_on_success(
        secondary_issuance=True,
        params=None,
    )


def test_delete_active_secondary_draft_on_success_no_asset_id():
    """Test delete_active_secondary_draft_on_success returns early if no asset_id."""
    params = MagicMock()
    params.asset_id = None

    delete_active_secondary_draft_on_success(
        secondary_issuance=True,
        params=params,
    )


@patch('src.views.components.ifa_hw_helpers.WalletDataService')
def test_delete_active_secondary_draft_on_success_no_session(mock_wallet_service):
    """Test delete_active_secondary_draft_on_success returns early if no session."""
    mock_wallet_service.get_session.return_value = None

    params = MagicMock()
    params.asset_id = 'asset123'

    delete_active_secondary_draft_on_success(
        secondary_issuance=True,
        params=params,
    )


@patch('src.views.components.ifa_hw_helpers.WalletDataService')
def test_delete_active_secondary_draft_on_success_no_draft(mock_wallet_service):
    """Test delete_active_secondary_draft_on_success when no active draft."""
    mock_session = MagicMock()
    mock_session.get_active_secondary_draft_for_asset.return_value = None
    mock_wallet_service.get_session.return_value = mock_session

    params = MagicMock()
    params.asset_id = 'asset123'

    delete_active_secondary_draft_on_success(
        secondary_issuance=True,
        params=params,
    )

    mock_session.delete_ifa_secondary_draft.assert_not_called()
