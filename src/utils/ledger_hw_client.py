"""
Ledger hardware wallet client utilities.

"""
from __future__ import annotations

import re
import socket
from typing import Any
from rgb_lib import WalletDescriptors
from ledger_bitcoin.psbt import PSBT
from ledger_bitcoin import Chain
from ledger_bitcoin import WalletPolicy
from ledger_bitcoin import createClient
from ledger_bitcoin.client_base import PartialSignature
from ledger_bitcoin.client_base import TransportClient

from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import LEDGER_EMULATOR_HOST
from src.utils.constant import LEDGER_EMULATOR_PORT
from src.data.repository.setting_repository import SettingRepository
from src.utils.logging import logger
from src.utils.hardware_client_store import hardware_client_store

# ---------------------------------------------------------------------------
# Hardware constant — Ledger's USB Vendor ID, assigned by USB-IF.
# This is not a business choice; it cannot change without new hardware.
# ---------------------------------------------------------------------------
_LEDGER_VENDOR_ID = 0x2C97

# ---------------------------------------------------------------------------
# Hardware models — mapped from USB Product IDs (same as HWI).
# This allows the UI to display "Nano S", "Nano X", etc. correctly.
# ---------------------------------------------------------------------------
_LEDGER_MODEL_IDS = {
    0x10: 'ledger_nano_s',
    0x40: 'ledger_nano_x',
    0x50: 'ledger_nano_s_plus',
    0x60: 'ledger_stax',
    0x70: 'ledger_flex',
}

_LEDGER_LEGACY_PRODUCT_IDS = {
    0x0001: 'ledger_nano_s',
    0x0004: 'ledger_nano_x',
}



# ---------------------------------------------------------------------------
# Emulator probe timeout — used by _is_emulator_reachable.
# ---------------------------------------------------------------------------
_LEDGER_EMULATOR_TIMEOUT = 1.0

def network_to_chain(network: NetworkEnumModel) -> Chain:
    """
    Convert a ``NetworkEnumModel`` value to the corresponding
    ``ledger_bitcoin.Chain``.

    * ``MAINNET``  → ``Chain.MAIN``
    * ``TESTNET``  → ``Chain.TEST``
    * ``REGTEST``  → ``Chain.TEST``  (Regtest uses testnet derivation paths)

    This is the single authoritative mapping used by both
    ``require_hardware_wallet_connected`` and ``common_operations_repository``.
    """
    return {
        NetworkEnumModel.MAINNET: Chain.MAIN,
        NetworkEnumModel.TESTNET: Chain.TEST,
        NetworkEnumModel.REGTEST: Chain.REGTEST,
    }.get(network, Chain.TEST)


def _is_emulator_reachable(host: str, port: int, timeout: float = _LEDGER_EMULATOR_TIMEOUT) -> bool:
    """
    Return True if a Speculos emulator is listening on host:port.
    Returns False immediately if host is empty or port is 0 (emulator disabled).
    """
    if not host or port == 0:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def _get_hid_devices() -> list[dict]:
    """
    Return raw HID device info dicts for all connected Ledger devices.
    Returns an empty list if the `hid` package is unavailable.
    """
    try:
        import hid  # pylint: disable=import-outside-toplevel
        raw: list[dict] = []
        for dev in hid.enumerate(_LEDGER_VENDOR_ID, 0):
            # Filter to the correct interface/usage_page like ledgercomm does
            if dev.get('interface_number') == 0 or dev.get('usage_page') == 0xFFA0:
                raw.append(dev)
        return raw
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning('[LedgerHW] hid.enumerate failed: %s', exc)
        return []


def _probe_device(transport_client: TransportClient) -> tuple[str | None, str | None]:
    """
    Open a short-lived connection and fetch (model_name, fingerprint_hex).
    Returns (None, None) if the device cannot be reached.
    """
    try:
        network = SettingRepository.get_wallet_network()
        chain = network_to_chain(network)
        client = createClient(transport_client, chain=chain)
        app_name, _version, _flags = client.get_version()
        fingerprint: bytes = client.get_master_fingerprint()
        client.stop()
        return app_name, fingerprint.hex()
    except Exception:
        transport_client.stop()
        return None,None


