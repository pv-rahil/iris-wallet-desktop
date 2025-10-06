"""UI tests for `BroadcastTransactionWidget`"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QDialog

from src.views.ui_broadcast_transaction import BroadcastTransactionWidget


@pytest.fixture
def vm_mock():
    """Create a lightweight mock of the `MainViewModel` and nested attributes used by the widget."""
    vm = MagicMock()
    # Signals used in setup_ui_connection
    btv = MagicMock()
    is_loading = MagicMock()
    is_loading.connect = lambda *_a, **_k: None
    tx_broadcasted = MagicMock()
    tx_broadcasted.connect = lambda *_a, **_k: None
    finalized_psbt = MagicMock()
    finalized_psbt.connect = lambda *_a, **_k: None
    hw_dialog_update = MagicMock()
    hw_dialog_update.connect = lambda *_a, **_k: None

    btv.is_loading = is_loading
    btv.tx_broadcasted = tx_broadcasted
    btv.finalized_psbt = finalized_psbt
    btv.hw_dialog_update = hw_dialog_update
    vm.broadcast_transaction_view_model = btv

    # Page navigation endpoints
    nav = MagicMock()
    vm.page_navigation = nav
    return vm


@pytest.fixture
def privileges_broadcast():
    """Return a privileges object for broadcast mode (no signing)."""
    return MagicMock(can_sign_psbt=False, can_broadcast_psbt=True)


@pytest.fixture
def privileges_sign():
    """Return a privileges object for sign-only mode (no broadcast)."""
    return MagicMock(can_sign_psbt=True, can_broadcast_psbt=False)


@pytest.fixture
def widget_broadcast(qt_app, vm_mock, privileges_broadcast):
    """Provide a widget instance configured for broadcast mode.

    Uses `from_sidebar=True` to avoid auto-loading PSBTs in constructor.
    """
    # Patch config and heavy UI dependencies
    with patch('src.views.ui_broadcast_transaction.get_current_wallet_mode_config') as cfg, \
            patch('src.views.ui_broadcast_transaction.load_stylesheet', return_value=''), \
            patch('src.views.ui_broadcast_transaction.HardwareWalletOperationDialog.get_instance') as get_hw:
        cfg.return_value = MagicMock(privileges=privileges_broadcast)
        hw = MagicMock()
        hw.isVisible.return_value = False
        get_hw.return_value = hw

        # Avoid auto loader side-effects by setting from_sidebar=True
        w = BroadcastTransactionWidget(vm_mock, from_sidebar=True)
        yield w
        w.close()


@pytest.fixture
def widget_sign(qt_app, vm_mock, privileges_sign):
    """Provide a widget instance configured for sign-only mode."""
    with patch('src.views.ui_broadcast_transaction.get_current_wallet_mode_config') as cfg, \
            patch('src.views.ui_broadcast_transaction.load_stylesheet', return_value=''), \
            patch('src.views.ui_broadcast_transaction.HardwareWalletOperationDialog.get_instance') as get_hw:
        cfg.return_value = MagicMock(privileges=privileges_sign)
        hw = MagicMock()
        hw.isVisible.return_value = False
        get_hw.return_value = hw

        w = BroadcastTransactionWidget(vm_mock, from_sidebar=True)
        yield w
        w.close()


def test_handle_button_enable_broadcast_requires_input_and_method(widget_broadcast: BroadcastTransactionWidget):
    """Broadcast button enables only when input exists (and selector ok)."""
    # Initially no input
    widget_broadcast.method_selector.setVisible(True)
    widget_broadcast.method_selector.addItem('opt')
    widget_broadcast.handle_button_enable()
    assert not widget_broadcast.broadcast_button.isEnabled()

    # With input
    widget_broadcast.broadcast_transaction_input.setPlainText('signedpsbt')
    widget_broadcast.handle_button_enable()
    assert widget_broadcast.broadcast_button.isEnabled()


def test_update_loading_state_toggles_button(widget_broadcast: BroadcastTransactionWidget):
    """Loading state disables button; clearing loading re-evaluates enablement."""
    widget_broadcast.broadcast_transaction_input.setPlainText('x')
    widget_broadcast.handle_button_enable()
    assert widget_broadcast.broadcast_button.isEnabled()

    widget_broadcast.update_loading_state(True)
    assert not widget_broadcast.broadcast_button.isEnabled()

    widget_broadcast.update_loading_state(False)
    assert widget_broadcast.broadcast_button.isEnabled()


def test_send_asset_cancel_does_nothing(widget_broadcast: BroadcastTransactionWidget, vm_mock):
    """When user cancels confirmation, no handler is called."""
    vm = vm_mock.broadcast_transaction_view_model
    with patch('src.views.ui_broadcast_transaction.ConfirmationDialog') as dlg:
        dlg.return_value.exec.return_value = QDialog.Rejected
        widget_broadcast.broadcast_transaction_input.setPlainText(
            'psbt:send_btc:abc',
        )
        widget_broadcast.send_asset()
    assert not vm.send_btc_end.called
    assert not vm.send_end.called
    assert not vm.create_utxos_end.called


@pytest.mark.parametrize(
    'payload,expected',
    [
        ('psbt:send_btc:abc', 'send_btc_end'),
        ('psbt:send_asset:def', 'send_end'),
        # Unknown purpose falls back to create_utxos_end
        ('psbt:other:ghi', 'create_utxos_end'),
    ],
)
def test_send_asset_routes_by_purpose(widget_broadcast: BroadcastTransactionWidget, vm_mock, payload, expected):
    """Routes to correct VM method based on encoded `psbt:<purpose>:<psbt>`."""
    vm = vm_mock.broadcast_transaction_view_model
    with patch('src.views.ui_broadcast_transaction.ConfirmationDialog') as dlg:
        dlg.return_value.exec.return_value = QDialog.Accepted
        widget_broadcast.broadcast_transaction_input.setPlainText(payload)
        widget_broadcast.send_asset()
    getattr(vm, expected).assert_called_once()


def test_send_asset_uses_selector_purpose_when_missing(widget_broadcast: BroadcastTransactionWidget, vm_mock):
    """If purpose is missing, derive it from selected signed PSBT item."""
    # When input is like `psbt:<psbt>` and there are signed items, use selected purpose
    vm = vm_mock.broadcast_transaction_view_model
    with patch('src.views.ui_broadcast_transaction.ConfirmationDialog') as dlg:
        dlg.return_value.exec.return_value = QDialog.Accepted
        # Inject signed items and show selector
        widget_broadcast._psbt_signed_items = [
            {'purpose': 'send_btc', 'psbt': 'A', 'id': 'id1'},
            {'purpose': 'send_asset', 'psbt': 'B', 'id': 'id2'},
        ]
        widget_broadcast.method_selector.setVisible(True)
        widget_broadcast.method_selector.addItems(['send_btc', 'send_asset'])
        widget_broadcast.method_selector.setCurrentIndex(1)
        # Ensure visibility check passes inside widget code
        widget_broadcast.show()

        widget_broadcast.broadcast_transaction_input.setPlainText('psbt:XYZ')
        widget_broadcast.send_asset()

    vm.send_end.assert_called_once_with('XYZ')


def test_on_click_close_button_navigates(widget_broadcast: BroadcastTransactionWidget, vm_mock):
    """Navigates to the page mapped by the checked sidebar button."""
    # Sidebar mock with a checked fungibles button
    btn = MagicMock()
    btn.isChecked.return_value = True
    btn.get_translation_key.return_value = 'fungibles'

    sidebar = MagicMock(
        backup=MagicMock(isChecked=lambda: False),
        help=MagicMock(isChecked=lambda: False),
        view_unspent_list=MagicMock(isChecked=lambda: False),
        faucet=MagicMock(isChecked=lambda: False),
        my_fungibles=btn,
        my_collectibles=MagicMock(isChecked=lambda: False),
        settings=MagicMock(isChecked=lambda: False),
        about=MagicMock(isChecked=lambda: False),
        broadcast_transaction=MagicMock(isChecked=lambda: False),
    )
    vm_mock.page_navigation.sidebar.return_value = sidebar

    widget_broadcast.on_click_close_button()
    vm_mock.page_navigation.fungibles_asset_page.assert_called_once()


def test_on_click_close_button_unknown_shows_toast(widget_broadcast: BroadcastTransactionWidget, vm_mock):
    """If no sidebar button is checked, an error toast is shown."""
    # No button checked => show toast error
    off = MagicMock(isChecked=lambda: False)
    sidebar = MagicMock(
        backup=off,
        help=off,
        view_unspent_list=off,
        faucet=off,
        my_fungibles=off,
        my_collectibles=off,
        settings=off,
        about=off,
        broadcast_transaction=off,
    )
    vm_mock.page_navigation.sidebar.return_value = sidebar

    with patch('src.views.ui_broadcast_transaction.ToastManager.show_toast') as st:
        widget_broadcast.on_click_close_button()
        st.assert_called()


def test_load_psbts_for_broadcast_zero_one_many(widget_broadcast: BroadcastTransactionWidget):
    """PSBT loader (broadcast) hides selector for 0/1, shows for many and updates input."""
    # zero
    with patch('src.views.ui_broadcast_transaction.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_psbt=lambda _signed: [])
        widget_broadcast._load_psbts_for_broadcast()
        assert not widget_broadcast.method_selector.isVisible()

    # one
    one = [{'psbt': 'SIGNED1', 'purpose': 'send_btc', 'id': 'abc'}]
    with patch('src.views.ui_broadcast_transaction.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_psbt=lambda _signed: one)
        widget_broadcast._load_psbts_for_broadcast()
        assert not widget_broadcast.method_selector.isVisible()
        assert widget_broadcast.broadcast_transaction_input.toPlainText() == 'SIGNED1'

    # many
    many = [
        {'psbt': 'S1', 'purpose': 'send_btc', 'id': 'id1'},
        {'psbt': 'S2', 'purpose': 'send_asset', 'id': 'id2'},
    ]
    with patch('src.views.ui_broadcast_transaction.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_psbt=lambda _signed: many)
        widget_broadcast._load_psbts_for_broadcast()
        # Parent widget is not shown in tests, so use isHidden() which ignores parent visibility
        assert not widget_broadcast.method_selector.isHidden()
        # Changing index updates input
        widget_broadcast.method_selector.setCurrentIndex(1)
        assert widget_broadcast.broadcast_transaction_input.toPlainText() == 'S2'


def test_load_psbts_for_signing_zero_one_many(widget_sign: BroadcastTransactionWidget):
    """PSBT loader (signing) hides selector for 0/1, shows for many and updates input."""
    # zero
    with patch('src.views.ui_broadcast_transaction.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_psbt=lambda _signed: [])
        widget_sign._load_psbts_for_signing()
        assert not widget_sign.method_selector.isVisible()

    # one
    one = [{'psbt': 'UNSIGNED1', 'purpose': 'psbt', 'id': 'xyz'}]
    with patch('src.views.ui_broadcast_transaction.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_psbt=lambda _signed: one)
        widget_sign._load_psbts_for_signing()
        assert not widget_sign.method_selector.isVisible()
        assert widget_sign.broadcast_transaction_input.toPlainText() == 'UNSIGNED1'

    # many
    many = [
        {'psbt': 'U1', 'purpose': 'psbt', 'id': 'id1'},
        {'psbt': 'U2', 'purpose': 'psbt', 'id': 'id2'},
    ]
    with patch('src.views.ui_broadcast_transaction.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_psbt=lambda _signed: many)
        widget_sign._load_psbts_for_signing()
        # Parent widget is not shown in tests, so use isHidden() which ignores parent visibility
        assert not widget_sign.method_selector.isHidden()
        widget_sign.method_selector.setCurrentIndex(1)
        assert widget_sign.broadcast_transaction_input.toPlainText() == 'U2'


def test_handle_nia_hw_dialog_updates_and_shows(widget_broadcast: BroadcastTransactionWidget):
    """HW dialog is updated and shown when receiving a dialog update."""
    # Hardware dialog is a MagicMock from fixture
    widget_broadcast.hw_dialog.isVisible.return_value = False
    widget_broadcast.handle_nia_hw_dialog('msg', MagicMock())
    widget_broadcast.hw_dialog.update_dialog.assert_called()
    widget_broadcast.hw_dialog.show.assert_called()


def test_show_signed_psbt_page_accepts_dialog_and_navigates(widget_sign: BroadcastTransactionWidget, vm_mock):
    """On signed PSBT, accept dialog if visible and navigate to receive page."""
    # Simulate visible hw dialog which should be accepted
    widget_sign.hw_dialog.isVisible.return_value = True
    widget_sign.show_signed_psbt_page('finalpsbt')
    widget_sign.hw_dialog.accept.assert_called_once()
    vm_mock.page_navigation.receive_asset_page.assert_called()


def test_retranslate_ui_sets_texts(widget_broadcast: BroadcastTransactionWidget):
    """Retranslate populates title, label, and button texts."""
    widget_broadcast.retranslate_ui()
    # Ensure labels are set (translated text fallback equals key in tests)
    assert widget_broadcast.broadcast_transaction_title_label.text()
    assert widget_broadcast.broadcast_transaction_label.text()
    assert widget_broadcast.broadcast_button.text()


def test_sign_only_sets_rgb_mode_true_for_send_asset(widget_sign: BroadcastTransactionWidget, vm_mock):
    """In sign-only mode, purpose 'send_asset' should set RGB mode True before signing."""
    with patch('src.views.ui_broadcast_transaction.ConfirmationDialog') as dlg, \
            patch('src.views.ui_broadcast_transaction.hardware_client_store') as store:
        dlg.return_value.exec.return_value = QDialog.Accepted
        # Simulate selected unsigned PSBT with purpose send_asset via selector
        widget_sign._psbt_items = [
            {'purpose': 'send_asset', 'psbt': 'UNSIGNED', 'id': 'id1'},
        ]
        widget_sign.method_selector.setVisible(False)
        widget_sign.broadcast_transaction_input.setPlainText('psbt:UNSIGNED')
        widget_sign.send_asset()
        store.set_rgb_mode.assert_called_once_with(True)
        vm_mock.broadcast_transaction_view_model.sign_and_finalize_psbt.assert_called_once_with(
            'UNSIGNED',
        )


def test_sign_only_sets_rgb_mode_false_for_btc(widget_sign: BroadcastTransactionWidget, vm_mock):
    """In sign-only mode, purpose not equal to 'send_asset' should set RGB mode False."""
    with patch('src.views.ui_broadcast_transaction.ConfirmationDialog') as dlg, \
            patch('src.views.ui_broadcast_transaction.hardware_client_store') as store:
        dlg.return_value.exec.return_value = QDialog.Accepted
        widget_sign._psbt_items = [
            {'purpose': 'send_btc', 'psbt': 'U', 'id': 'id1'},
        ]
        widget_sign.method_selector.setVisible(False)
        widget_sign.broadcast_transaction_input.setPlainText('psbt:U')
        widget_sign.send_asset()
        store.set_rgb_mode.assert_called_once_with(False)
        vm_mock.broadcast_transaction_view_model.sign_and_finalize_psbt.assert_called_once_with(
            'U',
        )
