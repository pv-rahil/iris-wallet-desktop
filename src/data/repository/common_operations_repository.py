"""Module containing CommonOperationRepository."""
from __future__ import annotations

from src.data.repository.setting_repository import SettingRepository
from src.data.repository.wallet_holder import WalletHolder
from src.model.common_operation_model import BackupRequestModel, WalletRequestModel
from src.model.common_operation_model import BackupResponseModel
from src.model.common_operation_model import ChangePasswordRequestModel
from src.model.common_operation_model import ChangePassWordResponseModel
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import InitResponseModel
from src.model.common_operation_model import LockResponseModel
from src.model.common_operation_model import NetworkInfoResponseModel
from src.model.common_operation_model import NodeInfoResponseModel
from src.model.common_operation_model import RestoreRequestModel
from src.model.common_operation_model import RestoreResponseModel
from src.model.common_operation_model import SendOnionMessageRequestModel
from src.model.common_operation_model import SendOnionMessageResponseModel
from src.model.common_operation_model import ShutDownResponseModel
from src.model.common_operation_model import SignMessageRequestModel
from src.model.common_operation_model import SignMessageResponseModel
from src.model.common_operation_model import UnlockRequestModel
from src.model.common_operation_model import UnlockResponseModel
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.is_node_initialized import is_node_initialized
from src.utils.decorators.lock_required import lock_required
from src.utils.decorators.unlock_required import unlock_required
from src.utils.endpoints import BACKUP_ENDPOINT
from src.utils.endpoints import CHANGE_PASSWORD_ENDPOINT
from src.utils.endpoints import INIT_ENDPOINT
from src.utils.endpoints import LOCK_ENDPOINT
from src.utils.endpoints import NETWORK_INFO_ENDPOINT
from src.utils.endpoints import NODE_INFO_ENDPOINT
from src.utils.endpoints import RESTORE_ENDPOINT
from src.utils.endpoints import SEND_ONION_MESSAGE_ENDPOINT
from src.utils.endpoints import SHUTDOWN_ENDPOINT
from src.utils.endpoints import SIGN_MESSAGE_ENDPOINT
from src.utils.endpoints import UNLOCK_ENDPOINT
from src.utils.helpers import get_bitcoin_config
from src.utils.request import Request
from rgb_lib import rgb_lib,BitcoinNetwork


class CommonOperationRepository:
    """Repository for handling common operations."""

    @staticmethod
    # @lock_required
    # @is_node_initialized
    def init(init: InitRequestModel) -> InitResponseModel:
        """Initialize operation."""
        # payload = init.dict()
        network = BitcoinNetwork(int(init.network))        
        with repository_custom_context():
            # response = Request.post(INIT_ENDPOINT, payload)
            response = rgb_lib.generate_keys(network)
            init_response = InitResponseModel(**response.__dict__)
            return init_response

    @staticmethod
    def unlock(unlock: WalletRequestModel) :
        """Unlock operation."""
        with repository_custom_context():
            # response = Request.post(UNLOCK_ENDPOINT, payload)
            # response.raise_for_status()  # Raises an exception for HTTP errors
            payload = unlock.dict()

            # Explicitly map 'bitcoin_network' to the correct enum and 'database_type' to DatabaseType
            payload['bitcoin_network'] = BitcoinNetwork(int(unlock.bitcoin_network))

            # Now we pass the unpacked dictionary to WalletData
            wallet_data = rgb_lib.WalletData(**payload,database_type=rgb_lib.DatabaseType.SQLITE)

            # Initialize the wallet
            recv_wallet = rgb_lib.Wallet(wallet_data)
            network : NetworkEnumModel = SettingRepository.get_wallet_network()
            indexer_url = get_bitcoin_config(network,'').indexer_url
            online_wallet = recv_wallet.go_online(False,indexer_url)
            WalletHolder.set_wallet(recv_wallet)
            WalletHolder.set_online(online_wallet)
            
        return recv_wallet

    @staticmethod
    # @unlock_required
    def node_info() -> NodeInfoResponseModel:
        # """Node info operation."""
        # with repository_custom_context():
        #     response = Request.get(NODE_INFO_ENDPOINT)
        #     response.raise_for_status()  # Raises an exception for HTTP errors
        #     data = response.json()
        #     return NodeInfoResponseModel(**data)
        pass

    @staticmethod
    # @unlock_required
    def network_info() -> NetworkInfoResponseModel:
        """Network info operation."""
        with repository_custom_context():
            response = Request.get(NETWORK_INFO_ENDPOINT)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return NetworkInfoResponseModel(**data)

    @staticmethod
    def lock() -> LockResponseModel:
        """Lock operation."""
        with repository_custom_context():
            response = Request.post(LOCK_ENDPOINT)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return LockResponseModel(status=True)

    @staticmethod
    @lock_required
    def backup(backup: BackupRequestModel) -> BackupResponseModel:
        """Backup operation."""
        payload = backup.dict()
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            wallet.backup(**payload)
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