def enumerate_ledger_devices() -> list[dict[str, Any]]:
    """
    Discover all available Ledger devices — real (HID) and emulated (TCP).

    Each entry in the returned list has the same shape as the old HWI enumerate
    result so callers need no changes:

        {
            'path'        : bytes | str,  # HID path or 'tcp:<host>:<port>'
            'type'        : 'hid' | 'tcp',
            'model'       : str,          # app name reported by the device
            'fingerprint' : str,          # 8-char hex
            'error'       : str | None,
        }

    Devices that are unreachable, locked, or not in the Bitcoin app will have
    'error' set and 'fingerprint' / 'model' will be empty strings.

    The Speculos TCP emulator is only probed when the active network has an
    emulator endpoint configured (Regtest by default).  On Testnet and Mainnet
    the emulator is disabled unless ``LEDGER_EMULATOR_HOST`` is explicitly set.
    """
    devices: list[dict[str, Any]] = []

    # --- Real HID devices ---
    for raw in _get_hid_devices():
        path: bytes = raw.get('path', b'')
        pid = raw.get('product_id', 0)
        model_id = pid >> 8
        model_name = _LEDGER_MODEL_IDS.get(model_id)
        if not model_name:
            model_name = _LEDGER_LEGACY_PRODUCT_IDS.get(pid, 'ledger')

        entry: dict[str, Any] = {
            'path': path,
            'type': 'hid',
            'model': model_name,
            'fingerprint': '',
            'error': None,
        }
        try:
            tc = TransportClient('hid', path=path)
            result = _probe_device(tc)
            app_name, fp = result
            if fp is None:
                entry['error'] = 'Device not in Bitcoin app or locked'
            else:
                entry['fingerprint'] = fp
        except Exception as exc:  # pylint: disable=broad-except
            entry['error'] = str(exc)
        devices.append(entry)
        logger.debug('[LedgerHW] HID device: %s', entry)

    # --- Speculos TCP emulator (network-aware) ---
    if _is_emulator_reachable(LEDGER_EMULATOR_HOST, LEDGER_EMULATOR_PORT):
        tcp_path = f'tcp:{LEDGER_EMULATOR_HOST}:{LEDGER_EMULATOR_PORT}'
        
        # Direct detection: try to find the running speculos process and its model.
        # Fallback to Nano S (HWI behavior).
        pid = 0x1000  # Default: Nano S
        try:
            import psutil
            for proc in psutil.process_iter(['cmdline']):
                cmd = proc.info.get('cmdline') or []
                if any('speculos' in str(arg).lower() for arg in cmd):
                    if '-m' in cmd:
                        m_idx = cmd.index('-m')
                        if m_idx + 1 < len(cmd):
                            model_flag = cmd[m_idx + 1].lower()
                            if 'flex' in model_flag: pid = 0x7000
                            elif 'stax' in model_flag: pid = 0x6000
                            elif 'nanosp' in model_flag: pid = 0x5000
                            elif 'nanox' in model_flag: pid = 0x4000
        except:
            pass

        model_id = pid >> 8
        model_name = _LEDGER_MODEL_IDS.get(model_id, 'ledger_nano_s')

        entry: dict[str, Any] = {
            'path': tcp_path,
            'type': 'tcp',
            'model': model_name,
            'fingerprint': '',
            'error': None,
        }
        try:
            tc = TransportClient('tcp', server=LEDGER_EMULATOR_HOST, port=LEDGER_EMULATOR_PORT)
            result = _probe_device(tc)
            if result is None or result[1] is None:
                entry['error'] = 'Emulator connection failed or not in app'
            else:
                app_name, fp = result
                entry['fingerprint'] = fp
        except Exception as exc:
            entry['error'] = str(exc)
        devices.append(entry)
        logger.debug('[LedgerHW] TCP emulator: %s', entry)

    return devices


