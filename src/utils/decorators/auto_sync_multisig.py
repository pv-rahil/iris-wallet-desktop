"""
Decorator for automatically syncing multisig wallets with the bridge.
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable

from rgb_lib import Operation

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletType
from src.utils.handle_exception import CommonException
from src.utils.logging import logger


def is_blocking_operation(op: Operation) -> bool:
    """
    Check if an operation is blocking (pending or review).
    """
    return (
        op.is_CREATE_UTXOS_TO_REVIEW()
        or op.is_CREATE_UTXOS_PENDING()
        or op.is_SEND_BTC_TO_REVIEW()
        or op.is_SEND_BTC_PENDING()
        or op.is_SEND_TO_REVIEW()
        or op.is_SEND_PENDING()
        or op.is_INFLATION_TO_REVIEW()
        or op.is_INFLATION_PENDING()
    )


def auto_sync_multisig(check_pending_ops: bool = False) -> Callable[..., Any]:
    """
    Decorator to automatically sync with the multisig bridge
    and block execution if a pending/review operation exists.
    """

    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if colored_wallet.is_multisig:
                if SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET:
                    return method(*args, **kwargs)
                try:
                    logger.info('Auto-syncing multisig wallet...')
                    sync_result = colored_wallet.wallet.sync_with_bridge(
                        online=colored_wallet.online,
                    )

                    # Block if pending/review operation exists
                    if (
                        check_pending_ops
                        and sync_result
                    ):
                        logger.warning(
                            'Multisig operation already in progress: %s',
                            sync_result.operation.__class__.__name__,
                        )
                        raise CommonException(
                            'A multisig operation is already pending or under review. '
                            'Please complete it before creating a new PSBT.',
                        )

                except CommonException:
                    raise
                except Exception as exc:
                    logger.error(
                        'Failed to auto-sync multisig wallet: %s',
                        exc,
                    )
                    raise CommonException(
                        'Failed to sync with bridge',
                    ) from exc

            return method(*args, **kwargs)

        return wrapper

    return decorator
