"""Module containing CommonOperationRepository."""
from __future__ import annotations

from hwilib.psbt import PSBT
from rgb_lib import AssetSchema
from rgb_lib import BitcoinNetwork
from rgb_lib import DatabaseType
from rgb_lib import Keys
from rgb_lib import rgb_lib
from rgb_lib import MultisigKeys,SinglesigKeys

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
from src.utils.custom_context import repository_custom_context
from src.utils.custom_exception import CommonException
from src.utils.decorators.require_hardware_wallet_connected import require_hardware_wallet_connected
from src.utils.hardware_client_store import hardware_client_store
from src.utils.wallet_credential_encryption import mnemonic_store
from src.utils.build_app_path import app_paths


class CommonOperationRepository:
    """Repository for handling common operations."""

    @staticmethod
    def init(init: InitRequestModel) -> Keys:
        """Initialize and generate RGB keys for the given Bitcoin network."""
        with repository_custom_context():
            response: Keys = rgb_lib.generate_keys(init.network)
            print('Generated Keys:', response)
            return response

    @staticmethod
    def unlock(unlock: WalletRequestModel) -> rgb_lib.Wallet | rgb_lib.MultisigWallet:
        """Unlock operation - creates either standard or multisig wallet."""
        with repository_custom_context():
            wallet_data = rgb_lib.WalletData(
                data_dir=unlock.data_dir, bitcoin_network=unlock.bitcoin_network, database_type=DatabaseType.SQLITE,
                max_allocations_per_utxo=unlock.max_allocations_per_utxo, supported_schemas=AssetSchema,
            )

            is_multisig = (
                SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET
            )

            if is_multisig:
                recv_wallet = rgb_lib.MultisigWallet(wallet_data, keys=unlock.keys)
            else:
                # Standard single-sig wallet
                recv_wallet = rgb_lib.Wallet(wallet_data, keys=unlock.keys)
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
    def sign_and_finalize_psbt(unsigned_psbt: str) -> str:
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
        
        # We need to map our BitcoinNetwork enum to rgb_lib.BitcoinNetwork
        # Assuming for now it's REGTEST as hardcoded previously, but better to map it
        # However, previous code hardcoded REGTEST. We should ideally fix this later but keep behavior.
        bitcoin_network = BitcoinNetwork.REGTEST

        keys = rgb_lib.restore_keys(bitcoin_network, mnemonic)
        
        wallet_data = rgb_lib.WalletData(
            data_dir=app_paths.app_path,
            bitcoin_network=bitcoin_network,
            database_type=DatabaseType.SQLITE,
            max_allocations_per_utxo=1,
            supported_schemas=AssetSchema,
        )

        return rgb_lib.Wallet(
            wallet_data, 
            keys=SinglesigKeys(
                account_xpub_vanilla=keys.account_xpub_vanilla,
                account_xpub_colored=keys.account_xpub_colored,
                vanilla_keychain=0,
                master_fingerprint=keys.master_fingerprint,
                mnemonic=mnemonic,
            )
        )

    @staticmethod
    def sign_psbt(unsigned_psbt: str) -> str:
        """
        Sign PSBT without finalizing (for multisig where we need multiple signatures).
        Returns the partially signed PSBT.
        """
        with repository_custom_context():
            key_storage_type = SettingRepository.get_key_storage_type()
            if key_storage_type == KeyStorageType.HARDWARE_WALLET:
                psbt = PSBT()
                psbt.deserialize(unsigned_psbt)
                signed_psbt = hardware_client_store.client.sign_tx(psbt)
                serialized_psbt = signed_psbt.serialize()
            else:
                # Check if this is a multisig wallet - MultisigWallet doesn't have sign_psbt
                # So we need to create a temporary singlesig Wallet for signing
                wallet_sig_type = SettingRepository.get_wallet_signature_type()
                if wallet_sig_type == WalletSignatureType.MULTI_SIG_WALLET:
                    temp_wallet = CommonOperationRepository._get_temp_singlesig_wallet()
                    serialized_psbt = temp_wallet.sign_psbt(unsigned_psbt)
                else:
                    # Regular singlesig wallet - use the existing wallet
                    serialized_psbt = colored_wallet.wallet.sign_psbt(
                        unsigned_psbt,
                    )
            return serialized_psbt
