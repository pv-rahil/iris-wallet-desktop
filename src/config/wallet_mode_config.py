from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from typing import List

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletSecurityType
from src.model.enums.enums_model import WalletType


@dataclass
class WalletModePrivilege:
    can_send_transactions: bool
    can_receive_transactions: bool
    can_view_balance: bool
    can_create_assets: bool
    can_manage_assets: bool
    can_use_hardware_wallet: bool
    can_backup_wallet: bool
    can_restore_wallet: bool


@dataclass
class WalletModeConfig:
    mode_name: str
    description: str
    privileges: WalletModePrivilege
    capabilities: list[str]
    limitations: list[str]
    recommended_for: list[str]


class WalletModeConfiguration:
    @staticmethod
    def get_mode_config(
        wallet_type: WalletType,
        security_type: WalletSecurityType = None,
        entry_type: WalletEntryType = None,
        storage_type: KeyStorageType = None,
    ) -> WalletModeConfig:
        """Get configuration for the selected wallet mode combination"""

        # Online Watch Only
        if (
            wallet_type == WalletType.ONLINE_TYPE_WALLET and
            security_type == WalletSecurityType.WATCH_ONLY
        ):
            return WalletModeConfig(
                mode_name='Online Watch-Only Wallet',
                description='A wallet that can view transactions and balances but cannot send transactions',
                privileges=WalletModePrivilege(
                    can_send_transactions=False,
                    can_receive_transactions=True,
                    can_view_balance=True,
                    can_create_assets=False,
                    can_manage_assets=False,
                    can_use_hardware_wallet=False,
                    can_backup_wallet=True,
                    can_restore_wallet=True,
                ),
                capabilities=[
                    '👁️ View balances & history',
                    '📥 Import signed PSBTs',
                    '📤 Broadcast signed PSBTs',
                    '🔄 Restore wallet',
                ],
                limitations=[
                    '🚫 Cannot create or sign transactions',
                    '🔒 No private key access',
                    '🚫 No hardware wallet support',
                ],
                recommended_for=[
                    '👀 Monitoring wallet balances',
                    '📊 Viewing transaction history',
                    '💸 Receiving funds',
                ],
            )

        # Online With Private Key
        elif (
            wallet_type == WalletType.ONLINE_TYPE_WALLET and
            security_type == WalletSecurityType.WITH_PRIVATE_KEY
        ):
            return WalletModeConfig(
                mode_name='Online Full Wallet',
                description='A fully functional wallet with complete control over funds and assets',
                privileges=WalletModePrivilege(
                    can_send_transactions=True,
                    can_receive_transactions=True,
                    can_view_balance=True,
                    can_create_assets=True,
                    can_manage_assets=True,
                    can_use_hardware_wallet=True,
                    can_backup_wallet=True,
                    can_restore_wallet=True,
                ),
                capabilities=[
                    '💸 Send transactions',
                    '📥 Receive transactions',
                    '👁️ View balances & history',
                    '🧠 Create & manage assets',
                    '🔐 Use hardware wallet',
                    '🗄️ Backup wallet',
                    '🔄 Restore wallet',
                ],
                limitations=[

                ],
                recommended_for=[
                    '⚡ Full wallet functionality',
                    '🛠️ Create & manage assets',
                    '🔄 Send & receive',
                ],
            )

        # Offline Wallet
        elif wallet_type == WalletType.OFFLINE_TYPE_WALLET:
            return WalletModeConfig(
                mode_name='Offline Wallet',
                description='A wallet that operates without network connection for enhanced security',
                privileges=WalletModePrivilege(
                    can_send_transactions=False,
                    can_receive_transactions=True,
                    can_view_balance=True,
                    can_create_assets=True,
                    can_manage_assets=True,
                    can_use_hardware_wallet=True,
                    can_backup_wallet=True,
                    can_restore_wallet=True,
                ),
                capabilities=[
                    '🛡️ Cold storage security',
                    '✍️ Sign PSBTs offline',
                    '👁️ View balances & history',
                    '🧠 Create & manage assets offline',
                    '🗄️ Backup wallet',
                    '🔄 Restore wallet',
                ],
                limitations=[
                    '🚫 Cannot send transactions directly',
                    '🚫 Cannot broadcast (offline mode)',
                    '📝 Manual transaction signing required',
                    '🔌 Limited to offline operations',
                ],
                recommended_for=[
                    '❄️ Cold storage',
                    '🔒 Enhanced security',
                    '🛠️ Managing assets offline',
                ],
            )

        # Default case
        return WalletModeConfig(
            mode_name='Unknown Mode',
            description='Invalid wallet mode combination',
            privileges=WalletModePrivilege(
                can_send_transactions=False,
                can_receive_transactions=False,
                can_view_balance=False,
                can_create_assets=False,
                can_manage_assets=False,
                can_use_hardware_wallet=False,
                can_backup_wallet=False,
                can_restore_wallet=False,
            ),
            capabilities=['❓ Invalid configuration'],
            limitations=['❓ Invalid configuration'],
            recommended_for=[],
        )
