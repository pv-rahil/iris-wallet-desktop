"""
Ledger hardware wallet client for taproot single-sig and multisig PSBT signing.
"""
from __future__ import annotations

import copy
import re
import socket
from typing import Any

from ledger_bitcoin import Chain, WalletPolicy, createClient
from ledger_bitcoin.client_base import PartialSignature, TransportClient
from ledger_bitcoin.psbt import PSBT
from rgb_lib import WalletDescriptors

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import LEDGER_EMULATOR_HOST, LEDGER_EMULATOR_PORT
from src.utils.hardware_client_store import hardware_client_store
from src.utils.logging import logger

# Ledger USB Vendor ID
_LEDGER_VENDOR_ID = 0x2C97

# Model names by product ID
_LEDGER_MODELS = {
    0x10: 'ledger_nano_s', 0x40: 'ledger_nano_x', 0x50: 'ledger_nano_s_plus',
    0x60: 'ledger_stax', 0x70: 'ledger_flex',
    0x0001: 'ledger_nano_s', 0x0004: 'ledger_nano_x',  # Legacy
}

_LEDGER_EMULATOR_TIMEOUT = 1.0


def network_to_chain(network: NetworkEnumModel) -> Chain:
    """Convert NetworkEnumModel to ledger_bitcoin Chain."""
    return {
        NetworkEnumModel.MAINNET: Chain.MAIN,
        NetworkEnumModel.TESTNET: Chain.TEST,
        NetworkEnumModel.REGTEST: Chain.REGTEST,
    }.get(network, Chain.TEST)


def _is_emulator_reachable(host: str, port: int) -> bool:
    """Check if Speculos emulator is listening on host:port."""
    if not host or port == 0:
        return False
    try:
        with socket.create_connection((host, port), timeout=_LEDGER_EMULATOR_TIMEOUT):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def _get_hid_devices() -> list[dict]:
    """Enumerate connected Ledger HID devices."""
    try:
        import hid
        devices = []
        for dev in hid.enumerate(_LEDGER_VENDOR_ID, 0):
            if dev.get('interface_number') == 0 or dev.get('usage_page') == 0xFFA0:
                devices.append(dev)
        return devices
    except Exception as exc:
        logger.warning('[LedgerHW] HID enumerate failed: %s', exc)
        return []


def _probe_device(transport: TransportClient) -> tuple[str | None, str | None]:
    """Get (app_name, fingerprint_hex) from device. Returns (None, None) on failure."""
    try:
        network = SettingRepository.get_wallet_network()
        client = createClient(transport, chain=network_to_chain(network))
        app_name, _, _ = client.get_version()
        fp = client.get_master_fingerprint().hex()
        client.stop()
        return app_name, fp
    except Exception:
        transport.stop()
        return None, None


def enumerate_ledger_devices() -> list[dict[str, Any]]:
    """
    Discover Ledger devices (HID and TCP emulator).
    
    Returns list of dicts with keys: path, type, model, fingerprint, error.
    """
    devices = []

    # HID devices
    for raw in _get_hid_devices():
        path = raw.get('path', b'')
        pid = raw.get('product_id', 0)
        model = _LEDGER_MODELS.get(pid >> 8) or _LEDGER_MODELS.get(pid, 'ledger')
        
        entry = {'path': path, 'type': 'hid', 'model': model, 'fingerprint': '', 'error': None}
        try:
            tc = TransportClient('hid', path=path)
            _, fp = _probe_device(tc)
            if fp:
                entry['fingerprint'] = fp
            else:
                entry['error'] = 'Device not in Bitcoin app or locked'
        except Exception as exc:
            entry['error'] = str(exc)
        devices.append(entry)

    # TCP emulator
    if _is_emulator_reachable(LEDGER_EMULATOR_HOST, LEDGER_EMULATOR_PORT):
        tcp_path = f'tcp:{LEDGER_EMULATOR_HOST}:{LEDGER_EMULATOR_PORT}'
        
        # Detect model from speculos process
        pid = 0x1000
        try:
            import psutil
            for proc in psutil.process_iter(['cmdline']):
                cmd = proc.info.get('cmdline') or []
                if any('speculos' in str(a).lower() for a in cmd) and '-m' in cmd:
                    model_flag = cmd[cmd.index('-m') + 1].lower()
                    if 'flex' in model_flag: pid = 0x7000
                    elif 'stax' in model_flag: pid = 0x6000
                    elif 'nanosp' in model_flag: pid = 0x5000
                    elif 'nanox' in model_flag: pid = 0x4000
        except Exception:
            pass

        model = _LEDGER_MODELS.get(pid >> 8, 'ledger_nano_s')
        entry = {'path': tcp_path, 'type': 'tcp', 'model': model, 'fingerprint': '', 'error': None}
        
        try:
            tc = TransportClient('tcp', server=LEDGER_EMULATOR_HOST, port=LEDGER_EMULATOR_PORT)
            _, fp = _probe_device(tc)
            if fp:
                entry['fingerprint'] = fp
            else:
                entry['error'] = 'Emulator connection failed'
        except Exception as exc:
            entry['error'] = str(exc)
        devices.append(entry)

    return devices


