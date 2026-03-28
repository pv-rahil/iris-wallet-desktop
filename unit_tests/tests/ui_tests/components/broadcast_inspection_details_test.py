# pylint: disable=redefined-outer-name, protected-access
"""Unit tests for the BroadcastInspectionDetails component."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import WalletType
from src.views.components.broadcast_inspection_details import BroadcastInspectionDetails


@pytest.fixture
def inspection_details(qtbot):
    """Fixture to create and return the BroadcastInspectionDetails widget."""
    widget = BroadcastInspectionDetails()
    qtbot.addWidget(widget)
    return widget


def test_initial_state(inspection_details):
    """Test the initial state of the component."""
    assert inspection_details._is_multisig is False
    assert inspection_details._is_watch_only is False
    assert inspection_details._can_broadcast is False
    assert inspection_details.details_title.isHidden()
    assert inspection_details.details_card.isHidden()


def test_show_inspection_details(inspection_details):
    """Test the show_inspection_details method of BroadcastInspectionDetails."""
    inspection_details.show_inspection_details(True)
    assert not inspection_details.details_title.isHidden()
    assert not inspection_details.details_card.isHidden()

    inspection_details.show_inspection_details(False)
    assert inspection_details.details_title.isHidden()
    assert inspection_details.details_card.isHidden()


def test_set_config_single_sig(inspection_details):
    """Test the set_config method of BroadcastInspectionDetails for single signature wallet."""
    inspection_details.set_config(
        is_multisig=False, is_watch_only=False, can_broadcast=True,
    )
    assert inspection_details._is_multisig is False
    assert inspection_details._is_watch_only is False
    assert inspection_details._can_broadcast is True
    assert not inspection_details.btn_primary.isHidden()
    assert inspection_details.btn_import.isHidden()


def test_set_config_layout_wipe(inspection_details):
    """Test the set_config method of BroadcastInspectionDetails for layout wipe."""
    inspection_details.set_config(
        is_multisig=False, is_watch_only=False, can_broadcast=True,
    )
    # Add a stretch to trigger the "else" branch of removeItem
    inspection_details.actions_layout.addStretch(1)
    inspection_details.set_config(
        is_multisig=True, is_watch_only=True, can_broadcast=False,
    )
    assert inspection_details._is_multisig is True


def test_set_config_multisig(inspection_details):
    """Test the set_config method of BroadcastInspectionDetails for multisignature wallet."""
    inspection_details.set_config(
        is_multisig=True, is_watch_only=True, can_broadcast=False,
    )
    assert inspection_details._is_multisig is True
    assert not inspection_details.btn_import.isHidden()
    assert not inspection_details.btn_reject.isHidden()
    assert not inspection_details.btn_primary.isHidden()


def test_set_multisig(inspection_details):
    """Test the set_multisig method of BroadcastInspectionDetails."""
    inspection_details.set_multisig(True)
    assert inspection_details._is_multisig is True


def test_wrap_to_two_lines():
    """Test the _wrap_to_two_lines static method of BroadcastInspectionDetails."""
    assert BroadcastInspectionDetails._wrap_to_two_lines(
        'short string',
    ) == 'short string'
    long_string = 'a' * 40
    wrapped = BroadcastInspectionDetails._wrap_to_two_lines(long_string, 34)
    assert wrapped == 'a' * 34 + '\n' + 'a' * 6
    assert BroadcastInspectionDetails._wrap_to_two_lines(None) == 'None'


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_update_psbt_details_offline(mock_wt, inspection_details):
    """Test the update_psbt_details method of BroadcastInspectionDetails for offline wallet."""
    mock_wt.return_value = WalletType.OFFLINE_TYPE_WALLET
    details = MagicMock()
    details.txid = 'some_txid'
    details.fee_sat = 1500

    with patch('src.views.components.broadcast_inspection_details.set_widgets_visible') as mock_set_vis:
        inspection_details.update_psbt_details(details, False, False, None)
        assert inspection_details.val_txid.text() == 'some_txid'
        assert inspection_details.val_fee.text() == '1,500 sats'
        assert not inspection_details.tile_fee.isHidden()
        mock_set_vis.assert_called()


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_update_psbt_details_rgb(mock_wt, inspection_details):
    """Test the update_psbt_details method of BroadcastInspectionDetails for RGB wallet."""
    mock_wt.return_value = WalletType.ONLINE_TYPE_WALLET
    details = MagicMock()
    details.txid = 'a_very_long_txid_' * 5
    details.fee_sat = -1  # hide fee

    with patch('src.data.service.broadcast_transaction_service.BroadcastTransactionService.get_transfer_type_label') as mock_lbl:
        mock_lbl.return_value = 'Send RGB'
        with patch('src.views.components.broadcast_inspection_details.set_widgets_visible') as mock_set_vis:
            inspection_details.update_psbt_details(
                details, False, True, 'pending_key',
            )
            assert inspection_details.tile_fee.isHidden()
            assert inspection_details.val_transfer_type.text() == 'Send RGB'
            assert not inspection_details.tile_ttype.isHidden()
            # Cover wrap to two lines
            assert '\\n' in repr(inspection_details.val_txid.text())
            mock_set_vis.assert_called()


def test_update_rgb_details(inspection_details):
    """Test the update_rgb_details method of BroadcastInspectionDetails."""
    # Hide amount, show nothing
    inspection_details.update_rgb_details(None, 0, None, None)
    assert inspection_details.tile_asset.isHidden()
    assert inspection_details.tile_minconf.isHidden()

    # Show specifics
    inspection_details._rgb_expected = True
    inspection_details.update_rgb_details('asset_123', 50, 'Receive', 2)
    assert not inspection_details.tile_asset.isHidden()
    assert inspection_details.val_asset_id.text() == 'asset_123'
    assert not inspection_details.tile_amount.isHidden()
    assert inspection_details.val_amount.text() == '50'
    assert not inspection_details.tile_ttype.isHidden()
    assert inspection_details.val_transfer_type.text() == 'Receive'
    assert not inspection_details.tile_minconf.isHidden()
    assert inspection_details.val_min_conf.text() == '2'


def test_update_transfer_type_label(inspection_details):
    """Test the update_transfer_type_label method of BroadcastInspectionDetails."""
    inspection_details.update_transfer_type_label('Test Label')
    assert not inspection_details.tile_ttype.isHidden()
    assert inspection_details.val_transfer_type.text() == 'Test Label'

    inspection_details.update_transfer_type_label('')
    assert inspection_details.tile_ttype.isHidden()


def test_retranslate_ui(inspection_details):
    """Test the retranslate_ui method of BroadcastInspectionDetails."""
    inspection_details._can_broadcast = True
    inspection_details.retranslate_ui()
    assert inspection_details.btn_primary.text() == 'broadcast_transaction'

    inspection_details._can_broadcast = False
    inspection_details.retranslate_ui()
    assert inspection_details.btn_primary.text() == 'sign_psbt'

    inspection_details.set_config(True, True, True)
    inspection_details.retranslate_ui()
    assert inspection_details.btn_primary.text() == 'post_to_multisig'
    assert inspection_details.btn_import.text() == 'import'


def test_loading_and_enabled_states(inspection_details):
    """Test the loading and enabled states of the BroadcastInspectionDetails component."""
    with patch.object(inspection_details.btn_primary, 'start_loading') as m1, \
            patch.object(inspection_details.btn_primary, 'stop_loading') as m2:
        inspection_details.set_primary_loading(True)
        m1.assert_called_once()
        inspection_details.set_primary_loading(False)
        m2.assert_called_once()

    with patch.object(inspection_details.btn_reject, 'start_loading') as m1, \
            patch.object(inspection_details.btn_reject, 'stop_loading') as m2:
        inspection_details.set_reject_loading(True)
        m1.assert_called_once()
        inspection_details.set_reject_loading(False)
        m2.assert_called_once()

    inspection_details.set_primary_enabled(False)
    assert inspection_details.btn_primary.isEnabled() is False

    inspection_details.set_reject_enabled(False)
    assert inspection_details.btn_reject.isEnabled() is False
