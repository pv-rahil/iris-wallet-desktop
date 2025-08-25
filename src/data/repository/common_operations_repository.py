"""Module containing CommonOperationRepository."""
from __future__ import annotations

from hwilib.psbt import PSBT
from rgb_lib import BitcoinNetwork
from rgb_lib import DatabaseType
from rgb_lib import Keys
from rgb_lib import rgb_lib

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.setting_repository import KeyStorageType
from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import wallet_data_service
from src.model.common_operation_model import BackupRequestModel
from src.model.common_operation_model import BackupResponseModel
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import RestoreRequestModel
from src.model.common_operation_model import RestoreResponseModel
from src.model.common_operation_model import WalletRequestModel
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.require_hardware_wallet_connected import require_hardware_wallet_connected
from src.utils.hardware_client_store import hardware_client_store


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
                max_allocations_per_utxo=unlock.max_allocations_per_utxo, account_xpub_vanilla=unlock.account_xpub_vanilla,
                account_xpub_colored=unlock.account_xpub_colored, mnemonic=unlock.mnemonic,
                master_fingerprint=unlock.master_fingerprint, vanilla_keychain=unlock.vanilla_keychain,
            )
            # Initialize the wallet
            recv_wallet = rgb_lib.Wallet(wallet_data)
            colored_wallet.set_wallet(recv_wallet)
            return recv_wallet

    @staticmethod
    def backup(backup: BackupRequestModel) -> BackupResponseModel:
        """Backup operation."""
        with repository_custom_context():
            colored_wallet.wallet.backup(
                backup_path=backup.backup_path, password=backup.password,
            )
            return BackupResponseModel(status=True)

    @staticmethod
    def restore(restore: RestoreRequestModel) -> RestoreResponseModel:
        """Restore operation."""
        with repository_custom_context():
            rgb_lib.restore_backup(
                backup_path=restore.backup_path,
                password=restore.password, data_dir=restore.data_dir,
            )
            return RestoreResponseModel(status=True)

    @staticmethod
    def restore_keys(bitcoin_network: BitcoinNetwork, mnemonic: str) -> Keys:
        """Restore keys operation."""
        with repository_custom_context():
            restore_keys = rgb_lib.restore_keys(bitcoin_network, mnemonic)
            return restore_keys

    @staticmethod
    @require_hardware_wallet_connected()
    def sign_and_finalize_psbt(unsigned_psbt: str):
        """Sign and finalize psbt"""
        with repository_custom_context():
            psbt = PSBT()
            psbt.deserialize(unsigned_psbt)
            key_storage_type = SettingRepository.get_key_storage_type()
            if key_storage_type == KeyStorageType.HARDWARE_WALLET:
                signed_psbt = hardware_client_store.client.sign_tx(psbt)
                serialized_psbt = signed_psbt.serialize()
            else:
                serialized_psbt = colored_wallet.wallet.sign_psbt(
                    unsigned_psbt,
                )
            finalized_psbt = colored_wallet.wallet.finalize_psbt(
                signed_psbt=serialized_psbt,
            )
            wallet_data_service.mark_psbt_signed(unsigned_psbt, finalized_psbt)
            return finalized_psbt