def create_ledger_client(device_info: dict[str, Any]) -> Any:
    """
    Create and return a ready-to-use ledger-bitcoin client.

    Parameters
    ----------
    device_info:
        A dict from `enumerate_ledger_devices()` (must contain 'type' and 'path').

    Returns
    -------
    A `ledger_bitcoin` client (NewClient or LegacyClient).
    """
    transport_type: str = device_info.get('type', 'hid')
    path = device_info.get('path')

    if transport_type == 'tcp':
        # Parse 'tcp:<host>:<port>' stored during enumeration
        if isinstance(path, str) and path.startswith('tcp:'):
            _, host, port_str = path.split(':', 2)
            port = int(port_str)
        else:
            host = LEDGER_EMULATOR_HOST
            port = LEDGER_EMULATOR_PORT
        tc = TransportClient('tcp', server=host, port=port)
    else:
        tc = TransportClient('hid', path=path)

    network = SettingRepository.get_wallet_network()
    chain = network_to_chain(network)

    return createClient(tc, chain=chain)


def build_wallet_policy_from_descriptor(
    desc_str: str,
    wallet_name: str = 'Taproot Multisig',
) -> WalletPolicy:
    """
    Parse an rgb-lib vanilla descriptor string and return a
    ``ledger_bitcoin.WalletPolicy`` that the device can register and sign with.

    Supports:
    * Standard single-sig taproot  ``tr(xpub/*)``  /  ``tr(xpub/**)``
    * Taproot multisig  ``tr(NUMS_KEY, multi_a(M, key1/*, key2/*, ...))``

    Parameters
    ----------
    desc_str:
        The full descriptor string from ``wallet.get_descriptors().vanilla``
        (or ``colored``).
    wallet_name:
        Human-readable name shown on the Ledger display during registration.

    Returns
    -------
    A ``WalletPolicy`` ready to be passed to
    ``client.register_wallet()`` or ``client.sign_psbt()``.
    """
    # Strip any checksum (#xxxx)
    desc_str = re.sub(r'#[a-z0-9]+$', '', desc_str.strip())

    # ------------------------------------------------------------------
    # Taproot multisig:  tr(INTERNAL_KEY, multi_a(M, k1, k2, ...))
    # ------------------------------------------------------------------
    multi_a_match = re.search(r'tr\(([^,]+),\s*multi_a\((\d+),(.*?)\)\)', desc_str, re.DOTALL)
    if multi_a_match:
        internal_key_raw = multi_a_match.group(1).strip()
        threshold = int(multi_a_match.group(2))
        participants_raw = multi_a_match.group(3)

        # Strip the wildcard derivation suffix carried by each key in the
        # descriptor — the WalletPolicy template uses @N/** notation instead.
        def _strip_wildcard(k: str) -> str:
            return k.replace('/0/*', '').replace('/**', '').replace('/1/*', '').strip()

        internal_key_clean = _strip_wildcard(internal_key_raw)
        participant_keys = [_strip_wildcard(k) for k in participants_raw.split(',') if k.strip()]

        keys_info = [internal_key_clean] + participant_keys
        template_parts = [f'@{i + 1}/**' for i in range(len(participant_keys))]
        template = f"tr(@0/**,multi_a({threshold},{','.join(template_parts)}))"
        return WalletPolicy(wallet_name, template, keys_info)

    single_sig_match = re.search(r'tr\(([^)]+)\)', desc_str)
    if single_sig_match:
        key_raw = single_sig_match.group(1).strip()
        # Ensure we strip wildcards like /0/* or /* which are common in rgb-lib descriptors
        key_clean = re.sub(r'/(?:[01]/)?(?:\*|\*\*)?$', '', key_raw)
        return WalletPolicy('Single Sig', 'tr(@0/**)', [key_clean])

    raise ValueError(
        f'Unsupported descriptor format for Ledger signing: {desc_str[:120]}',
    )


