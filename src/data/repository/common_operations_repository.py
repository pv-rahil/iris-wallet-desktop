"""Module containing CommonOperationRepository."""
from __future__ import annotations

from rgb_lib import DatabaseType
from rgb_lib import Keys
from rgb_lib import rgb_lib

from src.data.repository.wallet_holder import colored_wallet
from src.model.common_operation_model import BackupRequestModel
from src.model.common_operation_model import BackupResponseModel
from src.model.common_operation_model import ChangePasswordRequestModel
from src.model.common_operation_model import ChangePassWordResponseModel
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import LockResponseModel
from src.model.common_operation_model import RestoreRequestModel
from src.model.common_operation_model import RestoreResponseModel
from src.model.common_operation_model import SendOnionMessageRequestModel
from src.model.common_operation_model import SendOnionMessageResponseModel
from src.model.common_operation_model import ShutDownResponseModel
from src.model.common_operation_model import SignMessageRequestModel
from src.model.common_operation_model import SignMessageResponseModel
from src.model.common_operation_model import WalletRequestModel
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.lock_required import lock_required
from src.utils.decorators.unlock_required import unlock_required
from src.utils.endpoints import CHANGE_PASSWORD_ENDPOINT
from src.utils.endpoints import LOCK_ENDPOINT
from src.utils.endpoints import RESTORE_ENDPOINT
from src.utils.endpoints import SEND_ONION_MESSAGE_ENDPOINT
from src.utils.endpoints import SHUTDOWN_ENDPOINT
from src.utils.endpoints import SIGN_MESSAGE_ENDPOINT
from src.utils.request import Request
# from src.model.common_operation_model import NetworkInfoResponseModel
# from src.model.common_operation_model import NodeInfoResponseModel
# from src.utils.endpoints import NETWORK_INFO_ENDPOINT


class CommonOperationRepository:
    """Repository for handling common operations."""

    @staticmethod
    def init(init: InitRequestModel) -> Keys:
        """Initialize and generate RGB keys for the given Bitcoin network."""
        with repository_custom_context():
            response: Keys = rgb_lib.generate_keys(init.network)
            return response

    @staticmethod
    def unlock(unlock: WalletRequestModel):
        """Unlock operation."""
        with repository_custom_context():
            wallet_data = rgb_lib.WalletData(
                data_dir=unlock.data_dir, bitcoin_network=unlock.bitcoin_network, database_type=DatabaseType.SQLITE,
                max_allocations_per_utxo=unlock.max_allocations_per_utxo, pubkey=unlock.pubkey, mnemonic=unlock.mnemonic,
                vanilla_keychain=unlock.vanilla_keychain,
            )
            # Initialize the wallet
            recv_wallet = rgb_lib.Wallet(wallet_data)
            colored_wallet.set_wallet(recv_wallet)
            return recv_wallet

    # @staticmethod
    # # @unlock_required
    # def node_info() -> NodeInfoResponseModel:
    #     """Node info operation."""
    #     # with repository_custom_context():
    #     #     response = Request.get(NODE_INFO_ENDPOINT)
    #     #     response.raise_for_status()  # Raises an exception for HTTP errors
    #     #     data = response.json()
    #     #     return NodeInfoResponseModel(**data)
    #     pass  # pylint:disable=unnecessary-pass
    #     return None

    # @staticmethod
    # # @unlock_required
    # def network_info() -> NetworkInfoResponseModel:
    #     """Network info operation."""
    #     with repository_custom_context():
    #         response = Request.get(NETWORK_INFO_ENDPOINT)
    #         response.raise_for_status()  # Raises an exception for HTTP errors
    #         data = response.json()
    #         return NetworkInfoResponseModel(**data)

    @staticmethod
    def lock() -> LockResponseModel:
        """Lock operation."""
        with repository_custom_context():
            response = Request.post(LOCK_ENDPOINT)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return LockResponseModel(status=True)

    @staticmethod
    def backup(backup: BackupRequestModel) -> BackupResponseModel:
        """Backup operation."""
        with repository_custom_context():
            colored_wallet.wallet.backup(
                backup_path=backup.backup_path, password=backup.password,
            )
            return BackupResponseModel(status=True)

    @staticmethod
    @lock_required
    def change_password(
        change_password: ChangePasswordRequestModel,
    ) -> ChangePassWordResponseModel:
        """Change password operation."""
        payload = change_password.dict()
        with repository_custom_context():
            response = Request.post(CHANGE_PASSWORD_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return ChangePassWordResponseModel(status=True)

    @staticmethod
    @lock_required
    def restore(restore: RestoreRequestModel) -> RestoreResponseModel:
        """Restore operation."""
        payload = restore.dict()
        with repository_custom_context():
            response = Request.post(RESTORE_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return RestoreResponseModel(status=True)

    @staticmethod
    @unlock_required
    def send_onion_message(
        send_onion_message: SendOnionMessageRequestModel,
    ) -> SendOnionMessageResponseModel:
        """Send onion message operation."""
        payload = send_onion_message.dict()
        with repository_custom_context():
            response = Request.post(SEND_ONION_MESSAGE_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return SendOnionMessageResponseModel(status=True)

    @staticmethod
    @unlock_required
    def shutdown() -> ShutDownResponseModel:
        """Shutdown operation."""
        with repository_custom_context():
            response = Request.post(SHUTDOWN_ENDPOINT)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return ShutDownResponseModel(status=True)

    @staticmethod
    @unlock_required
    def sign_message(sign_message: SignMessageRequestModel) -> SignMessageResponseModel:
        """Sign message operation."""
        payload = sign_message.dict()
        with repository_custom_context():
            response = Request.post(SIGN_MESSAGE_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return SignMessageResponseModel(**data)
