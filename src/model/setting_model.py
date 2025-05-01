# pylint: disable = W0107,too-few-public-methods
# Model classes are used to store data and don't require methods.
"""
Module containing models related to settings.
"""
from __future__ import annotations

from pydantic import BaseModel


class Status(BaseModel):
    """
    Base model representing a status with an enabled flag.

    Attributes:
        is_enabled (bool): Indicates if the status is enabled.
    """
    is_enabled: bool


class SetWalletInitialized(BaseModel):
    """
    Response model for setting wallet initialization status.

    Attributes:
        status (bool): Indicates if the wallet is initialized.
    """
    status: bool


class IsWalletInitialized(BaseModel):
    """
    Response model for checking wallet initialization status.

    Attributes:
        is_wallet_initialized (bool): Indicates if the wallet is initialized.
    """
    is_wallet_initialized: bool


class IsBackupConfiguredModel(BaseModel):
    """
    Model representing the backup configuration status.

    Attributes:
        is_backup_configured (bool): Indicates if the backup is configured.
    """
    is_backup_configured: bool


class NativeAuthenticationStatus(Status):
    """
    Model representing the native authentication status.

    Inherits from:
        Status
    """
    pass


class IsDefaultFeeRateSet(Status):
    """
    Model representing the status of the default fee rate being set.

    Inherits from:
        Status
    """
    pass


class DefaultFeeRate(BaseModel):
    """
    Model representing the default fee rate.

    Attributes:
        fee_rate (int): The default fee rate value.
    """
    fee_rate: int


class IsDefaultExpiryTimeSet(Status):
    """
    Model representing the status of the default expiry time being set.

    Inherits from:
        Status
    """
    pass


class DefaultExpiryTime(BaseModel):
    """
    Model representing the default expiry time.

    Attributes:
        time (int): The default expiry time value.
        unit (str): The default expiry time unit value.
    """
    time: int
    unit: str


class IsDefaultMinConfirmationSet(Status):
    """
    Model representing the status of the default min confirmation being set.

    Inherits from:
        Status
    """
    pass


class DefaultMinConfirmation(BaseModel):
    """
    Model representing the default min confirmation.

    Attributes:
        min_confirmation (int): The default min confirmation value.
    """
    min_confirmation: int


class IsNativeLoginIntoAppEnabled(Status):
    """
    Model representing the status of native login into the app being enabled.

    Inherits from:
        Status
    """
    pass


class IsShowHiddenAssetEnabled(Status):
    """
    Model representing the status of showing hidden assets being enabled.

    Inherits from:
        Status
    """
    pass


class IsHideExhaustedAssetEnabled(Status):
    """
    Model representing the status of hiding exhausted assets being enabled.

    Inherits from:
        Status
    """
    pass


class IsDefaultEndpointSet(Status):
    """
    Model representing the status of the default indexer url being set.

    Inherits from:
        Status
    """
    pass


class DefaultIndexerUrl(BaseModel):
    """
    Model representing the default indexer url.

    Attributes:
        url (str): The default indexer url value.
    """
    url: str


class DefaultProxyEndpoint(BaseModel):
    """
    Model representing the default indexer url.

    Attributes:
        url (str): The default indexer url value.
    """
    endpoint: str


class SettingPageLoadModel(BaseModel):
    """This model represent data during page load of setting page."""
    status_of_native_auth: NativeAuthenticationStatus
    status_of_native_logging_auth: IsNativeLoginIntoAppEnabled
    status_of_hide_asset: IsShowHiddenAssetEnabled
    status_of_exhausted_asset: IsHideExhaustedAssetEnabled
    value_of_default_fee: DefaultFeeRate
    value_of_default_expiry_time: DefaultExpiryTime
    value_of_default_indexer_url: DefaultIndexerUrl
    value_of_default_proxy_endpoint: DefaultProxyEndpoint
    value_of_default_min_confirmation: DefaultMinConfirmation
