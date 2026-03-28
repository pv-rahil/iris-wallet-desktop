# pylint: disable=too-many-lines
"""
Multisig setup service - business logic for multisig wallet configuration.
"""
from __future__ import annotations

import os

from rgb_lib import Cosigner
from rgb_lib import CosignerData

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import CosignerDataResult
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import ThresholdValidationResult
from src.model.enums.enums_model import KeyStorageType
from src.utils.build_app_path import app_paths
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import MASTER_XPUB
from src.utils.constant import MNEMONIC_KEY
from src.utils.constant import VANILLA_KEYCHAIN
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.wallet_credential_encryption import mnemonic_store


class MultisigSetupService:
    """Service class for multisig setup business logic."""

    @staticmethod
    def validate_threshold(required: int, total: int) -> ThresholdValidationResult:
        """Validate threshold configuration.

        Args:
            required: Number of required signatures
            total: Total number of signers

        Returns:
            ThresholdValidationResult with validation status
        """
        if total < 2 or total > 15:
            return ThresholdValidationResult(
                is_valid=False,
                required=required,
                total=total,
                error_message='Total signers must be between 2 and 15',
            )
        if required < 2 or required > total:
            return ThresholdValidationResult(
                is_valid=False,
                required=required,
                total=total,
                error_message=f'Required signatures must be between 2 and {
                    total
                }',
            )
        return ThresholdValidationResult(
            is_valid=True,
            required=required,
            total=total,
            error_message=None,
        )

    @staticmethod
    def parse_cosigner_string(cosigner_string: str) -> CosignerDataResult:
        """Parse cosigner string and extract data.

        Args:
            cosigner_string: The cosigner string to parse

        Returns:
            CosignerDataResult with parsed data
        """
        text = cosigner_string.strip()
        if not text:
            return CosignerDataResult(
                master_fingerprint='',
                account_xpub_vanilla='',
                account_xpub_colored='',
                vanilla_keychain=None,
                is_valid=False,
            )
        try:
            data = Cosigner(text).cosigner_data()
            val = data.vanilla_keychain
            return CosignerDataResult(
                master_fingerprint=data.master_fingerprint,
                account_xpub_vanilla=data.account_xpub_vanilla,
                account_xpub_colored=data.account_xpub_colored,
                vanilla_keychain=int(val) if val is not None else 0,
                is_valid=True,
            )
        except Exception:
            return CosignerDataResult(
                master_fingerprint='',
                account_xpub_vanilla='',
                account_xpub_colored='',
                vanilla_keychain=None,
                is_valid=False,
            )

    @staticmethod
    def generate_cosigner_string(
        master_fp: str,
        account_xpub_vanilla: str,
        account_xpub_colored: str,
        keychain: int = 0,
    ) -> str | None:
        """Generate cosigner string from components.

        Args:
            master_fp: Master fingerprint
            account_xpub_vanilla: Vanilla account xpub
            account_xpub_colored: Colored account xpub
            keychain: Vanilla keychain value

        Returns:
            Cosigner string or None if generation fails
        """
        if not master_fp or not account_xpub_vanilla or not account_xpub_colored:
            return None
        try:
            data = CosignerData(
                master_fingerprint=master_fp,
                account_xpub_vanilla=account_xpub_vanilla,
                account_xpub_colored=account_xpub_colored,
                vanilla_keychain=keychain,
            )
            return Cosigner.from_data(data).cosigner_string()
        except Exception as e:
            logger.error('Failed to generate cosigner string: %s', e)
            return None

    @staticmethod
    def truncate_text(text: str, max_length: int = 40) -> str:
        """Truncate text with ellipsis in the middle.

        Args:
            text: Text to truncate
            max_length: Maximum length before truncation

        Returns:
            Truncated text
        """
        if text and len(text) > max_length:
            return text[:25] + '...' + text[-25:]
        return text

    @staticmethod
    def generate_wallet_keys(password: str) -> dict | None:
        """Generate wallet keys for multisig setup.

        Args:
            password: Wallet password for encryption

        Returns:
            Dictionary with key data or None on failure
        """
        try:
            if os.path.exists(app_paths.mnemonic_file_path):
                logger.info(
                    'Keys already exist - skipping generation to preserve mnemonic.',
                )
                return {'exists': True}

            network = get_bitcoin_network_from_enum(
                SettingRepository.get_wallet_network(),
            )
            keys = CommonOperationRepository.init(
                InitRequestModel(password='', network=network),
            )

            local_store.set_value(MASTER_FINGERPRINT, keys.master_fingerprint)
            local_store.set_value(MASTER_XPUB, keys.xpub)
            local_store.set_value(
                ACCOUNT_XPUB_VANILLA,
                keys.account_xpub_vanilla,
            )
            local_store.set_value(
                ACCOUNT_XPUB_COLORED,
                keys.account_xpub_colored,
            )

            encrypted = mnemonic_store.encrypt(password, keys.mnemonic)
            local_store.write_to_file(
                file_name=MNEMONIC_KEY,
                file_path=app_paths.mnemonic_file_path,
                value=encrypted,
            )
            logger.info('Fresh setup - encrypted and saved mnemonic.')
            return {
                'exists': False,
                'master_fingerprint': keys.master_fingerprint,
                'xpub': keys.xpub,
                'account_xpub_vanilla': keys.account_xpub_vanilla,
                'account_xpub_colored': keys.account_xpub_colored,
            }
        except Exception as e:
            logger.error('Error generating wallet keys: %s', e)
            return None

    @staticmethod
    def get_wallet_review_data() -> dict:
        """Get wallet review data from local storage.

        Returns:
            Dictionary with wallet review fields
        """
        master_fp = local_store.get_value(MASTER_FINGERPRINT)
        account_xpub_vanilla = local_store.get_value(ACCOUNT_XPUB_VANILLA)
        account_xpub_colored = local_store.get_value(ACCOUNT_XPUB_COLORED)
        keychain = local_store.get_value(VANILLA_KEYCHAIN)
        derivation_path = "m/48'/0'/0'/2'"

        return {
            'master_fingerprint': master_fp or '',
            'keychain': str(keychain) if keychain is not None else '0',
            'derivation_path': derivation_path,
            'account_xpub_vanilla': account_xpub_vanilla or '',
            'account_xpub_colored': account_xpub_colored or '',
        }

    @staticmethod
    def save_watch_only_data(
        fp: str,
        keychain: str,
        vanilla: str,
        colored: str,
    ) -> bool:
        """Save watch-only wallet data to local storage.

        Args:
            fp: Master fingerprint
            keychain: Vanilla keychain value
            vanilla: Account xpub vanilla
            colored: Account xpub colored

        Returns:
            True if saved successfully
        """
        if not fp or not vanilla or not colored:
            return False
        local_store.set_value(MASTER_FINGERPRINT, fp)
        local_store.set_value(
            VANILLA_KEYCHAIN, int(
                keychain,
            ) if keychain.isdigit() else 0,
        )
        local_store.set_value(ACCOUNT_XPUB_VANILLA, vanilla)
        local_store.set_value(ACCOUNT_XPUB_COLORED, colored)
        return True

    @staticmethod
    def save_cosigners_data(cosigner_rows: list[dict]) -> bool:
        """Validate and save cosigners data.

        Args:
            cosigner_rows: List of cosigner row data

        Returns:
            True if all valid and saved successfully
        """
        cosigners_data = []
        for row in cosigner_rows:
            cosigner_string = row.get('string', '').strip()
            if not cosigner_string:
                return False

            result = MultisigSetupService.parse_cosigner_string(
                cosigner_string,
            )
            if not result.is_valid:
                return False

            cosigners_data.append({
                'index': row.get('index'),
                MASTER_FINGERPRINT: result.master_fingerprint,
                ACCOUNT_XPUB_VANILLA: result.account_xpub_vanilla,
                ACCOUNT_XPUB_COLORED: result.account_xpub_colored,
                VANILLA_KEYCHAIN: result.vanilla_keychain,
            })

        SettingRepository.set_cosigners(cosigners_data)
        return True

    @staticmethod
    def check_duplicate_cosigners(cosigner_rows: list[dict]) -> tuple[bool, int | None]:
        """Check for duplicate cosigners based on vanilla xpub.

        Args:
            cosigner_rows: List of cosigner row data

        Returns:
            Tuple of (has_duplicates, duplicate_index)
        """
        seen = set()
        for row in cosigner_rows:
            xpub = row.get('vanilla_xpub_str')
            if xpub:
                if xpub in seen:
                    return True, row.get('index')
                seen.add(xpub)
        return False, None

    @staticmethod
    def is_hardware_wallet() -> bool:
        """Check if current wallet uses hardware wallet storage."""
        return SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET

    @staticmethod
    def get_card_size_for_signers(total_signers: int) -> tuple[int, int]:
        """Get card size based on number of signers.

        Args:
            total_signers: Total number of signers

        Returns:
            Tuple of (min_size, max_size)
        """
        if total_signers > 2:
            return (770, 640)
        return (770, 520)
