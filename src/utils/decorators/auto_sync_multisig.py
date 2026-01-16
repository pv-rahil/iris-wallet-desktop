"""
Decorator for automatically syncing multisig wallets with the bridge.
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable

from src.data.repository.colored_wallet import colored_wallet
from src.utils.handle_exception import CommonException
from src.utils.logging import logger


def auto_sync_multisig(before: bool = False, after: bool = True) -> Callable[..., Any]:
    """
    Decorator to automatically sync with the multisig bridge before and/or after the method execution
    if the current wallet is a multisig wallet.

    :param before: Whether to sync before the method execution (default: False)
    :param after: Whether to sync after the method execution (default: True)
    """
    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Sync before execution
            if before and colored_wallet.is_multisig:
                try:
                    logger.info('Auto-syncing multisig wallet (before)...')
                    colored_wallet.wallet.sync_with_bridge(
                        online=colored_wallet.online,
                    )
                except Exception as exc:
                    logger.error(
                        'Failed to auto-sync multisig wallet (before): %s',
                        exc,
                    )
                    raise CommonException(
                        'Failed to sync with bridge',
                    ) from exc

            result = method(*args, **kwargs)

            # Sync after execution
            if after and colored_wallet.is_multisig:
                try:
                    logger.info('Auto-syncing multisig wallet (after)...')
                    colored_wallet.wallet.sync_with_bridge(
                        online=colored_wallet.online,
                    )
                except Exception as exc:
                    logger.error(
                        'Failed to auto-sync multisig wallet (after): %s',
                        exc,
                    )
                    raise CommonException(
                        'Failed to sync with bridge after operation',
                    ) from exc

            return result
        return wrapper
    return decorator
