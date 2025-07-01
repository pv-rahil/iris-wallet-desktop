"""Service module for common operation in application"""
from __future__ import annotations

from rgb_lib import Keys
from rgb_lib import RgbLibError
from rgb_lib import Wallet

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import UnlockResponseModel
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletSecurityType
from src.utils.build_app_path import app_paths
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import MASTER_FINGERPRINT
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
    and unlocking of a wallet. It ensures that the wallet operates in the correct network
    context and handles exceptions during these operations.
    """

    @staticmethod
    def initialize_wallet(password: str) -> tuple[Keys, str]:
        """
        Initializes the wallet with the provided password, unlocks it, and verifies
        that the wallet's network matches the expected network.
        """
        try:
            stored_network: NetworkEnumModel = SettingRepository.get_wallet_network()
            network = get_bitcoin_network_from_enum(
                stored_network,
            )

            # Check if this is a watch-only wallet
            security_type = SettingRepository.get_wallet_security_type()
            is_watch_only = security_type == WalletSecurityType.WATCH_ONLY

            response: Keys | None = None
            wallet: Wallet | None = None

            if is_watch_only:
                account_xpub_colored = local_store.get_value(
                    ACCOUNT_XPUB_COLORED,
                )
                account_xpub_vanilla = local_store.get_value(
                    ACCOUNT_XPUB_VANILLA,
                )
                master_fingerprint = local_store.get_value(MASTER_FINGERPRINT)

                if not account_xpub_vanilla or not account_xpub_colored or not master_fingerprint:
                    raise CommonException(
                        'Watch-only wallet xpubs and fingerprint not found. Please set up watch-only wallet first.',
                    )

                # Create a Keys object for watch-only wallets using stored values
                response = Keys(
                    account_xpub_vanilla=account_xpub_vanilla,
                    account_xpub_colored=account_xpub_colored,
                    mnemonic=None,
                    master_fingerprint=master_fingerprint,
                    xpub=None,
                )

                wallet = CommonOperationRepository.unlock(
                    WalletRequestModel(
                        data_dir=app_paths.app_path, bitcoin_network=network,
                        account_xpub_vanilla=account_xpub_vanilla, account_xpub_colored=account_xpub_colored,
                        mnemonic=None, master_fingerprint=master_fingerprint,
                    ),
                )
            else:
                # For regular wallets, generate new keys
                response = CommonOperationRepository.init(
                    InitRequestModel(password=password, network=network),
                )

                wallet = CommonOperationRepository.unlock(
                    WalletRequestModel(
                        data_dir=app_paths.app_path, bitcoin_network=network,
                        account_xpub_vanilla=response.account_xpub_vanilla,
                        account_xpub_colored=response.account_xpub_colored,
                        mnemonic=response.mnemonic, master_fingerprint=response.master_fingerprint,
                    ),
                )
                mnemonic_store.decrypted_mnemonic = response.mnemonic

            colored_wallet.set_wallet(wallet)
            return response, password
        except (CommonException, RgbLibError) as exc:
            return handle_exceptions(exc=exc)

    @staticmethod
    def enter_wallet_password(password: str) -> UnlockResponseModel:
        """
        Unlocks the wallet with the provided password,
        and verifies that the wallet's network matches the expected network.
        """
        try:
            stored_network: NetworkEnumModel = get_bitcoin_network_from_enum(
                SettingRepository.get_wallet_network(),
            )
            network = get_bitcoin_network_from_enum(
                stored_network,
            )
            account_xpub_vanilla = local_store.get_value(ACCOUNT_XPUB_VANILLA)
            account_xpub_colored = local_store.get_value(ACCOUNT_XPUB_COLORED)
            master_fingerprint = local_store.get_value(MASTER_FINGERPRINT)

            # Check if this is a watch-only wallet
            is_watch_only = SettingRepository.get_wallet_security_type(
            ) == WalletSecurityType.WATCH_ONLY

            if is_watch_only:
                # For watch-only wallets, use None mnemonic
                decrypted_mnemonic = None
            else:
                # For regular wallets, decrypt mnemonic from file
                decrypted_mnemonic = mnemonic_store.decrypt(
                    password=password, path=app_paths.mnemonic_file_path,
                )

            response: UnlockResponseModel = CommonOperationRepository.unlock(
                WalletRequestModel(
                    data_dir=app_paths.app_path, bitcoin_network=network,
                    account_xpub_vanilla=account_xpub_vanilla, account_xpub_colored=account_xpub_colored,
                    mnemonic=decrypted_mnemonic, master_fingerprint=master_fingerprint,
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
