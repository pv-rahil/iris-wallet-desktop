"""
Decorator to ensure a hardware wallet device is connected and a client is initialized before executing the decorated function.
"""
from __future__ import annotations

import time
from functools import wraps
from typing import Any
from typing import Callable

from hwilib.commands import enumerate as hwi_enumerate
from hwilib.common import Chain
from hwilib.devices.ledger import LedgerClient

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.hardware_client_store import hardware_client_store
from src.utils.logging import logger


def require_hardware_wallet_connected() -> Callable[..., Any]:
    """
    Decorator to ensure a hardware wallet is connected and the Ledger client is initialized.
    Refreshes the device connection every 5 seconds or if client is missing.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        last_enumerate_time = 0.0
        last_device_path = None

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal last_enumerate_time, last_device_path

            # Only proceed if hardware wallet is required
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
                if (not client) or (now - last_enumerate_time > 5.0):
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
                        raise RuntimeError(
                            'No device path found in HWI enumerate result.',
                        )

                    # If device path changed or client is missing, recreate client
                    if (not client) or (device_path != last_device_path):
                        network = SettingRepository.get_wallet_network()
                        if network is None:
                            raise ValueError('Network must be specified.')

                        chain = {
                            NetworkEnumModel.MAINNET: Chain.MAIN,
                            NetworkEnumModel.TESTNET: Chain.TEST,
                            NetworkEnumModel.REGTEST: Chain.REGTEST,
                        }.get(network)
                        # Close previous client if it exists
                        if client:
                            try:
                                client.close()
                            except Exception as e:
                                logger.warning(
                                    'Failed to close previous LedgerClient: %s', e,
                                )
                        client = LedgerClient(device_path, None, True, chain)
                        hardware_client_store.set_client(client)
                        last_device_path = device_path

                return func(*args, **kwargs)

            except Exception as e:
                logger.error('[HW Wallet Decorator] Exception: %s', e)
                hardware_client_store.set_client(None)
                last_device_path = None
                raise RuntimeError(
                    f"Hardware wallet connection failed: {e}",
                ) from e

        return wrapper

    return decorator
