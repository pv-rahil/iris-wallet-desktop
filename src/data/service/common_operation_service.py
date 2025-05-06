"""Service module for common operation in application"""
from __future__ import annotations

from rgb_lib import Keys
from rgb_lib import Wallet

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.repository.wallet_holder import colored_wallet
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import UnlockResponseModel
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.build_app_path import app_paths
from src.utils.constant import ACCOUNT_XPUB
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_KEYRING_STORE_NOT_ACCESSIBLE
from src.utils.error_message import ERROR_UNABLE_GET_MNEMONIC
from src.utils.error_message import ERROR_UNABLE_TO_GET_HASHED_MNEMONIC
from src.utils.handle_exception import handle_exceptions
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.helpers import hash_mnemonic
from src.utils.keyring_storage import set_value
from src.utils.local_store import local_store
from src.utils.wallet_credential_encryption import mnemonic_store


class CommonOperationService:
    """
    The CommonOperationService class provides static methods for managing the initialization
    and unlocking of a wallet within a Lightning Network node environment. It ensures
    that the wallet operates in the correct network context and handles exceptions during these operations.
    """

    @staticmethod
    def initialize_wallet(password: str) -> tuple[Keys, str]:
        """
        Initializes the wallet with the provided password, unlocks it, and verifies
        that the node's network matches the expected network.
        """
        try:
            stored_network: NetworkEnumModel = SettingRepository.get_wallet_network()
            network = get_bitcoin_network_from_enum(
                stored_network,
            )
            response: Keys = CommonOperationRepository.init(
                InitRequestModel(password=password, network=network),
            )
            wallet: Wallet = CommonOperationRepository.unlock(
                WalletRequestModel(
                    data_dir=app_paths.app_path, bitcoin_network=network,
                    account_xpub=response.account_xpub, mnemonic=response.mnemonic,
                ),
            )
            colored_wallet.set_wallet(wallet)
            mnemonic_store.decrypted_mnemonic = response.mnemonic
            return response, password
        except CommonException as exc:
            return handle_exceptions(exc=exc)

    @staticmethod
    def enter_wallet_password(password: str) -> UnlockResponseModel:
        """
        Unlocks the wallet with the provided password after ensuring the node is locked,
        and verifies that the node's network matches the expected network.
        """
        try:
            stored_network: NetworkEnumModel = get_bitcoin_network_from_enum(
                SettingRepository.get_wallet_network(),
            )
            network = get_bitcoin_network_from_enum(
                stored_network,
            )
            account_xpub = local_store.get_value(ACCOUNT_XPUB)
            decrypted_mnemonic = mnemonic_store.decrypt(
                password=password, path=app_paths.mnemonic_file_path,
            )
            response: UnlockResponseModel = CommonOperationRepository.unlock(
                WalletRequestModel(
                    data_dir=app_paths.app_path, bitcoin_network=network,
                    account_xpub=account_xpub, mnemonic=decrypted_mnemonic,
                ),
            )
            return response
        except Exception as exc:
            return handle_exceptions(exc=exc)

    @staticmethod
    def keyring_toggle_enable_validation(password: str):
        """validate keyring enable """
        try:
            network: NetworkEnumModel = SettingRepository.get_wallet_network()
            is_password_stored = set_value(
                WALLET_PASSWORD_KEY, password, network.value,
            )
            if is_password_stored is False:
                raise CommonException(ERROR_KEYRING_STORE_NOT_ACCESSIBLE)
            SettingRepository.set_keyring_status(status=False)
        except Exception as exc:
            handle_exceptions(exc=exc)

    @staticmethod
    def get_hashed_mnemonic(mnemonic):
        """This method returns the hashed mnemonic"""
        if not mnemonic:
            raise CommonException(ERROR_UNABLE_GET_MNEMONIC)

        hashed_mnemonic = hash_mnemonic(mnemonic_phrase=mnemonic)

        if not hashed_mnemonic:
            raise CommonException(ERROR_UNABLE_TO_GET_HASHED_MNEMONIC)

        return hashed_mnemonic
