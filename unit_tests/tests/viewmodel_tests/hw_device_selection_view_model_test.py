# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""Unit tests for `HWDeviceSelectionViewModel`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from hwilib.common import Chain

from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.local_store import local_store
from src.viewmodels.hw_device_selection_view_model import HWDeviceSelectionViewModel


@pytest.fixture
def vm() -> HWDeviceSelectionViewModel:
    """Return a fresh `HWDeviceSelectionViewModel` instance for tests."""
    return HWDeviceSelectionViewModel()


def test_connect_to_device_runs_in_thread(vm: HWDeviceSelectionViewModel):
    """connect_to_device() should schedule _fetch_ledger_xpubs via ThreadManager."""
    with patch('src.utils.worker.ThreadManager.run_in_thread') as run:
        vm.connect_to_device('/dev/hw', NetworkEnumModel.TESTNET)
        assert run.called
        args, _ = run.call_args
        assert args[0].__name__ == '_fetch_ledger_xpubs'
        # run_in_thread is invoked with a positional dict of options
        assert args[1]['args'] == ['/dev/hw', NetworkEnumModel.TESTNET]


@patch('src.viewmodels.hw_device_selection_view_model.LedgerClient')
def test_fetch_ledger_xpubs_success(mock_ledger, vm: HWDeviceSelectionViewModel):
    """_fetch_ledger_xpubs should return (vanilla, colored, fingerprint)."""
    client = MagicMock()
    client.get_pubkey_at_path.return_value.to_string.return_value = 'xpub'
    client.get_master_fingerprint.return_value.hex.return_value = 'f1f2f3f4'
    mock_ledger.return_value = client

    res = vm._fetch_ledger_xpubs('/dev/hw', NetworkEnumModel.TESTNET)
    assert res == ('xpub', 'xpub', 'f1f2f3f4')
    # Ensure LedgerClient constructed with correct Chain for TESTNET
    args, _ = mock_ledger.call_args
    assert args == ('/dev/hw', None, True, Chain.TEST)


def test_on_ledger_success_sets_local_store_and_emits(vm: HWDeviceSelectionViewModel, qtbot):
    """on_ledger_success should update local_store and emit connect_succeeded."""
    with qtbot.waitSignal(vm.connect_succeeded, timeout=1000):
        vm.on_ledger_success(('van', 'col', 'fp'))
    assert local_store.get_value(ACCOUNT_XPUB_VANILLA) == 'van'
    assert local_store.get_value(ACCOUNT_XPUB_COLORED) == 'col'
    assert local_store.get_value(MASTER_FINGERPRINT) == 'fp'


@patch('src.viewmodels.hw_device_selection_view_model.LedgerClient')
@pytest.mark.parametrize(
    'network, expected_chain',
    [
        (NetworkEnumModel.MAINNET, Chain.MAIN),
        (NetworkEnumModel.TESTNET, Chain.TEST),
        (NetworkEnumModel.REGTEST, Chain.REGTEST),
    ],
)
def test_fetch_ledger_xpubs_chain_mapping(mock_ledger, vm: HWDeviceSelectionViewModel, network, expected_chain):
    """LedgerClient should be called with correct Chain depending on network."""
    client = MagicMock()
    client.get_pubkey_at_path.return_value.to_string.return_value = 'xpub'
    client.get_master_fingerprint.return_value.hex.return_value = 'abcd'
    mock_ledger.return_value = client

    vm._fetch_ledger_xpubs('/dev/hw', network)
    args, _ = mock_ledger.call_args
    assert args == ('/dev/hw', None, True, expected_chain)


@patch('src.viewmodels.hw_device_selection_view_model.LedgerClient', side_effect=Exception('boom'))
def test_fetch_ledger_xpubs_emits_on_error(_mock_ledger, vm: HWDeviceSelectionViewModel, qtbot):
    """On exception, `_fetch_ledger_xpubs` should emit connect_failed with the error."""
    with qtbot.waitSignal(vm.connect_failed, timeout=1000) as sig:
        vm._fetch_ledger_xpubs('/dev/hw', NetworkEnumModel.TESTNET)
    assert 'boom' in sig.args[0]


def test_on_ledger_error_emits_and_toast(vm: HWDeviceSelectionViewModel, qtbot):
    """on_ledger_error should emit connect_failed and show toast error."""
    with patch('src.views.components.toast.ToastManager.error') as terr:
        with qtbot.waitSignal(vm.connect_failed, timeout=1000):
            vm.on_ledger_error('bad')
        terr.assert_called()
