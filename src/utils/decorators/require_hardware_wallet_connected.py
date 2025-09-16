"""
Decorator to ensure a hardware wallet device is connected and a client is initialized before executing the decorated function.
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable

from hwilib.commands import enumerate as hwi_enumerate
from hwilib.common import Chain
from hwilib.devices.ledger import LedgerClient
from hwilib.devices.ledger_bitcoin.client import Client
from hwilib.devices.ledger_bitcoin.exception import NotSupportedError
from hwilib.errors import DeviceConnectionError

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.custom_exception import CommonException
from src.utils.hardware_client_store import hardware_client_store
from src.utils.logging import logger


def require_hardware_wallet_connected() -> Callable[..., Any]:
    """
    Decorator to ensure a hardware wallet is connected and the Ledger client is initialized.
    Always creates a fresh client before the decorated function and closes it after.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key_storage_type = SettingRepository.get_key_storage_type()
            if key_storage_type != KeyStorageType.HARDWARE_WALLET:
                return func(*args, **kwargs)

            client = None

            try:
                devices = hwi_enumerate(allow_emulators=True)

                if not devices:
                    raise RuntimeError(
                        'No hardware wallet device found. Please connect your device.',
                    )

                device_info = devices[0]
                device_path = device_info.get('path')
                if not device_path:
                    raise RuntimeError(
                        'No device path found in HWI enumerate result.',
                    )

                network = SettingRepository.get_wallet_network()
                if network is None:
                    raise ValueError('Network must be specified.')

                chain = {
                    NetworkEnumModel.MAINNET: Chain.MAIN,
                    NetworkEnumModel.TESTNET: Chain.TEST,
                    NetworkEnumModel.REGTEST: Chain.REGTEST,
                }.get(network)

                is_rgb_mode = hardware_client_store.get_rgb_mode()
                client = LedgerClient(
                    path=device_path,
                    password=None,
                    expert=True,
                    chain=chain,
                    is_rgb=is_rgb_mode,
                )

                base_client = Client(client.transport_client)
                app_name, app_version, _ = base_client.get_version()
                hardware_client_store.set_client(client)

                return func(*args, **kwargs)

            except Exception as e:
                logger.error('[HW Wallet Decorator] Exception: %s', e)
                hardware_client_store.stop_client()
                raise RuntimeError(
                    f"Hardware wallet connection failed: {e}",
                ) from e

            finally:
                hardware_client_store.clear_rgb_mode()
                if client:
                    client.close()

        return wrapper

    return decorator
