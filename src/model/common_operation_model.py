# pylint:disable=too-few-public-methods
# Model classes are used to store data and don't require methods.
"""Module containing common operation models."""
from __future__ import annotations

from pydantic import BaseModel
from rgb_lib import BitcoinNetwork

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
    account_xpub_vanilla: str
    account_xpub_colored: str
    mnemonic: str
    vanilla_keychain: int | None = None

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