def sign_psbt_with_ledger(
    unsigned_psbt: str,
    client: Any,
    descriptor: WalletDescriptors,
    wallet_name: str = 'Taproot Multisig',
) -> str:
    """
    High-level helper that:

    1. Parses ``descriptor`` to build a :class:`WalletPolicy`.
    2. Registers the policy with the Ledger device (user confirms on screen).
    3. Deserializes ``unsigned_psbt`` and signs it.
    4. Applies signatures to the PSBT inputs.
    5. Returns the serialized PSBT string.

    Parameters
    ----------
    unsigned_psbt:
        Base-64-encoded PSBT string.
    client:
        An active ``ledger_bitcoin`` client.
    descriptor:
        The vanilla (or colored) descriptor string from rgb-lib, e.g.
        ``wallet.get_descriptors().vanilla``.
    wallet_name:
        Display name shown on the Ledger during registration.

    Returns
    -------
    Serialized PSBT string with signatures applied.
    """
    is_rgb_mode = hardware_client_store.get_rgb_mode()
    if is_rgb_mode:
        policy = build_wallet_policy_from_descriptor(descriptor.colored, wallet_name)
    else:
        policy = build_wallet_policy_from_descriptor(descriptor.vanilla, wallet_name)
    
    # For standard single-sig wallets, registration is not required and can cause
    # 0x6a80 errors if the device considers the policy built-in.
    if len(policy.keys_info) == 1:
        policy_hmac = None
    else:
        _policy_id, policy_hmac = client.register_wallet(policy)

    psbt = PSBT()
    psbt.deserialize(unsigned_psbt)

    partial_sigs = client.sign_psbt(psbt, policy, policy_hmac)

    apply_signatures_to_psbt(psbt, partial_sigs)
    return psbt.serialize()


def apply_signatures_to_psbt(psbt: Any, partial_sigs: list) -> Any:
    """
    Apply the partial signatures returned by ``client.sign_psbt()`` back to the
    PSBT object so callers can serialise and pass it to rgb_lib for finalisation.

    Parameters
    ----------
    psbt:
        A ``ledger_bitcoin.psbt.PSBT`` instance (already deserialized).
    partial_sigs:
        The list of ``(input_index, SignPsbtYieldedObject)`` tuples returned by
        ``client.sign_psbt()``.

    Returns
    -------
    The same PSBT object with signatures applied in-place.
    """
    for input_index, sig_obj in partial_sigs:
        if input_index >= len(psbt.inputs):
            logger.warning(
                '[LedgerHW] Signature for out-of-range input %d ignored', input_index,
            )
            continue

        inp = psbt.inputs[input_index]

        if not isinstance(sig_obj, PartialSignature):
            # MusigPubNonce / MusigPartialSignature — not handled here
            logger.debug(
                '[LedgerHW] Skipping non-PartialSignature for input %d', input_index,
            )
            continue

        if sig_obj.tapleaf_hash is not None:
            # Taproot script-path: key is (xonly_pubkey[32], tapleaf_hash[32])
            inp.tap_script_sigs[(sig_obj.pubkey, sig_obj.tapleaf_hash)] = sig_obj.signature
            logger.debug('[LedgerHW] Applied tap_script_sig for input %d', input_index)
        elif len(sig_obj.pubkey) == 32:
            # Taproot key-path
            inp.tap_key_sig = sig_obj.signature
            logger.debug('[LedgerHW] Applied tap_key_sig for input %d', input_index)
        else:
            # Legacy / segwit
            inp.partial_sigs[sig_obj.pubkey] = sig_obj.signature
            logger.debug('[LedgerHW] Applied partial_sig for input %d', input_index)

    return psbt
