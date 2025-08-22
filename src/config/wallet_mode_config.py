# pylint: disable=too-few-public-methods,too-many-return-statements
"""
Configuration and privilege definitions for wallet modes and their capabilities.
"""
from __future__ import annotations

from src.model.common_operation_model import WalletModeConfig
from src.model.common_operation_model import WalletModePrivilege
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletSecurityType
from src.model.enums.enums_model import WalletType


class WalletModeConfiguration:
    """
    A utility class for retrieving wallet mode configurations based on various parameters.
    """
    @staticmethod
    def get_mode_config(
        wallet_type: WalletType | None,
        security_type: WalletSecurityType | None,
        entry_type: WalletEntryType | None,
        storage_type: KeyStorageType | None,
    ) -> WalletModeConfig:
        """
        Get configuration for the selected wallet mode combination.
        Returns a WalletModeConfig object describing the mode.
        """

        # Online Watch Only
        if (
            wallet_type == WalletType.ONLINE_TYPE_WALLET and
            security_type == WalletSecurityType.WATCH_ONLY
        ):
            return WalletModeConfig(
                mode_name='Online Watch-Only Wallet',
                description='A secure wallet for monitoring transactions and balances without private key access',
                privileges=WalletModePrivilege(
                    can_send_transactions=False,
                    can_receive_transactions=False,
                    can_create_assets=False,
                    can_backup_wallet=True,
                    can_export_psbt=True,
                    can_receive_asset=False,
                    can_use_faucet=False,
                ),
                capabilities=[
                    {'emoji': '👁️', 'text': 'View balances & transaction history'},
                    {'emoji': '📥', 'text': 'Import signed PSBTs'},
                    {'emoji': '📤', 'text': 'Broadcast signed PSBTs'},
                ],
                limitations=[
                    {'emoji': '🚫', 'text': 'Cannot create or sign transactions'},
                    {'emoji': '🔒', 'text': 'No private key access'},
                    {'emoji': '⛔', 'text': 'Cannot create or manage assets'},
                ],
                recommended_for=[
                    {'emoji': '👀', 'text': 'Transaction tracking'},
                    {'emoji': '🔍', 'text': 'Balance monitoring'},
                ],
            )

        # Online Create New with Private Key (On Device)
        if (
            wallet_type == WalletType.ONLINE_TYPE_WALLET and
            security_type == WalletSecurityType.WITH_PRIVATE_KEY and
            storage_type == KeyStorageType.ON_DEVICE and
            entry_type == WalletEntryType.CREATE
        ):
            return WalletModeConfig(
                mode_name='Online Wallet - Create New (On Device)',
                description='Create a new wallet with private key stored on your device',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=True,
                    can_export_psbt=False,
                    can_receive_asset=True,
                    can_use_faucet=True,
                ),
                capabilities=[
                    {'emoji': '🆕', 'text': 'Generate new wallet & keys'},
                    {'emoji': '🔐', 'text': 'Secure key storage on device'},
                    {'emoji': '💸', 'text': 'Send and receive transactions'},
                    {'emoji': '🧠', 'text': 'Full asset management'},
                ],
                limitations=[
                    {'emoji': '🔑', 'text': 'Keep your recovery phrase safe'},
                    {'emoji': '🧩', 'text': 'Must choose a strong and safe password'},
                ],
                recommended_for=[
                    {'emoji': '🆕', 'text': 'Everyday spending and receiving'},
                    {'emoji': '📱', 'text': 'Personal wallets on trusted devices'},
                ],
            )

        # Online Create New with Hardware Wallet
        if (
            wallet_type == WalletType.ONLINE_TYPE_WALLET and
            security_type == WalletSecurityType.WITH_PRIVATE_KEY and
            storage_type == KeyStorageType.HARDWARE_WALLET and
            entry_type == WalletEntryType.CREATE
        ):
            return WalletModeConfig(
                mode_name='Online Wallet - Create New (Hardware)',
                description='Set up a new wallet with a hardware security device',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=True,
                    can_export_psbt=False,
                    can_receive_asset=True,
                    can_use_faucet=True,
                ),
                capabilities=[
                    {'emoji': '🆕', 'text': 'Initialize new wallet with hardware device'},
                    {'emoji': '🛡️', 'text': 'Maximum security setup'},
                    {'emoji': '💸', 'text': 'Hardware-signed transactions'},
                    {'emoji': '🧠', 'text': 'Asset management'},
                ],
                limitations=[
                    {'emoji': '🔌', 'text': 'Hardware device required'},
                    {'emoji': '⚡', 'text': 'Connection needed for signing'},
                ],
                recommended_for=[
                    {'emoji': '🔒', 'text': 'High-value or long-term holdings'},
                    {'emoji': '🛡️', 'text': 'Security-focused users'},
                ],
            )

        # Online Load Existing with Private Key (On Device)
        if (
            wallet_type == WalletType.ONLINE_TYPE_WALLET and
            security_type == WalletSecurityType.WITH_PRIVATE_KEY and
            storage_type == KeyStorageType.ON_DEVICE and
            entry_type == WalletEntryType.LOAD

        ):
            return WalletModeConfig(
                mode_name='Online Wallet - Load Existing (On Device)',
                description='Import an existing wallet to store on your device',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=True,
                    can_export_psbt=False,
                    can_receive_asset=True,
                    can_use_faucet=True,
                ),
                capabilities=[
                    {'emoji': '📥', 'text': 'Import existing wallet'},
                    {'emoji': '💸', 'text': 'Send and receive transactions'},
                    {'emoji': '🔄', 'text': 'View transaction history'},
                    {'emoji': '🧠', 'text': 'Manage assets'},
                    {'emoji': '🔐', 'text': 'Secure key storage on device'},
                ],
                limitations=[
                    {'emoji': '📝', 'text': 'Requires recovery phrase/key'},
                    {'emoji': '🧩', 'text': 'Must choose a strong and safe password'},
                ],
                recommended_for=[
                    {'emoji': '🔄', 'text': 'Migrating wallets to a new device'},
                    {'emoji': '💼', 'text': 'Active traders and regular users'},
                ],
            )

        # Online Load Existing with Hardware Wallet
        if (
            wallet_type == WalletType.ONLINE_TYPE_WALLET and
            security_type == WalletSecurityType.WITH_PRIVATE_KEY and
            storage_type == KeyStorageType.HARDWARE_WALLET and
            entry_type == WalletEntryType.LOAD

        ):
            return WalletModeConfig(
                mode_name='Online Wallet - Load Existing (Hardware)',
                description='Connect your existing hardware wallet for secure access',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=True,
                    can_export_psbt=False,
                    can_receive_asset=True,
                    can_use_faucet=True,
                ),
                capabilities=[
                    {'emoji': '🔌', 'text': 'Connect hardware wallet'},
                    {'emoji': '🛡️', 'text': 'Hardware security'},
                    {'emoji': '💸', 'text': 'Secure transactions'},
                    {'emoji': '🧠', 'text': 'Asset management'},
                ],
                limitations=[
                    {'emoji': '🔌', 'text': 'Hardware device required'},
                    {'emoji': '⚡', 'text': 'Connection needed for signing'},
                    {'emoji': '📝', 'text': 'Requires xpub key'},
                ],
                recommended_for=[
                    {'emoji': '🔌', 'text': 'Accessing funds with hardware wallet'},
                    {'emoji': '🏦', 'text': 'Institutional or business accounts'},
                ],
            )

        # Offline Create New (On Device)
        if (
            wallet_type == WalletType.OFFLINE_TYPE_WALLET and
            storage_type == KeyStorageType.ON_DEVICE and
            entry_type == WalletEntryType.CREATE
        ):
            return WalletModeConfig(
                mode_name='Offline Wallet - Create New (On Device)',
                description='Create a new air-gapped cold storage wallet',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=False,
                    can_export_psbt=False,
                    can_receive_asset=True,
                    can_use_faucet=False,
                ),
                capabilities=[
                    {'emoji': '🆕', 'text': 'Generate offline wallet'},
                    {'emoji': '✍️', 'text': 'PSBT signing'},
                    {'emoji': '💾', 'text': 'Secure key generation'},
                    {'emoji': '📤', 'text': 'Export signed PSBTs'},
                ],
                limitations=[
                    {'emoji': '🌐', 'text': 'No online functionality'},
                    {'emoji': '🚫', 'text': 'Cannot broadcast the transaction'},
                    {'emoji': '🧩', 'text': 'Must choose a strong and safe password'},
                ],
                recommended_for=[
                    {'emoji': '❄️', 'text': 'Cold storage for long-term savings'},
                    {'emoji': '📝', 'text': 'Manual signing and air-gapped security'},
                ],
            )

        # Offline Create New (Hardware Wallet)
        if (
            wallet_type == WalletType.OFFLINE_TYPE_WALLET and
            storage_type == KeyStorageType.HARDWARE_WALLET and
            entry_type == WalletEntryType.CREATE
        ):
            return WalletModeConfig(
                mode_name='Offline Wallet - Create New (Hardware)',
                description='Create a new offline wallet with hardware security',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=False,
                    can_export_psbt=False,
                    can_receive_asset=True,
                    can_use_faucet=False,
                ),
                capabilities=[
                    {'emoji': '🆕', 'text': 'New wallet setup using hardware device'},
                    {
                        'emoji': '🛡️',
                        'text': 'Dual security (offline + hardware)',
                    },
                    {'emoji': '✍️', 'text': 'Hardware PSBT signing'},
                    {'emoji': '📤', 'text': 'Export signed PSBTs'},
                ],
                limitations=[
                    {'emoji': '🌐', 'text': 'No online features'},
                    {'emoji': '🔌', 'text': 'Hardware device required'},
                    {'emoji': '🚫', 'text': 'Cannot broadcast the transaction'},
                ],
                recommended_for=[
                    {'emoji': '🏦', 'text': 'Institutional vaults and treasuries'},
                    {'emoji': '💎', 'text': 'Ultra-secure, high-value storage'},
                ],
            )

        # Offline Load Existing (On Device)
        if (
            wallet_type == WalletType.OFFLINE_TYPE_WALLET and
            storage_type == KeyStorageType.ON_DEVICE and
            entry_type == WalletEntryType.LOAD

        ):
            return WalletModeConfig(
                mode_name='Offline Wallet - Load Existing (On Device)',
                description='Import an existing wallet for offline cold storage',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=False,
                    can_export_psbt=False,
                    can_receive_asset=True,
                    can_use_faucet=False,
                ),
                capabilities=[
                    {'emoji': '📥', 'text': 'Import existing wallet offline'},
                    {
                        'emoji': '🛡️',
                        'text': 'Dual security (offline + hardware)',
                    },
                    {'emoji': '✍️', 'text': 'Local PSBT signing'},
                    {'emoji': '📤', 'text': 'Export signed PSBTs'},
                ],
                limitations=[
                    {'emoji': '🌐', 'text': 'No online features'},
                    {'emoji': '📝', 'text': 'Manual key import required'},
                    {'emoji': '🚫', 'text': 'Cannot broadcast the transaction'},
                    {'emoji': '🧩', 'text': 'Must choose a strong and safe password'},
                ],
                recommended_for=[
                    {'emoji': '🔒', 'text': 'Migrating cold storage wallets'},
                    {'emoji': '🛡️', 'text': 'Offline recovery and signing'},
                ],
            )

        # Offline Load Existing (Hardware Wallet)
        if (
            wallet_type == WalletType.OFFLINE_TYPE_WALLET and
            storage_type == KeyStorageType.HARDWARE_WALLET and
            entry_type == WalletEntryType.LOAD

        ):
            return WalletModeConfig(
                mode_name='Offline Wallet - Load Existing (Hardware)',
                description='Connect existing hardware wallet in offline mode',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_create_assets=True,
                    can_backup_wallet=False,
                    can_export_psbt=False,
                    can_receive_asset=False,
                    can_use_faucet=False,
                ),
                capabilities=[
                    {'emoji': '🔌', 'text': 'Offline hardware connection'},
                    {'emoji': '🛡️', 'text': 'Maximum security mode'},
                    {'emoji': '✍️', 'text': 'Hardware PSBT signing'},
                    {'emoji': '🔐', 'text': 'Secure key access'},
                    {'emoji': '📤', 'text': 'Export signed PSBTs'},
                ],
                limitations=[
                    {'emoji': '🌐', 'text': 'No online features'},
                    {'emoji': '🔌', 'text': 'Hardware device required'},
                    {'emoji': '🚫', 'text': 'Cannot broadcast the transaction'},
                ],
                recommended_for=[
                    {'emoji': '🔌', 'text': 'Offline access with hardware wallet'},
                    {'emoji': '🏦', 'text': 'Institutional cold storage'},
                ],
            )

        # Default case
        return WalletModeConfig(
            mode_name='Unknown Mode',
            description='Invalid wallet mode combination',
            privileges=WalletModePrivilege(
                can_send_transactions=False,
                can_receive_transactions=False,
                can_create_assets=False,
                can_backup_wallet=False,
                can_export_psbt=False,
                can_receive_asset=False,
                can_use_faucet=False,
            ),
            capabilities=[{'emoji': '❓', 'text': 'Invalid configuration'}],
            limitations=[
                {'emoji': '⚠️', 'text': 'Invalid wallet mode combination'},
            ],
            recommended_for=[
                {'emoji': '❓', 'text': 'Invalid configuration'},
                {'emoji': '⚠️', 'text': 'Check wallet settings'},
            ],
        )
