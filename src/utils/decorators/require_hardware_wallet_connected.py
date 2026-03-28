"""
Decorator to ensure a hardware wallet device is connected and a client is initialized before executing the decorated function.
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.hardware_client_store import hardware_client_store
from src.utils.ledger_hw_client import create_ledger_client
from src.utils.ledger_hw_client import enumerate_ledger_devices
from src.utils.local_store import local_store
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
                devices = enumerate_ledger_devices()

                if not devices:
                    raise RuntimeError(
                        'No hardware wallet device found. Please connect your device.',
                    )

                # Select device matching the stored fingerprint when possible
                preferred_fingerprint = local_store.get_value(
                    MASTER_FINGERPRINT,
                )
                device_info = None
                if preferred_fingerprint:
                    for d in devices:
                        if d.get('fingerprint') == preferred_fingerprint:
                            device_info = d
                            break

                # Fall back to the first healthy device
                if device_info is None:
                    device_info = next(
                        (d for d in devices if not d.get('error')),
                        None,
                    )

                if device_info is None:
                    raise RuntimeError(
                        'No accessible Ledger device found.',
                    )

                network = SettingRepository.get_wallet_network()
                if network is None:
                    raise ValueError('Network must be specified.')

                client = create_ledger_client(device_info)
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
                    client.stop()

        return wrapper

    return decorator
