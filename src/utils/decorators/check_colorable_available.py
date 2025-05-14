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

from src.data.repository.setting_card_repository import SettingCardRepository
from src.data.repository.wallet_holder import colored_wallet
from src.model.rgb_model import CreateUtxosRequestModel
from src.model.setting_model import DefaultFeeRate
from src.utils.cache import Cache
from src.utils.error_message import ERROR_CREATE_UTXO_FEE_RATE_ISSUE
from src.utils.error_message import ERROR_MESSAGE_TO_CHANGE_FEE_RATE
from src.utils.handle_exception import CommonException
from src.utils.logging import logger


def create_utxos() -> None:
    """Create UTXOs for RGB operations by calling the wallet's create_utxos method."""
    try:
        default_fee_rate: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
        create_utxos_model = CreateUtxosRequestModel(
            online=colored_wallet.online,
            fee_rate=default_fee_rate.fee_rate,
            num=2,
        )
        colored_wallet.wallet.create_utxos(
            online=create_utxos_model.online, up_to=create_utxos_model.up_to,
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
        logger.error(
            'Exception occurred at Decorator(unlock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException(
            'Decorator(check_colorable_available): Error while calling create utxos',
        ) from exc


def check_colorable_available() -> Callable[..., Any]:
    """
    Decorator to check if colorable UTXOs are available. If not, it calls create_utxos
    and retries the original method.

    :param create_utxos: Fallback function to create UTXOs when insufficient UTXOs are available.
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
                    create_utxos()  # Fallback call to create UTXOs
                    # Retry the original function
                    return method(*args, **kwargs)
                except RgbLibError.InsufficientAllocationSlots as exc:
                    raise CommonException('NoAvailableUtxos') from exc
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
