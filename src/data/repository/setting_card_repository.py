""""This module defines a repository class for managing settings card related to wallet initialization.
"""
from __future__ import annotations

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.model.setting_model import DefaultFeeRate
from src.model.setting_model import DefaultIndexerUrl
from src.model.setting_model import DefaultMinConfirmation
from src.model.setting_model import DefaultProxyEndpoint
from src.model.setting_model import IsDefaultEndpointSet
from src.model.setting_model import IsDefaultFeeRateSet
from src.model.setting_model import IsDefaultMinConfirmationSet
from src.utils.constant import FEE_RATE
from src.utils.constant import INDEXER_URL_MAINNET
from src.utils.constant import INDEXER_URL_REGTEST
from src.utils.constant import INDEXER_URL_TESTNET
from src.utils.constant import MIN_CONFIRMATION
from src.utils.constant import PROXY_ENDPOINT_MAINNET
from src.utils.constant import PROXY_ENDPOINT_REGTEST
from src.utils.constant import PROXY_ENDPOINT_TESTNET
from src.utils.constant import SAVED_INDEXER_URL
from src.utils.constant import SAVED_PROXY_ENDPOINT
from src.utils.handle_exception import handle_exceptions
from src.utils.local_store import local_store


class SettingCardRepository:
    """
    Manages wallet settings such as fee rate, expiry time, indexer URL, and proxy endpoint.
    Provides methods to set and get these settings, and to validate indexer URLs and proxy endpoints.
    """
    @staticmethod
    def set_default_fee_rate(rate: str) -> IsDefaultFeeRateSet:
        """
        Sets the default fee rate.

        Args:
            rate (float | int): The fee rate to set.

        Returns:
            IsDefaultFeeRateSet: A model indicating whether the default fee rate is set.
        """
        try:
            local_store.set_value('defaultFeeRate', rate)
            # Verify the setting was applied
            if local_store.get_value('defaultFeeRate', value_type=int):
                return IsDefaultFeeRateSet(is_enabled=True)
            return IsDefaultFeeRateSet(is_enabled=False)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def get_default_fee_rate() -> DefaultFeeRate:
        """
        Gets the default fee rate.

        Returns:
            DefaultFeeRate: A model indicating the default fee rate.
        """
        try:
            fee_rate = local_store.get_value('defaultFeeRate')
            if fee_rate is None:
                fee_rate = FEE_RATE
            return DefaultFeeRate(fee_rate=fee_rate)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def set_default_endpoints(key, value: str | int) -> IsDefaultEndpointSet:
        """
        Sets the default endpoint value.

        Args:
            key (str): The key to store the endpoint value.
            value (str | int): The value to be set for the specified key.

        Returns:
            IsDefaultEndpointSet: A model indicating whether the default endpoint
            value was successfully set.
        """
        try:
            local_store.set_value(key, value)

            # Verify the setting was applied
            stored_value = local_store.get_value(key)
            if stored_value == str(value) or stored_value == int(value):
                return IsDefaultEndpointSet(is_enabled=True)
            return IsDefaultEndpointSet(is_enabled=False)

        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def get_default_indexer_url() -> DefaultIndexerUrl:
        """
        Gets the default indexer url.

        Returns:
            DefaultIndexerUrl: A model indicating the default indexer url.
        """
        try:
            indexer_url = None
            stored_network: NetworkEnumModel = SettingRepository.get_wallet_network()

            if stored_network == NetworkEnumModel.MAINNET:
                indexer_url = INDEXER_URL_MAINNET
            elif stored_network == NetworkEnumModel.TESTNET:
                indexer_url = INDEXER_URL_TESTNET
            elif stored_network == NetworkEnumModel.REGTEST:
                indexer_url = INDEXER_URL_REGTEST
            url = local_store.get_value(SAVED_INDEXER_URL)
            if url is None:
                url = indexer_url
            return DefaultIndexerUrl(url=url)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def get_default_proxy_endpoint() -> DefaultProxyEndpoint:
        """
        Gets the default proxy endpoint.

        Returns:
            DefaultProxyEndpoint: A model indicating the default proxy endpoint value.
        """
        try:
            proxy_endpoint = None
            stored_network: NetworkEnumModel = SettingRepository.get_wallet_network()

            if stored_network == NetworkEnumModel.MAINNET:
                proxy_endpoint = PROXY_ENDPOINT_MAINNET
            elif stored_network == NetworkEnumModel.TESTNET:
                proxy_endpoint = PROXY_ENDPOINT_TESTNET
            elif stored_network == NetworkEnumModel.REGTEST:
                proxy_endpoint = PROXY_ENDPOINT_REGTEST
            endpoint = local_store.get_value(SAVED_PROXY_ENDPOINT)
            if endpoint is None:
                endpoint = proxy_endpoint
            return DefaultProxyEndpoint(endpoint=endpoint)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def set_default_min_confirmation(min_confirmation: int) -> IsDefaultMinConfirmationSet:
        """
        Sets the default min confirmation.

        Args:
            min_confirmation (int): The min confirmation to set.

        Returns:
            IsDefaultMinConfirmationSet: A model indicating whether the default min confirmation is set.
        """
        try:
            local_store.set_value('defaultMinConfirmation', min_confirmation)
            # Verify the setting was applied
            if local_store.get_value('defaultMinConfirmation', value_type=int):
                return IsDefaultMinConfirmationSet(is_enabled=True)
            return IsDefaultMinConfirmationSet(is_enabled=False)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def get_default_min_confirmation() -> DefaultMinConfirmation:
        """
        Gets the default fee rate.

        Returns:
            DefaultFeeRate: A model indicating the default fee rate.
        """
        try:
            min_confirmation = local_store.get_value('defaultMinConfirmation')
            if min_confirmation is None:
                min_confirmation = MIN_CONFIRMATION
            return DefaultMinConfirmation(min_confirmation=min_confirmation)
        except Exception as exe:
            return handle_exceptions(exe)
