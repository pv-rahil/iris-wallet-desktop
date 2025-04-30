"""
This module contains custom decoratorsto insure node unlocked.
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable

import rgb_lib
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError

import src.flavour as bitcoin_network
from src.data.repository.setting_repository import SettingRepository
from src.data.repository.wallet_holder import WalletHolder
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.build_app_path import app_paths
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.error_message import ERROR_NODE_IS_LOCKED_CALL_UNLOCK
from src.utils.error_message import ERROR_NODE_WALLET_NOT_INITIALIZED
from src.utils.error_message import ERROR_PASSWORD_INCORRECT
from src.utils.handle_exception import CommonException
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.keyring_storage import get_value
from src.utils.logging import logger
from src.utils.page_navigation_events import PageNavigationEventManager


def unlock_node() -> Any:
    """Unlock the node by sending a request to the unlock endpoint."""
    try:
        password = None
        keyring_status = SettingRepository.get_keyring_status()
        if keyring_status is False:
            password = get_value(
                WALLET_PASSWORD_KEY,
                network=bitcoin_network.__network__,
            )
        init = WalletHolder.get_init_response()
        network: NetworkEnumModel = SettingRepository.get_wallet_network()
        network = get_bitcoin_network_from_enum(network)
        wallet_data_args = WalletRequestModel(
            data_dir=app_paths.app_path, bitcoin_network=network, pubkey=init.account_xpub, mnemonic=init.mnemonic,
        )
        wallet_data = rgb_lib.WalletData(
            **wallet_data_args, database_type=rgb_lib.DatabaseType.SQLITE,
        )

        # Initialize the wallet
        wallet = rgb_lib.Wallet(wallet_data)
        WalletHolder.set_wallet(wallet)
        return True
    except HTTPError as error:
        error_data = error.response.json()
        error_message = error_data.get('error', 'Unhandled error')
        if error_data.get('error') == ERROR_PASSWORD_INCORRECT and error_data.get('code') == 401:
            PageNavigationEventManager.get_instance().enter_wallet_password_page_signal.emit()
        if error_data.get('error') == ERROR_NODE_WALLET_NOT_INITIALIZED and error_data.get('code') == 403:
            SettingRepository.unset_wallet_initialized()
            PageNavigationEventManager.get_instance().term_and_condition_page_signal.emit()
        logger.error(error_message)
        raise CommonException(error_message) from error
    except RequestsConnectionError as exc:
        logger.error(
            'Exception occurred at Decorator(unlock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException('Unable to connect to node') from exc
    except Exception as exc:
        logger.error(
            'Exception occurred at Decorator(unlock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        PageNavigationEventManager.get_instance().term_and_condition_page_signal.emit()
        raise CommonException(
            'Unable to unlock node',
        ) from exc


def is_node_locked() -> bool:
    """Check if the node is locked by sending a request to the node info endpoint."""
    try:
        # response = Request.get(NODE_INFO_ENDPOINT)
        # response.raise_for_status()
        return False
    except HTTPError as error:
        if error.response.status_code == 403:
            try:
                error_data = error.response.json()
                if error_data.get('error') == ERROR_NODE_IS_LOCKED_CALL_UNLOCK and error_data.get('code') == 403:
                    return True
            except ValueError:
                pass
        else:
            error_data = error.response.json()
            error_message = error_data.get('error', 'Unhandled error')
            logger.error(error_message)
            raise CommonException(error_message) from error
    except RequestsConnectionError as exc:
        logger.error(
            'Exception occurred at Decorator(unlock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException('Unable to connect to node') from exc
    except Exception as exc:
        logger.error(
            'Exception occurred at Decorator(unlock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException(
            'Decorator(unlock_required): Error while checking if node is locked',
        ) from exc

    return False


def unlock_required(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to ensure the node is unlocked before proceeding with the decorated method."""
    @wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if is_node_locked():
            unlock_node()
        return method(*args, **kwargs)
    return wrapper