def create_ledger_client(device_info: dict[str, Any]) -> Any:
    """Create ledger_bitcoin client from device_info dict."""
    transport_type = device_info.get('type', 'hid')
    path = device_info.get('path')

    if transport_type == 'tcp' and isinstance(path, str) and path.startswith('tcp:'):
        _, host, port_str = path.split(':', 2)
        tc = TransportClient('tcp', server=host, port=int(port_str))
    elif transport_type == 'tcp':
        tc = TransportClient('tcp', server=LEDGER_EMULATOR_HOST, port=LEDGER_EMULATOR_PORT)
    else:
        tc = TransportClient('hid', path=path)

    network = SettingRepository.get_wallet_network()
    return createClient(tc, chain=network_to_chain(network))


def _hardened(n: int) -> int:
    """Convert to hardened derivation index."""
    return n + 0x80000000


def _get_bip44_coin_type(is_testnet: bool, is_rgb: bool) -> int:
    """Get BIP44 coin type. RGB uses 827166/827167, Bitcoin uses 0/1."""
    if is_rgb:
        return 827167 if is_testnet else 827166
    return 1 if is_testnet else 0


def _build_multisig_policy(desc_str: str, wallet_name: str) -> WalletPolicy:
    """Build WalletPolicy from taproot multisig descriptor."""
    match = re.search(r'tr\(([^,]+),\s*multi_a\((\d+),(.*?)\)\)', desc_str, re.DOTALL)
    if not match:
        raise ValueError(f'Invalid multisig descriptor: {desc_str[:60]}')

    internal_key = match.group(1).strip()
    threshold = int(match.group(2))
    participants = match.group(3)

    def strip_wildcard(k: str) -> str:
        return k.replace('/0/*', '').replace('/**', '').replace('/1/*', '').strip()

    keys = [strip_wildcard(internal_key)] + [strip_wildcard(k) for k in participants.split(',') if k.strip()]
    template_parts = [f'@{i + 1}/**' for i in range(len(keys) - 1)]
    template = f"tr(@0/**,multi_a({threshold},{','.join(template_parts)}))"
    
    return WalletPolicy(wallet_name, template, keys)


def sign_psbt_with_ledger(
    unsigned_psbt: str,
    client: Any,
    descriptor: WalletDescriptors,
    wallet_name: str = 'Taproot Multisig',
) -> str:
    """
    Sign PSBT with Ledger device.
    
    Single-sig: Reads account from PSBT, queries device for xpub, builds standard policy.
    Multisig: Builds policy from descriptor, registers with device.
    """
    is_rgb = hardware_client_store.get_rgb_mode()
    desc_str = descriptor.colored if is_rgb else descriptor.vanilla
    is_multisig = 'multi_a(' in desc_str

    # Parse and convert PSBT to v2
    psbt = PSBT()
    psbt.deserialize(unsigned_psbt)
    psbt_v2 = copy.deepcopy(psbt)
    if psbt_v2.version != 2:
        psbt_v2.convert_to_v2()

    network = SettingRepository.get_wallet_network()
    is_testnet = network in (NetworkEnumModel.TESTNET, NetworkEnumModel.REGTEST)

    if is_multisig:
        policy = _build_multisig_policy(desc_str, wallet_name)
        _, policy_hmac = client.register_wallet(policy)
    else:
        # Single-sig: extract account from PSBT and query device for xpub
        master_fp = client.get_master_fingerprint()
        account = 0

        for inp in psbt_v2.inputs:
            if hasattr(inp, 'tap_bip32_paths') and inp.tap_bip32_paths:
                for key, (_, origin) in inp.tap_bip32_paths.items():
                    if key == inp.tap_internal_key and origin.fingerprint == master_fp:
                        account = origin.path[2] - _hardened(0)
                        break

        coin_type = _get_bip44_coin_type(is_testnet, is_rgb)
        xpub = client.get_extended_pubkey(path=f"m/86'/{coin_type}'/{account}'", display=False)
        key_str = f"[{master_fp.hex()}/86'/{coin_type}'/{account}']{xpub}"
        policy = WalletPolicy('', 'tr(@0/**)', [key_str])
        policy_hmac = None

        logger.debug('[LedgerHW] Single-sig policy: m/86\'/%d\'/%d\'', coin_type, account)

    logger.debug('[LedgerHW] Signing: template=%s keys=%d', policy.descriptor_template, len(policy.keys_info))
    
    partial_sigs = client.sign_psbt(psbt_v2, policy, policy_hmac)
    _apply_signatures(psbt, partial_sigs)
    return psbt.serialize()


def _apply_signatures(psbt: Any, partial_sigs: list) -> None:
    """Apply signatures from sign_psbt() result to PSBT object."""
    for idx, sig_obj in partial_sigs:
        if idx >= len(psbt.inputs):
            continue

        inp = psbt.inputs[idx]
        if not isinstance(sig_obj, PartialSignature):
            continue

        if sig_obj.tapleaf_hash is not None:
            inp.tap_script_sigs[(sig_obj.pubkey, sig_obj.tapleaf_hash)] = sig_obj.signature
        elif len(sig_obj.pubkey) == 32:
            inp.tap_key_sig = sig_obj.signature
        else:
            inp.partial_sigs[sig_obj.pubkey] = sig_obj.signature
