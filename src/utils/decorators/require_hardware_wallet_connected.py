"""
Decorator to ensure a hardware wallet device is connected and a client is initialized before executing the decorated function.
"""
from __future__ import annotations

import time
from functools import wraps

from hwilib.commands import enumerate as hwi_enumerate
from hwilib.common import Chain
from hwilib.devices.ledger import LedgerClient

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.hardware_client_store import hardware_client_store
from src.utils.logging import logger
# Example: adjust this import to your actual HWI interface


def require_hardware_wallet_connected():
    """
    Decorator to ensure a hardware wallet device is connected (using HWI enumerate, checked every 5 seconds)
    and a client is initialized and stored in hardware_client_store. If the device is disconnected or changes,
    the client is recreated.
    """
    def decorator(func):
        last_enumerate_time = 0
        last_device_path = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if this is a hardware wallet - if not, just call the function
            key_storage_type = SettingRepository.get_key_storage_type()
            if key_storage_type != KeyStorageType.HARDWARE_WALLET:
                return func(*args, **kwargs)

            nonlocal last_enumerate_time, last_device_path
            try:
                now = time.time()
                client = hardware_client_store.client
                device_path = last_device_path
                # Check if client is None or closed
                # Refresh device status every 5 seconds or if no client
                if (not client) or (now - last_enumerate_time > 5):
                    devices = hwi_enumerate()
                    last_enumerate_time = now
                    if not devices:
                        hardware_client_store.set_client(None)
                        last_device_path = None
                        raise RuntimeError(
                            'No hardware wallet device found. Please connect your device.',
                        )
                    device_info = devices[0]
                    device_path = device_info.get('path')
                    if not device_path:
                        hardware_client_store.set_client(None)
                        last_device_path = None
                        raise RuntimeError(
                            'No device path found in HWI enumerate result.',
                        )
                    # If device changed or client is missing, recreate client
                    if (not client) or (device_path != last_device_path):
                        network: NetworkEnumModel = SettingRepository.get_wallet_network()
                        if network is None:
                            raise ValueError(
                                "NetworkEnumModel must be provided as a kwarg 'network' or as a positional argument.",
                            )
                        if network == NetworkEnumModel.MAINNET:
                            chain = Chain.MAIN
                        elif network == NetworkEnumModel.TESTNET:
                            chain = Chain.TEST
                        else:
                            chain = Chain.REGTEST
                        client = LedgerClient(
                            device_path, None, True, Chain.RGB,
                        )
                        hardware_client_store.set_client(client)
                        last_device_path = device_path
                return func(*args, **kwargs)
            except Exception as e:
                hardware_client_store.set_client(None)
                last_device_path = None
                logger.error('[HardwareWalletDecorator] Exception: %s', e)
                raise RuntimeError(
                    f"Hardware wallet connection failed: {e}",
                ) from e
        return wrapper
    return decorator
