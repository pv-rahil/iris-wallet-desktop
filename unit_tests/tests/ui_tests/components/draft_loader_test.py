"""Unit tests for draft_loader."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.views.components.draft_loader import load_secondary_issuance_drafts
from src.views.components.draft_loader import load_transfer_draft


def test_load_transfer_draft_returns_unchanged_for_offline_wallet():
    """Test load_transfer_draft returns unchanged index for offline wallet."""
    # Setup
    with patch('src.views.components.draft_loader.SettingRepository') as mock_repo:
        mock_repo.get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
        scroll_contents = MagicMock()
        scroll_layout = MagicMock()
        view_model = MagicMock()

        # Execute
        result = load_transfer_draft(
            'asset_id', 0, scroll_contents, scroll_layout, view_model,
        )

        # Assert
        assert result == 0


def test_load_transfer_draft_returns_unchanged_when_no_session():
    """Test load_transfer_draft returns unchanged index when no session."""
    # Setup
    with patch('src.views.components.draft_loader.SettingRepository') as mock_repo, \
            patch('src.views.components.draft_loader.WalletDataService') as mock_svc:
        mock_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
        mock_svc.get_session.return_value = None
        scroll_contents = MagicMock()
        scroll_layout = MagicMock()
        view_model = MagicMock()

        # Execute
        result = load_transfer_draft(
            'asset_id', 0, scroll_contents, scroll_layout, view_model,
        )

        # Assert
        assert result == 0


def test_load_transfer_draft_returns_unchanged_when_no_draft():
    """Test load_transfer_draft returns unchanged index when no draft."""
    # Setup
    with patch('src.views.components.draft_loader.SettingRepository') as mock_repo, \
            patch('src.views.components.draft_loader.WalletDataService') as mock_svc:
        mock_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
        mock_session = MagicMock()
        mock_session.get_draft_transfer.return_value = None
        mock_svc.get_session.return_value = mock_session
        scroll_contents = MagicMock()
        scroll_layout = MagicMock()
        view_model = MagicMock()

        # Execute
        result = load_transfer_draft(
            'asset_id', 0, scroll_contents, scroll_layout, view_model,
        )

        # Assert
        assert result == 0


def test_load_secondary_issuance_drafts_returns_unchanged_for_standard_wallet():
    """Test load_secondary_issuance_drafts returns unchanged for standard wallet."""
    # Setup
    with patch('src.views.components.draft_loader.SettingRepository') as mock_repo:
        mock_repo.get_wallet_access_type.return_value = WalletAccessType.WITH_PRIVATE_KEY
        mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
        scroll_contents = MagicMock()
        scroll_layout = MagicMock()
        view_model = MagicMock()

        # Execute
        result = load_secondary_issuance_drafts(
            'asset_id', '/path/to/image', 0, scroll_contents, scroll_layout, view_model,
        )

        # Assert
        assert result == 0


def test_load_secondary_issuance_drafts_returns_unchanged_when_no_session():
    """Test load_secondary_issuance_drafts returns unchanged when no session."""
    # Setup
    with patch('src.views.components.draft_loader.SettingRepository') as mock_repo, \
            patch('src.views.components.draft_loader.WalletDataService') as mock_svc:
        mock_repo.get_wallet_access_type.return_value = WalletAccessType.WATCH_ONLY
        mock_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
        mock_repo.get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
        mock_svc.get_session.return_value = None
        scroll_contents = MagicMock()
        scroll_layout = MagicMock()
        view_model = MagicMock()

        # Execute
        result = load_secondary_issuance_drafts(
            'asset_id', '/path/to/image', 0, scroll_contents, scroll_layout, view_model,
        )

        # Assert
        assert result == 0
