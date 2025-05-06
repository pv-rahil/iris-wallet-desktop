"""This module contains the SettingViewModel class, which represents the view model
for the term and conditions page activities.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from rgb_lib import RgbLibError
from rgb_lib import TransportEndpoint
from rgb_lib import TransportType

from src.data.repository.setting_card_repository import SettingCardRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.repository.wallet_holder import colored_wallet
from src.data.service.common_operation_service import CommonOperationService
from src.model.enums.enums_model import NativeAuthType
from src.model.setting_model import DefaultExpiryTime
from src.model.setting_model import DefaultFeeRate
from src.model.setting_model import DefaultIndexerUrl
from src.model.setting_model import DefaultMinConfirmation
from src.model.setting_model import DefaultProxyEndpoint
from src.model.setting_model import IsDefaultEndpointSet
from src.model.setting_model import IsDefaultExpiryTimeSet
from src.model.setting_model import IsDefaultFeeRateSet
from src.model.setting_model import IsDefaultMinConfirmationSet
from src.model.setting_model import IsHideExhaustedAssetEnabled
from src.model.setting_model import IsNativeLoginIntoAppEnabled
from src.model.setting_model import IsShowHiddenAssetEnabled
from src.model.setting_model import NativeAuthenticationStatus
from src.model.setting_model import SettingPageLoadModel
from src.utils.cache import Cache
from src.utils.constant import FEE_RATE
from src.utils.constant import LN_INVOICE_EXPIRY_TIME
from src.utils.constant import LN_INVOICE_EXPIRY_TIME_UNIT
from src.utils.constant import MIN_CONFIRMATION
from src.utils.constant import SAVED_INDEXER_URL
from src.utils.constant import SAVED_PROXY_ENDPOINT
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_KEYRING
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.error_message import ERROR_UNABLE_TO_SET_EXPIRY_TIME
from src.utils.error_message import ERROR_UNABLE_TO_SET_FEE
from src.utils.error_message import ERROR_UNABLE_TO_SET_MIN_CONFIRMATION
from src.utils.info_message import INFO_SET_EXPIRY_TIME_SUCCESSFULLY
from src.utils.info_message import INFO_SET_FEE_RATE_SUCCESSFULLY
from src.utils.info_message import INFO_SET_MIN_CONFIRMATION_SUCCESSFULLY
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class SettingViewModel(QObject, ThreadManager):
    """This class represents the activities of the term and conditions page."""
    native_auth_enable_event = Signal(bool)
    native_auth_logging_event = Signal(bool)
    hide_asset_event = Signal(bool)
    exhausted_asset_event = Signal(bool)
    fee_rate_set_event = Signal(str)
    expiry_time_set_event = Signal(str, str)
    indexer_url_set_event = Signal(str)
    proxy_endpoint_set_event = Signal(str)
    bitcoind_rpc_host_set_event = Signal(str)
    bitcoind_rpc_port_set_event = Signal(int)
    announce_address_set_event = Signal(list[str])
    announce_alias_set_event = Signal(str)
    min_confirmation_set_event = Signal(int)
    on_page_load_event = Signal(SettingPageLoadModel)
    on_error_validation_keyring_event = Signal()
    on_success_validation_keyring_event = Signal()
    loading_status = Signal(bool)
    is_loading = Signal(bool)

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation
        self.login_toggle: bool = False
        self.auth_toggle: bool = False
        self.indexer_url = None
        self.password = None
        self.key = None
        self.value = None

    def on_success_native_login(self, success: bool):
        """Callback function after native authentication successful"""
        if success:
            is_set: bool = SettingRepository.enable_logging_native_authentication(
                self.login_toggle,
            )
            if is_set is False:
                self.native_auth_logging_event.emit(not self.login_toggle)
                ToastManager.info(
                    description=ERROR_KEYRING,
                )
            else:
                self.native_auth_logging_event.emit(self.login_toggle)
        else:
            self.native_auth_logging_event.emit(not self.login_toggle)
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def on_success_native_auth(self, success: bool):
        """Callback function after native authentication successful"""
        if success:
            is_set: bool = SettingRepository.set_native_authentication_status(
                self.auth_toggle,
            )
            if is_set is False:
                self.native_auth_enable_event.emit(not self.auth_toggle)
                ToastManager.info(
                    description=ERROR_KEYRING,
                )
            else:
                self.native_auth_enable_event.emit(self.auth_toggle)
        else:
            self.native_auth_enable_event.emit(not self.auth_toggle)
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def on_error_native_login(self, error: Exception):
        """Callback function on error"""
        description = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG
        ToastManager.error(description=description)
        self.native_auth_logging_event.emit(not self.login_toggle)

    def on_error_native_auth(self, error: Exception):
        """Callback function on error"""
        description = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG
        ToastManager.error(description=description)
        self.native_auth_enable_event.emit(not self.auth_toggle)

    def enable_native_logging(self, is_checked: bool):
        """This method is used for accepting the terms and conditions."""
        self.login_toggle = is_checked
        self.run_in_thread(
            SettingRepository.native_authentication,
            {
                'args': [NativeAuthType.LOGGING_TO_APP],
                'callback': self.on_success_native_login,
                'error_callback': self.on_error_native_login,
            },
        )

    def enable_native_authentication(self, is_checked: bool):
        """This method is used for decline the terms and conditions."""
        self.auth_toggle = is_checked
        self.run_in_thread(
            SettingRepository.native_authentication,
            {
                'args': [NativeAuthType.MAJOR_OPERATION],
                'callback': self.on_success_native_auth,
                'error_callback': self.on_error_native_auth,
            },
        )

    def enable_exhausted_asset(self, is_checked: bool):
        """This method is used for decline the terms and conditions."""
        try:
            success: IsHideExhaustedAssetEnabled = SettingRepository.enable_exhausted_asset(
                is_checked,
            )
            if success.is_enabled:
                self.exhausted_asset_event.emit(is_checked)
            else:
                self.exhausted_asset_event.emit(not is_checked)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
        except CommonException as error:
            self.exhausted_asset_event.emit(not is_checked)
            ToastManager.error(
                description=error.message,
            )
        except Exception:
            self.exhausted_asset_event.emit(not is_checked)
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def enable_hide_asset(self, is_checked: bool):
        """This method is used for decline the terms and conditions."""
        try:
            success: IsShowHiddenAssetEnabled = SettingRepository.enable_show_hidden_asset(
                is_checked,
            )
            if success.is_enabled:
                self.hide_asset_event.emit(is_checked)
            else:
                self.hide_asset_event.emit(not is_checked)
        except CommonException as exc:
            self.hide_asset_event.emit(not is_checked)
            ToastManager.error(
                description=exc.message,
            )
        except Exception:
            self.hide_asset_event.emit(not is_checked)
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def set_default_fee_rate(self, value: str):
        """Sets the default fee rate."""
        try:
            success: IsDefaultFeeRateSet = SettingCardRepository.set_default_fee_rate(
                value,
            )
            if success.is_enabled:
                ToastManager.success(
                    description=INFO_SET_FEE_RATE_SUCCESSFULLY,
                )
                self.fee_rate_set_event.emit(value)
                self.on_page_load()
            else:
                self.fee_rate_set_event.emit(str(FEE_RATE))
                ToastManager.error(
                    description=ERROR_UNABLE_TO_SET_FEE,
                )
        except CommonException as error:
            self.fee_rate_set_event.emit(str(FEE_RATE))
            ToastManager.error(
                description=error.message,
            )
        except Exception:
            self.fee_rate_set_event.emit(str(FEE_RATE))
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def set_default_expiry_time(self, time: int, unit: str):
        """
        Sets the default expiry time and unit for invoices.
        """
        try:
            success: IsDefaultExpiryTimeSet = SettingCardRepository.set_default_expiry_time(
                time, unit,
            )
            if success.is_enabled:
                ToastManager.success(
                    description=INFO_SET_EXPIRY_TIME_SUCCESSFULLY,
                )
                self.expiry_time_set_event.emit(time, unit)
                self.on_page_load()
            else:
                self.expiry_time_set_event.emit(
                    str(LN_INVOICE_EXPIRY_TIME), str(
                        LN_INVOICE_EXPIRY_TIME_UNIT,
                    ),
                )
                ToastManager.error(
                    description=ERROR_UNABLE_TO_SET_EXPIRY_TIME,
                )
        except CommonException as error:
            self.expiry_time_set_event.emit(
                str(LN_INVOICE_EXPIRY_TIME), str(LN_INVOICE_EXPIRY_TIME_UNIT),
            )
            ToastManager.error(
                description=error.message,
            )
        except Exception:
            self.expiry_time_set_event.emit(
                str(LN_INVOICE_EXPIRY_TIME), str(LN_INVOICE_EXPIRY_TIME_UNIT),
            )
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def on_page_load(self):
        'This method call on setting page load'
        try:
            status_of_native_auth_res: NativeAuthenticationStatus = (
                SettingRepository.get_native_authentication_status()
            )
            status_of_native_logging_auth_res: IsNativeLoginIntoAppEnabled = (
                SettingRepository.native_login_enabled()
            )
            status_of_hide_asset_res: IsShowHiddenAssetEnabled = (
                SettingRepository.is_show_hidden_assets_enabled()
            )
            status_of_exhausted_asset_res: IsHideExhaustedAssetEnabled = (
                SettingRepository.is_exhausted_asset_enabled()
            )
            value_of_default_fee_res: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
            value_of_default_expiry_time_res: DefaultExpiryTime = SettingCardRepository.get_default_expiry_time()
            value_of_default_indexer_url_res: DefaultIndexerUrl = SettingCardRepository.get_default_indexer_url()
            value_of_default_proxy_endpoint_res: DefaultProxyEndpoint = SettingCardRepository.get_default_proxy_endpoint()
            value_of_default_min_confirmation_res: DefaultMinConfirmation = SettingCardRepository.get_default_min_confirmation()
            self.on_page_load_event.emit(
                SettingPageLoadModel(
                    status_of_native_auth=status_of_native_auth_res,
                    status_of_native_logging_auth=status_of_native_logging_auth_res,
                    status_of_hide_asset=status_of_hide_asset_res,
                    status_of_exhausted_asset=status_of_exhausted_asset_res,
                    value_of_default_fee=value_of_default_fee_res,
                    value_of_default_expiry_time=value_of_default_expiry_time_res,
                    value_of_default_indexer_url=value_of_default_indexer_url_res,
                    value_of_default_proxy_endpoint=value_of_default_proxy_endpoint_res,
                    value_of_default_min_confirmation=value_of_default_min_confirmation_res,
                ),
            )
        except CommonException as exc:
            ToastManager.error(
                description=exc.message,
            )
            self._page_navigation.fungibles_asset_page()
        except Exception:
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )
            self._page_navigation.fungibles_asset_page()

    def on_success_of_keyring_validation(self):
        """This is a callback call on successfully unlock of node"""
        self.loading_status.emit(False)
        self.on_success_validation_keyring_event.emit()

    def on_error_of_keyring_enable_validation(self, error: Exception):
        """Callback function on error"""
        self.on_error_validation_keyring_event.emit()
        self.loading_status.emit(False)
        if isinstance(error, CommonException):
            ToastManager.error(
                description=error.message,
            )
        else:
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def enable_keyring(self, password: str):
        """Enable keyring status"""
        self.loading_status.emit(True)
        self.run_in_thread(
            CommonOperationService.keyring_toggle_enable_validation,
            {
                'args': [password],
                'callback': self.on_success_of_keyring_validation,
                'error_callback': self.on_error_of_keyring_enable_validation,
            },
        )

    def check_indexer_url_endpoint(self, indexer_url: str):
        """
        Validates and sets the indexer URL in a background thread.
        Args:
            indexer_url (str): The new indexer URL to validate and set.
        """
        try:
            self.is_loading.emit(True)  # Show loading indicator
            indexer_url = indexer_url.strip()

            # Call the go_online_again method to try setting the new indexer URL
            colored_wallet.go_online_again(indexer_url=indexer_url)
            success: IsDefaultEndpointSet = SettingCardRepository.set_default_endpoints(
                SAVED_INDEXER_URL,
                indexer_url,
            )
            if success.is_enabled:
                self.indexer_url_set_event.emit(indexer_url)

            self.is_loading.emit(False)
            ToastManager.success(
                description='electrum url set successfully',
            )

        except RgbLibError as e:
            self.is_loading.emit(False)
            ToastManager.error(
                description=str(e),
            )

    def check_proxy_endpoint(self, proxy_endpoint: str):
        """
        Validates and sets the proxy endpoint in a background thread.
        Args:
            proxy_endpoint (str): The new proxy endpoint to validate and set.
        """

        self.is_loading.emit(True)
        proxy_endpoint = proxy_endpoint.strip()
        try:
            consignment_endpoint = TransportEndpoint(proxy_endpoint)

            if consignment_endpoint.transport_type() != TransportType.JSON_RPC:
                raise ValueError('Transport type is not JSON_RPC')

            success: IsDefaultEndpointSet = SettingCardRepository.set_default_endpoints(
                SAVED_PROXY_ENDPOINT,
                proxy_endpoint,
            )
            if success.is_enabled:
                self.proxy_endpoint_set_event.emit(proxy_endpoint)
            ToastManager.success(
                description='proxy endpoint set successfully',
            )
            self.is_loading.emit(False)
        except (RgbLibError, ValueError) as e:
            self.is_loading.emit(False)
            print(e)
            ToastManager.error(
                description=str(e),
            )

    def set_min_confirmation(self, min_confirmation: int):
        """Sets the default min confirmation."""
        try:
            success: IsDefaultMinConfirmationSet = SettingCardRepository.set_default_min_confirmation(
                min_confirmation,
            )
            if success.is_enabled:
                ToastManager.success(
                    description=INFO_SET_MIN_CONFIRMATION_SUCCESSFULLY,
                )
                self.min_confirmation_set_event.emit(min_confirmation)
                self.on_page_load()
            else:
                self.min_confirmation_set_event.emit(MIN_CONFIRMATION)
                ToastManager.error(
                    description=ERROR_UNABLE_TO_SET_MIN_CONFIRMATION,
                )
        except CommonException as error:
            self.min_confirmation_set_event.emit(MIN_CONFIRMATION)
            ToastManager.error(
                description=error.message,
            )
        except Exception:
            self.min_confirmation_set_event.emit(MIN_CONFIRMATION)
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )
