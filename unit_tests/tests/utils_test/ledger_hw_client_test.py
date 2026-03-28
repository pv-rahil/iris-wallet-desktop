# pylint: disable=redefined-outer-name, unused-argument, protected-access
"""
This module contains the unit tests for the ledger_hw_client module.
"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ledger_bitcoin import Chain
from ledger_bitcoin.client_base import PartialSignature

from src.model.enums.enums_model import NetworkEnumModel
from src.utils.ledger_hw_client import _apply_signatures
from src.utils.ledger_hw_client import _build_multisig_policy
from src.utils.ledger_hw_client import _get_bip44_coin_type
from src.utils.ledger_hw_client import _get_hid_devices
from src.utils.ledger_hw_client import _hardened
from src.utils.ledger_hw_client import _is_emulator_reachable
from src.utils.ledger_hw_client import _probe_device
from src.utils.ledger_hw_client import create_ledger_client
from src.utils.ledger_hw_client import enumerate_ledger_devices
from src.utils.ledger_hw_client import network_to_chain
from src.utils.ledger_hw_client import sign_psbt_with_ledger


def test_network_to_chain():
    """Test network_to_chain function."""
    assert network_to_chain(NetworkEnumModel.MAINNET) == Chain.MAIN
    assert network_to_chain(NetworkEnumModel.TESTNET) == Chain.TEST
    assert network_to_chain(NetworkEnumModel.REGTEST) == Chain.REGTEST
    assert network_to_chain(None) == Chain.TEST


def test_is_emulator_reachable():
    """Test is_emulator_reachable function."""
    with patch('socket.create_connection') as mock_conn:
        assert _is_emulator_reachable('localhost', 1234) is True

        mock_conn.side_effect = OSError
        assert _is_emulator_reachable('localhost', 1234) is False

        assert _is_emulator_reachable(None, 1234) is False
        assert _is_emulator_reachable('localhost', 0) is False


def test_get_hid_devices():
    """Test get_hid_devices function."""
    with patch('hid.enumerate') as mock_enum:
        mock_enum.return_value = [
            {'path': b'1', 'interface_number': 0},
            {'path': b'2', 'interface_number': 1, 'usage_page': 0xFFA0},
            {'path': b'3', 'interface_number': 1},  # Should be ignored
        ]
        devices = _get_hid_devices()
        assert len(devices) == 2
        assert devices[0]['path'] == b'1'
        assert devices[1]['path'] == b'2'

        mock_enum.side_effect = Exception('err')
        assert not _get_hid_devices()


@patch('src.utils.ledger_hw_client.SettingRepository')
@patch('src.utils.ledger_hw_client.createClient')
def test_probe_device(mock_create_client, mock_repo):
    """Test probe_device function."""
    mock_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET
    mock_transport = MagicMock()
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    # Success case
    mock_client.get_version.return_value = ('RGB App', '1.0.0', 'flags')
    mock_client.get_master_fingerprint.return_value = bytes.fromhex('aabbccdd')
    app, fp = _probe_device(mock_transport)
    assert app == 'RGB App'
    assert fp == 'aabbccdd'
    mock_client.stop.assert_called_once()

    # Wrong app case
    mock_client.get_version.return_value = ('Bitcoin App', '1.0.0', 'flags')
    app, fp = _probe_device(mock_transport)
    assert app is None
    mock_transport.stop.assert_called()

    # Exception case
    mock_client.get_version.side_effect = Exception('err')
    app, fp = _probe_device(mock_transport)
    assert app is None


@patch('src.utils.ledger_hw_client._get_hid_devices')
@patch('src.utils.ledger_hw_client.TransportClient')
@patch('src.utils.ledger_hw_client._probe_device')
@patch('src.utils.ledger_hw_client._is_emulator_reachable')
@patch('psutil.process_iter')
def test_enumerate_ledger_devices(mock_psutil, mock_reachable, mock_probe, mock_tc, mock_hid):
    """Test enumerate_ledger_devices function."""
    # HID device
    mock_hid.return_value = [{'path': b'hid_path', 'product_id': 0x4000}]
    mock_probe.return_value = ('RGB', 'fp_hid')

    # Emulator
    mock_reachable.return_value = True
    mock_psutil.return_value = [
        MagicMock(info={'cmdline': ['speculos', '-m', 'nanox']}),
    ]
    # Mock second probe for emulator
    mock_probe.side_effect = [('RGB', 'fp_hid'), ('RGB', 'fp_tcp')]

    devices = enumerate_ledger_devices()
    assert len(devices) == 2
    assert devices[0]['type'] == 'hid'
    assert devices[0]['fingerprint'] == 'fp_hid'
    assert devices[1]['type'] == 'tcp'
    assert devices[1]['fingerprint'] == 'fp_tcp'
    assert devices[1]['model'] == 'ledger_nano_x'


@patch('src.utils.ledger_hw_client._get_hid_devices')
@patch('src.utils.ledger_hw_client.TransportClient')
@patch('src.utils.ledger_hw_client._probe_device')
def test_enumerate_ledger_devices_errors(mock_probe, mock_tc, mock_hid):
    """Test enumerate_ledger_devices function with errors."""
    mock_hid.return_value = [{'path': b'path'}]
    mock_probe.return_value = (None, None)

    devices = enumerate_ledger_devices()
    assert devices[0]['error'] == 'App not open or device locked'

    mock_tc.side_effect = Exception('0x5515')
    devices = enumerate_ledger_devices()
    assert devices[0]['error'] == 'ledger_unlock_device'


@patch('src.utils.ledger_hw_client.SettingRepository')
@patch('src.utils.ledger_hw_client.TransportClient')
@patch('src.utils.ledger_hw_client.createClient')
def test_create_ledger_client(mock_create, mock_tc, mock_repo):
    """Test create_ledger_client function."""
    mock_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET

    # HID
    create_ledger_client({'type': 'hid', 'path': b'p'})
    mock_tc.assert_called_with('hid', path=b'p')

    # TCP explicit
    create_ledger_client({'type': 'tcp', 'path': 'tcp:1.2.3.4:5000'})
    mock_tc.assert_called_with('tcp', server='1.2.3.4', port=5000)

    # TCP default
    create_ledger_client({'type': 'tcp', 'path': None})
    mock_tc.assert_called_with('tcp', server='127.0.0.1', port=9999)


def test_hardened():
    """Test hardened function."""
    assert _hardened(0) == 0x80000000


def test_get_bip44_coin_type():
    """Test get_bip44_coin_type function."""
    assert _get_bip44_coin_type(False, True) == 827166
    assert _get_bip44_coin_type(True, True) == 827167
    assert _get_bip44_coin_type(False, False) == 0
    assert _get_bip44_coin_type(True, False) == 1


def test_build_multisig_policy():
    """Test build_multisig_policy function."""
    desc = 'tr(key1,multi_a(2,key2/**,key3/**))'
    policy = _build_multisig_policy(desc, 'Wallet')
    assert policy.name == 'Wallet'
    assert len(policy.keys_info) == 3
    assert '@0/**' in policy.descriptor_template

    with pytest.raises(ValueError):
        _build_multisig_policy('invalid', 'Wallet')


@patch('src.utils.ledger_hw_client.hardware_client_store')
@patch('src.utils.ledger_hw_client.SettingRepository')
@patch('src.utils.ledger_hw_client.PSBT')
@patch('src.utils.ledger_hw_client._build_multisig_policy')
def test_sign_psbt_with_ledger_multisig(mock_build, mock_psbt, mock_repo, mock_store):
    """Test sign_psbt_with_ledger_multisig function."""
    mock_store.get_rgb_mode.return_value = True
    mock_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_client = MagicMock()
    mock_client.register_wallet.return_value = (None, b'hmac')
    mock_psbt_inst = MagicMock()
    mock_psbt.return_value = mock_psbt_inst
    mock_psbt_inst.version = 2

    descriptor = MagicMock()
    descriptor.colored = 'tr(k,multi_a(1,k2))'

    sign_psbt_with_ledger('unsigned', mock_client, descriptor)
    mock_client.sign_psbt.assert_called_once()


@patch('src.utils.ledger_hw_client.copy.deepcopy', side_effect=lambda x: x)
@patch('src.utils.ledger_hw_client.hardware_client_store')
@patch('src.utils.ledger_hw_client.SettingRepository')
@patch('src.utils.ledger_hw_client.PSBT')
def test_sign_psbt_with_ledger_singlesig(mock_psbt, mock_repo, mock_store, _mock_copy):
    """Test sign_psbt_with_ledger_singlesig function."""
    mock_store.get_rgb_mode.return_value = False  # Vanilla
    mock_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET

    mock_client = MagicMock()
    mock_fp = bytes.fromhex('aabbccdd')
    mock_client.get_master_fingerprint.return_value = mock_fp
    mock_client.get_extended_pubkey.return_value = 'xpub'

    mock_psbt_inst = MagicMock()
    mock_psbt.return_value = mock_psbt_inst
    mock_psbt_inst.version = 0

    # Setup inputs for account discovery
    mock_input = MagicMock()
    mock_input.tap_internal_key = 'key'
    mock_origin = MagicMock()
    mock_origin.fingerprint = mock_fp
    mock_origin.path = [0, 0, 0x80000000 + 5]  # account 5
    mock_input.tap_bip32_paths = {'key': (None, mock_origin)}
    mock_psbt_inst.inputs = [mock_input]

    descriptor = MagicMock()
    descriptor.vanilla = 'tr(k)'

    sign_psbt_with_ledger('unsigned', mock_client, descriptor)
    mock_psbt_inst.convert_to_v2.assert_called_once()
    mock_client.get_extended_pubkey.assert_called_with(
        path="m/86'/0'/5'", display=False,
    )


def test_apply_signatures():
    """Test apply_signatures function."""
    psbt = MagicMock()
    inp = MagicMock()
    inp.tap_script_sigs = {}
    inp.partial_sigs = {}
    psbt.inputs = [inp]

    # Tap script sig
    sig1 = PartialSignature(
        signature=b'sig1', pubkey=b'pub1', tapleaf_hash=b'hash',
    )
    # Tap key sig (32 bytes pubkey)
    sig2 = PartialSignature(
        signature=b'sig2', pubkey=b'P' * 32, tapleaf_hash=None,
    )
    # Partial sig (33 bytes legacy pubkey)
    sig3 = PartialSignature(
        signature=b'sig3', pubkey=b'P' * 33, tapleaf_hash=None,
    )

    # 99 is invalid index
    _apply_signatures(psbt, [(0, sig1), (0, sig2), (0, sig3), (99, sig1)])

    assert inp.tap_script_sigs[(b'pub1', b'hash')] == b'sig1'
    assert inp.tap_key_sig == b'sig2'
    assert inp.partial_sigs[b'P' * 33] == b'sig3'

    # Test non-PartialSignature
    _apply_signatures(psbt, [(0, 'not a sig')])
