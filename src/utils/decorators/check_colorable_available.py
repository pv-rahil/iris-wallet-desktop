"""
This module contains custom decorators.
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from rgb_lib import RgbLibError

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.setting_card_repository import SettingCardRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import CreateUtxosRequestModel
from src.model.setting_model import DefaultFeeRate
from src.utils.cache import Cache
from src.utils.error_message import ERROR_CREATE_UTXO_FEE_RATE_ISSUE
from src.utils.error_message import ERROR_MESSAGE_TO_CHANGE_FEE_RATE
from src.utils.handle_exception import CommonException
from src.utils.logging import logger


def get_unspent_utxo_count() -> int:
    """Get the count of unspent UTXOs that are not assigned to any RGB asset."""
    try:
        unspents = colored_wallet.wallet.list_unspents(
            online=colored_wallet.online, settled_only=False, skip_sync=False,
        )

        return len([
            u for u in unspents
            if not u.rgb_allocations and u.utxo.colorable
        ])
    except Exception as exc:
        logger.error(
            'Error getting unspent UTXO count: %s: %s',
            type(exc).__name__, str(exc),
        )
        return 0


def create_utxos(num: int) -> None:
    """Create UTXOs for RGB operations by calling the wallet's create_utxos method.

    :param num: exact number of UTXOs to create in a single transaction
    """
    try:
        default_fee_rate: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
        key_storage_type = SettingRepository.get_key_storage_type()
        wallet_type = SettingRepository.get_wallet_type()
        wallet_access_type = SettingRepository.get_wallet_access_type()
        wallet_signature_type = SettingRepository.get_wallet_signature_type()
        create_utxos_model = CreateUtxosRequestModel(
            online=colored_wallet.online,
            fee_rate=default_fee_rate.fee_rate,
            num=num,
        )
        if (key_storage_type == KeyStorageType.HARDWARE_WALLET and wallet_type == WalletType.ONLINE_TYPE_WALLET) \
                or wallet_access_type == WalletAccessType.WATCH_ONLY \
                or wallet_signature_type == WalletSignatureType.MULTI_SIG_WALLET:
            raise CommonException('NoAvailableUtxos')
        colored_wallet.wallet.create_utxos(
            online=create_utxos_model.online, up_to=False,
            num=create_utxos_model.num, size=create_utxos_model.size,
            fee_rate=create_utxos_model.fee_rate, skip_sync=create_utxos_model.skip_sync,
        )
        cache = Cache.get_cache_session()
        if cache is not None:
            cache.invalidate_cache()
    except HTTPError as error:
        error_data = error.response.json()
        error_message = error_data.get('error', 'Unhandled error')
        logger.error(error_message)
        if error_message == ERROR_CREATE_UTXO_FEE_RATE_ISSUE:
            raise CommonException(ERROR_MESSAGE_TO_CHANGE_FEE_RATE) from error
        raise CommonException(error_message) from error
    except RequestsConnectionError as exc:
        logger.error(
            'Exception occurred at Decorator(unlock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException('Unable to connect to wallet') from exc
    except Exception as exc:
        if (key_storage_type == KeyStorageType.HARDWARE_WALLET and wallet_type == WalletType.ONLINE_TYPE_WALLET) \
                or wallet_access_type == WalletAccessType.WATCH_ONLY \
                or wallet_signature_type == WalletSignatureType.MULTI_SIG_WALLET:
            raise exc
        logger.error(
            'Exception occurred at Decorator: %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException(
            'Decorator(check_colorable_available): Error while calling create utxos',
        ) from exc


def check_colorable_available(required_utxos: int = 1) -> Callable[..., Any]:
    """
    Ensure at least `required_utxos` uncolored UTXOs exist. If insufficient, create only the missing
    count in a single transaction and retry the original method.

    :param required_utxos: Number of uncolored UTXOs required (default: 2)
    """
    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Attempt to execute the main function
                return method(*args, **kwargs)
            except RgbLibError.InsufficientAllocationSlots:
                # If the error is due to insufficient uncolored UTXOs, call the fallback
                try:
                    current = get_unspent_utxo_count()
                    needed = required_utxos - current
                    if needed > 0:
                        create_utxos(num=needed)
                    # Retry the original function
                    return method(*args, **kwargs)
                except RgbLibError.InsufficientAllocationSlots as exc:
                    key_storage_type = SettingRepository.get_key_storage_type()
                    wallet_type = SettingRepository.get_wallet_type()
                    wallet_access_type = SettingRepository.get_wallet_access_type()
                    wallet_signature_type = SettingRepository.get_wallet_signature_type()
                    if (key_storage_type == KeyStorageType.HARDWARE_WALLET and wallet_type == WalletType.ONLINE_TYPE_WALLET) \
                            or wallet_access_type == WalletAccessType.WATCH_ONLY \
                            or wallet_signature_type == WalletSignatureType.MULTI_SIG_WALLET:
                        raise CommonException('NoAvailableUtxos') from exc
                    create_utxos(num=needed)
                    return method(*args, **kwargs)
                except CommonException:
                    raise
                except Exception as fallback_exc:
                    # If the fallback function fails, wrap the error in a CommonException
                    raise CommonException(
                        f"Failed to create UTXOs in fallback. Error: {
                            str(fallback_exc)
                        }",
                    ) from fallback_exc
                # If it's another type of error, re-raise it
                raise
            except CommonException:
                raise
            except Exception as exc:
                # Catch any other generic exceptions and wrap them in CommonException
                error = str(exc)
                raise CommonException(
                    f"Decorator(check_colorable_available): {error}",
                ) from exc
        return wrapper
    return decorator
