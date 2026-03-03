# pylint:disable=too-few-public-methods
# Model classes are used to store data and don't require methods.
"""Module containing common operation models."""
from __future__ import annotations

from pydantic import BaseModel
from rgb_lib import BitcoinNetwork
from rgb_lib import MultisigKeys
from rgb_lib import SinglesigKeys

from src.model.btc_model import OfflineAsset
from src.model.rgb_model import GetAssetResponseModel
from src.utils.constant import MAX_ALLOCATIONS_PER_UTXO


# -------------------- Helper models -----------------------

class StatusModel(BaseModel):
    """Response status model."""

    status: bool

# -------------------- Request models -----------------------


class InitRequestModel(BaseModel):
    """Init request model."""

    password: str
    network: BitcoinNetwork

    class Config:
        """Pydantic configuration class allowing arbitrary types."""
        arbitrary_types_allowed = True


class BackupRequestModel(BaseModel):
    """Backup request model."""

    backup_path: str
    password: str


class ConfigModel(InitRequestModel):
    """Unlock request model."""
    indexer_url: str
    proxy_endpoint: str


class WalletRequestModel(BaseModel):
    """Wallet Request Model"""
    data_dir: str
    bitcoin_network: BitcoinNetwork
    max_allocations_per_utxo: int = MAX_ALLOCATIONS_PER_UTXO
    keys: SinglesigKeys | MultisigKeys

    class Config:
        """Pydantic configuration class allowing arbitrary types."""
        arbitrary_types_allowed = True


class RestoreRequestModel(BackupRequestModel):
    """Restore request model."""
    data_dir: str


# -------------------- Response models -----------------------

class BackupResponseModel(StatusModel):
    """Backup response model."""


class RestoreResponseModel(StatusModel):
    """Restore response model."""
    is_multisig: bool = False


class UnlockResponseModel(StatusModel):
    """Unlock response model."""


class MainPageDataResponseModel(GetAssetResponseModel):
    """To extend the get asset response model for vanilla asset"""
    vanilla: OfflineAsset


# -------------------- Component models -----------------------


class ConfigurableCardModel(BaseModel):
    ' A model representing a configurable card for the settings page.'
    title_label: str
    title_desc: str
    suggestion_label: str | None = None
    suggestion_desc: str | None = None
    placeholder_value: float | str


class AppPathsModel(BaseModel):
    """Model representing filesystem paths used by the application"""
    app_path: str
    iriswallet_temp_folder_path: str
    cache_path: str
    app_logs_path: str
    pickle_file_path: str
    config_file_path: str
    backup_folder_path: str
    restore_folder_path: str
    mnemonic_file_path: str
    wallet_data_folder_path: str
    download_consignment_path: str


class BroadcastPsbtRequestModel(BaseModel):
    """Request model for broadcast"""
    signed_psbt: str
    skip_sync: bool = False


class KeyringDialogModel(BaseModel):
    """Model representing keyring dialog"""
    mnemonic: str | None = None
    password: str | None = None
    xpub_vanilla: str | None = None
    xpub_colored: str | None = None
    master_fingerprint: str | None = None
    parent: object = None
    navigate_to: object = None
    originating_page: str | None = None


class ReceiveAssetModel(BaseModel):
    """
    Model representing the data needed to display and share a PSBT (Partially Signed Bitcoin Transaction).
    """
    page_name: str
    address_info: str
    psbt: str | None = None
    is_signed: bool | None = None
    close_button_navigation: object | None = None


class USBDrive(BaseModel):
    """Represents a USB drive with its properties."""
    name: str
    path: str
    is_empty: bool


class WalletModePrivilege(BaseModel):
    """
    Dataclass for defining the privileges of a wallet mode.
    """
    can_send_transactions: bool
    can_receive_asset: bool
    can_create_assets: bool
    can_backup_wallet: bool
    can_broadcast_psbt: bool
    can_use_faucet: bool
    can_sign_psbt: bool


class WalletModeConfig(BaseModel):
    """
    Dataclass for defining the configuration of a wallet mode.
    """
    mode_name: str
    description: str
    privileges: WalletModePrivilege
    capabilities: list[dict]
    limitations: list[dict]
    recommended_for: list[dict]


class IssueAssetDraftModel(BaseModel):
    """Model representing the data needed to display and share a PSBT (Partially Signed Bitcoin Transaction)."""
    name: str
    ticker: str
    issued_amount: int
    file_path: str | None = None
    inflation_amounts: int | None = None
