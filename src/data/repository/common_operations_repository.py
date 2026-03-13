"""Module containing CommonOperationRepository."""
from __future__ import annotations

from rgb_lib import AssetSchema
from rgb_lib import BitcoinNetwork
from rgb_lib import DatabaseType
from rgb_lib import generate_keys
from rgb_lib import Keys
from rgb_lib import MultisigWallet
from rgb_lib import restore_backup
from rgb_lib import restore_keys
from rgb_lib import SinglesigKeys
from rgb_lib import Wallet
from rgb_lib import WalletData

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.setting_repository import KeyStorageType
from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import BackupRequestModel
from src.model.common_operation_model import BackupResponseModel
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import RestoreRequestModel
from src.model.common_operation_model import RestoreResponseModel
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import WalletSignatureType
from src.utils.build_app_path import app_paths
from src.utils.custom_context import repository_custom_context
from src.utils.custom_exception import CommonException
from src.utils.decorators.require_hardware_wallet_connected import require_hardware_wallet_connected
from src.utils.hardware_client_store import hardware_client_store
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.ledger_hw_client import sign_psbt_with_ledger
from src.utils.wallet_credential_encryption import mnemonic_store


class CommonOperationRepository:
    """Repository for handling common operations."""

    @staticmethod
    def init(init: InitRequestModel) -> Keys:
        """Initialize and generate RGB keys for the given Bitcoin network."""
        with repository_custom_context():
            response: Keys = generate_keys(init.network)

            return response

    @staticmethod
    def unlock(unlock: WalletRequestModel) -> Wallet | MultisigWallet:
        """Unlock operation - creates either standard or multisig wallet."""
        with repository_custom_context():
            wallet_data = WalletData(
                data_dir=unlock.data_dir, bitcoin_network=unlock.bitcoin_network, database_type=DatabaseType.SQLITE,
                max_allocations_per_utxo=unlock.max_allocations_per_utxo, supported_schemas=AssetSchema,
            )

            is_multisig = (
                SettingRepository.get_wallet_signature_type(
                ) == WalletSignatureType.MULTI_SIG_WALLET
            )

            if is_multisig:
                recv_wallet = MultisigWallet(
                    wallet_data, keys=unlock.keys,
                )
            else:
                # Standard single-sig wallet
                recv_wallet = Wallet(wallet_data, keys=unlock.keys)
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
            restore_backup(
                backup_path=restore.backup_path,
                password=restore.password, data_dir=restore.data_dir,
            )
            return RestoreResponseModel(status=True)

    @staticmethod
    def restore_keys(bitcoin_network: BitcoinNetwork, mnemonic: str) -> Keys:
        """Restore keys operation."""
        with repository_custom_context():
            restore_key = restore_keys(bitcoin_network, mnemonic)
            return restore_key

    @staticmethod
    @require_hardware_wallet_connected()
    def sign_and_finalize_psbt(unsigned_psbt: str) -> str:
        """Sign and finalize PSBT using hardware wallet or software wallet."""
        with repository_custom_context():
            key_storage_type = SettingRepository.get_key_storage_type()
            if key_storage_type == KeyStorageType.HARDWARE_WALLET:
                # Get descriptor dynamically from the active wallet — no hardcoded values.
                descriptor = colored_wallet.wallet.get_descriptors()
                client = hardware_client_store.client
                serialized_psbt = sign_psbt_with_ledger(
                    unsigned_psbt, client, descriptor,
                )
            else:
                serialized_psbt = colored_wallet.wallet.sign_psbt(
                    unsigned_psbt,
                )
            finalized_psbt = colored_wallet.wallet.finalize_psbt(
                signed_psbt=serialized_psbt,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.mark_psbt_signed(unsigned_psbt, finalized_psbt)
                wallet_service.update_secondary_draft_psbt_id(
                    unsigned_psbt, finalized_psbt,
                )
            return finalized_psbt

    @staticmethod
    def _get_temp_singlesig_wallet():
        """Helper to create a temporary singlesig wallet for signing."""
        mnemonic = mnemonic_store.decrypted_mnemonic
        if not mnemonic:
            raise CommonException('Mnemonic not available for signing')

        network = get_bitcoin_network_from_enum(
            SettingRepository.get_wallet_network(),
        )

        keys = restore_keys(network, mnemonic)

        wallet_data = WalletData(
            data_dir=app_paths.app_path,
            bitcoin_network=network,
            database_type=DatabaseType.SQLITE,
            max_allocations_per_utxo=1,
            supported_schemas=AssetSchema,
        )

        return Wallet(
            wallet_data,
            keys=SinglesigKeys(
                account_xpub_vanilla=keys.account_xpub_vanilla,
                account_xpub_colored=keys.account_xpub_colored,
                vanilla_keychain=0,
                master_fingerprint=keys.master_fingerprint,
                mnemonic=mnemonic,
            ),
        )

    @staticmethod
    @require_hardware_wallet_connected()
    def sign_psbt(unsigned_psbt: str) -> str:
        """
        Sign PSBT without finalizing (for multisig where we need multiple signatures).
        Returns the partially signed PSBT.
        """
        with repository_custom_context():
            key_storage_type = SettingRepository.get_key_storage_type()
            if key_storage_type == KeyStorageType.HARDWARE_WALLET:
                # Get descriptor dynamically from the active wallet — no hardcoded values.
                descriptor = colored_wallet.wallet.get_descriptors()
                client = hardware_client_store.client
                serialized_psbt = sign_psbt_with_ledger(
                    unsigned_psbt, client, descriptor,
                )
            else:
                temp_wallet = CommonOperationRepository._get_temp_singlesig_wallet()
                serialized_psbt = temp_wallet.sign_psbt(unsigned_psbt)

            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.mark_psbt_signed(unsigned_psbt, serialized_psbt)
                wallet_service.update_secondary_draft_psbt_id(
                    unsigned_psbt, serialized_psbt,
                )
            return serialized_psbt
