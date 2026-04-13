# pylint: disable=too-many-instance-attributes
# mypy: ignore-errors
"""This module contains the CFADetailViewModel class, which represents the view model
for the Bitcoin page activities.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from rgb_lib import AssetSchema
from rgb_lib import Assignment

from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.asset_detail_page_services import AssetDetailPageService
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import FailTransferRequestModel
from src.model.rgb_model import FailTransferResponseModel
from src.model.rgb_model import ListTransferAssetWithBalanceResponseModel
from src.model.rgb_model import ListTransfersRequestModel
from src.model.rgb_model import RefreshFailureItem
from src.model.rgb_model import SendAssetRequestModel
from src.model.rgb_model import SendAssetResponseModel
from src.model.rgb_model import SendBeginRequestModel
from src.utils.cache import Cache
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
from src.utils.error_message import ERROR_FAIL_TRANSFER
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.hardware_client_store import hardware_client_store
from src.utils.helpers import requires_native_authentication
from src.utils.info_message import INFO_ASSET_SENT
from src.utils.info_message import INFO_FAIL_TRANSFER_SUCCESSFULLY
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_REFRESH_SUCCESSFULLY
from src.utils.info_message import INFO_TX_BROADCAST
from src.utils.page_navigation_events import PageNavigationEventManager
from src.utils.worker import ThreadManager
from src.viewmodels.viewmodel_helpers import handle_hardware_wallet_signing
from src.viewmodels.viewmodel_helpers import post_signed_psbt_to_bridge
from src.viewmodels.viewmodel_helpers import sign_and_finalize_psbt
from src.viewmodels.viewmodel_helpers import sign_psbt_for_multisig
from src.views.components.toast import ToastManager


class CFAViewModel(QObject, ThreadManager):
    """This class represents the activities of the bitcoin page."""

    asset_info = Signal(str, str, str, Enum)
    txn_list_loaded = Signal(str, str, str, Enum)
    send_cfa_button_clicked = Signal(bool)
    message = Signal(ToastPreset, str)
    is_loading = Signal(bool)
    refresh = Signal(bool)
    stop_loading = Signal(bool)
    hw_dialog_update = Signal(object, Enum)
    unsigned_psbt = Signal(str)

    def __init__(self, page_navigation: Any) -> None:
        super().__init__()
        self._page_navigation = page_navigation
        self.asset_info.connect(self.get_cfa_asset_detail)

        # Initializing default values for attributes
        self.asset_id = None
        self.asset_name = None
        self.image_path = None
        self.asset_type = None
        self.blinded_utxo = None
        self.transport_endpoints = None
        self.fee_rate = None
        self.min_confirmation = None
        self.assignment = None
        self.txn_list = []
        self.current_send_request = None
        self.operation_idx = None

    def get_cfa_asset_detail(self, asset_id: str, asset_name: str, image_path: str, asset_type: Enum) -> None:
        """Retrieve CFA asset list."""

        def on_success(response: ListTransferAssetWithBalanceResponseModel) -> None:
            """Handle success for the CFA asset detail list."""
            self.txn_list = response
            self.txn_list_loaded.emit(
                asset_id, asset_name, image_path, asset_type,
            )
            self.asset_id, self.asset_name, self.image_path, self.asset_type = asset_id, asset_name, image_path, asset_type
            self.is_loading.emit(False)

        def on_error(error: CommonException) -> None:
            """Handle error for the main asset page."""
            self.txn_list_loaded.emit(
                asset_id, asset_name, image_path, asset_type,
            )
            self.is_loading.emit(False)
            ToastManager.error(description=error)

        try:
            self.run_in_thread(
                AssetDetailPageService.get_asset_transactions,
                {
                    'args': [ListTransfersRequestModel(asset_id=asset_id)],
                    'callback': on_success,
                    'error_callback': on_error,
                },
            )
        except Exception as e:
            on_error(CommonException(message=str(e)))

    def on_success_cfa(self, tx_id: SendAssetResponseModel | None = None) -> None:
        """Handle success for sending CFA asset."""
        self.is_loading.emit(False)
        self.send_cfa_button_clicked.emit(False)
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            self.hw_dialog_update.emit(
                None, PsbtStatus.SUCCESS,
            )

        # Check for multisig pending status via wallet type and response
        is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        if is_multisig:
            ToastManager.success(
                description=INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE,
            )
            self.hw_dialog_update.emit(
                None, PsbtStatus.SUCCESS,
            )
        else:
            ToastManager.success(
                description=INFO_ASSET_SENT.format(tx_id.txid),
            )

        if self.asset_type == AssetSchema.CFA:
            self._page_navigation.collectibles_asset_page()
        elif self.asset_type == AssetSchema.NIA:
            self._page_navigation.fungibles_asset_page()
        elif self.asset_type == AssetSchema.IFA:
            self._page_navigation.inflatable_asset_page()

    def on_error(self, error) -> None:
        """Handle error for sending CFA asset."""
        self.is_loading.emit(False)
        self.send_cfa_button_clicked.emit(False)
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET or (
            isinstance(
                error, CommonException,
            ) and error.message == 'NoAvailableUtxos'
        ) or SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            self.hw_dialog_update.emit(
                str(error.message), PsbtStatus.ERROR,
            )
        else:
            ToastManager.error(description=error.message)

    def on_error_native_auth(self, error: Exception) -> None:
        """Callback function on error during native authentication."""
        description = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG
        ToastManager.error(description=description)

    def on_send_click(self, blinded_utxo: str, transport_endpoints: list, fee_rate: int, min_confirmation: int, assignment: Assignment) -> None:
        """Starts a thread to execute the send_cfa function with the provided arguments."""
        self.blinded_utxo = blinded_utxo
        self.transport_endpoints = transport_endpoints
        self.fee_rate = fee_rate
        self.min_confirmation = min_confirmation
        self.assignment = assignment
        self.send_cfa_button_clicked.emit(True)
        self.is_loading.emit(True)

        if requires_native_authentication():
            self.run_in_thread(
                SettingRepository.native_authentication,
                {
                    'args': [NativeAuthType.MAJOR_OPERATION],
                    'callback': self.on_success_send_rgb_asset,
                    'error_callback': self.on_error_native_auth,
                },
            )
        else:
            self._proceed_with_send_asset()

    def _proceed_with_send_asset(self):
        """Proceed with sending asset after native auth or directly for non-auth variants."""
        try:
            self.run_in_thread(
                RgbRepository.send_asset,
                {
                    'args': [
                        SendAssetRequestModel(
                            asset_id=self.asset_id,
                            assignment=self.assignment,
                            recipient_id=self.blinded_utxo,
                            transport_endpoints=self.transport_endpoints,
                            fee_rate=int(self.fee_rate),
                            min_confirmations=int(self.min_confirmation),
                        ),
                    ],
                    'callback': self.on_success_cfa,
                    'error_callback': self.on_error,
                },
            )
        except Exception as e:
            self.on_error(CommonException(message=str(e)))

    def on_success_send_rgb_asset(self, success: bool) -> None:
        """Callback function after native authentication is successful."""
        if success:
            self.send_cfa_button_clicked.emit(True)
            self.is_loading.emit(True)
            self._proceed_with_send_asset()
        else:
            self.send_cfa_button_clicked.emit(False)
            self.is_loading.emit(False)
            ToastManager.error(description=ERROR_AUTHENTICATION_CANCELLED)

    def on_refresh_click(self, asset_id=None) -> None:
        """Executes the refresh operation in a separate thread."""
        cache = Cache.get_cache_session()
        if cache is not None:
            cache.invalidate_cache()
        self.send_cfa_button_clicked.emit(True)
        self.is_loading.emit(True)

        def on_success_refresh(refresh_data=None) -> None:
            """Handle success for refreshing transactions.
            If there are failures for the current asset, show the refresh dialog filtered to this asset only.
            """
            self.is_loading.emit(False)
            self.refresh.emit(True)
            failures_only = {
                k: v for k, v in refresh_data.items(
                ) if v is not None and v.failure is not None
            }

            if failures_only:
                items = [
                    RefreshFailureItem(
                        asset_id=self.asset_id,
                        failure=entry.failure,
                    )
                    for entry in failures_only.values()
                ]
                if items:
                    PageNavigationEventManager.get_instance(
                    ).refresh_transfer_result_dialog_signal.emit(items)
            else:
                ToastManager.success(description=INFO_REFRESH_SUCCESSFULLY)
                self.get_cfa_asset_detail(
                    self.asset_id, self.asset_name, None, self.asset_type,
                )

        def on_error(error: CommonException) -> None:
            """Handle error for refreshing transactions."""
            self.refresh.emit(False)
            self.is_loading.emit(False)
            ToastManager.error(
                description=f'{ERROR_SOMETHING_WENT_WRONG}: {error}',
            )

        try:
            self.run_in_thread(
                RgbRepository.refresh_transfer,
                {
                    'args': [asset_id],
                    'callback': on_success_refresh,
                    'error_callback': on_error,
                },
            )
        except Exception as e:
            on_error(CommonException(message=str(e)))

    def on_fail_transfer(self, batch_transfer_idx: int) -> None:
        """Executes the fail transfer operation in a separate thread."""
        self.is_loading.emit(True)

        def on_success_fail_transfer(response: FailTransferResponseModel) -> None:
            """Handle success for failing a transfer."""
            if response.transfers_changed:
                self.get_cfa_asset_detail(
                    self.asset_id, self.asset_name, None, self.asset_type,
                )
                ToastManager.success(
                    description=INFO_FAIL_TRANSFER_SUCCESSFULLY,
                )
            else:
                self.is_loading.emit(False)
                ToastManager.error(description=ERROR_FAIL_TRANSFER)

        def on_error(error: CommonException) -> None:
            """Handle error for failing a transfer."""
            self.is_loading.emit(False)
            ToastManager.error(
                description=f'{ERROR_SOMETHING_WENT_WRONG}: {error.message}',
            )

        try:
            self.run_in_thread(
                RgbRepository.fail_transfer,
                {
                    'args': [FailTransferRequestModel(batch_transfer_idx=batch_transfer_idx)],
                    'callback': on_success_fail_transfer,
                    'error_callback': on_error,
                },
            )
        except Exception as e:
            on_error(CommonException(message=str(e)))

    def send_begin(self, blinded_utxo: str, transport_endpoints: list, fee_rate: int, min_confirmation: int, assignment: Assignment):
        """
        Begin the process of sending an asset by creating a PSBT.
        Calls RgbRepository.send_begin and expects a PSBT to be signed externally.
        """
        self.send_cfa_button_clicked.emit(True)
        # Store params for later use
        self.blinded_utxo = blinded_utxo
        self.transport_endpoints = transport_endpoints
        self.fee_rate = fee_rate
        self.min_confirmation = min_confirmation
        self.assignment = assignment

        if requires_native_authentication():
            self.run_in_thread(
                SettingRepository.native_authentication,
                {
                    'args': [NativeAuthType.MAJOR_OPERATION],
                    'callback': self._on_success_native_auth_send_begin,
                    'error_callback': self.on_error_native_auth,
                },
            )
        else:
            self._proceed_with_send_begin()

    def _on_success_native_auth_send_begin(self, success: bool):
        """Callback after native auth success for send_begin."""
        if success:
            self._proceed_with_send_begin()
        else:
            self.send_cfa_button_clicked.emit(False)
            ToastManager.error(description=ERROR_AUTHENTICATION_CANCELLED)

    def _proceed_with_send_begin(self):
        """Proceed with PSBT creation after native auth check."""
        request = SendBeginRequestModel(
            asset_id=self.asset_id,
            assignment=self.assignment,
            recipient_id=self.blinded_utxo,
            transport_endpoints=self.transport_endpoints,
            fee_rate=self.fee_rate,
            min_confirmations=self.min_confirmation,
        )
        # Store request for multisig post_send step
        self.current_send_request = request
        if SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            self.run_in_thread(
                RgbRepository.send_init,
                {
                    'args': [request],
                    'callback': self.on_psbt_created,
                    'error_callback': self.on_error,
                },
            )
        else:
            self.run_in_thread(
                RgbRepository.send_begin,
                {
                    'args': [request],
                    'callback': self.on_psbt_created,
                    'error_callback': self.on_error,
                },
            )

    def on_psbt_created(self, result):
        """
        Handle the PSBT created by send_begin or send_init.
        Run signing and finalization in a background thread.
        """
        if SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            unsigned_psbt = result.psbt
            self.operation_idx = result.operation_idx
        else:
            unsigned_psbt = result.psbt
            self.operation_idx = None
        if SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY:
            self.unsigned_psbt.emit(unsigned_psbt)
            return

        is_hw = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET
        is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        is_on_device = SettingRepository.get_key_storage_type() == KeyStorageType.ON_DEVICE

        handle_hardware_wallet_signing(
            self, is_hw, is_online, is_multisig, is_on_device, self.send_cfa_button_clicked,
        )

        if is_multisig:
            sign_psbt_for_multisig(self, unsigned_psbt, self.operation_idx)
        else:
            sign_and_finalize_psbt(self, unsigned_psbt)

    def on_multisig_psbt_signed(self, signed_psbt: str):
        """Post signed PSBT and recipient map to bridge."""
        post_signed_psbt_to_bridge(self, signed_psbt, self.operation_idx)

    def on_success_multisig_post(self, _):
        """Handle success after posting to bridge."""
        # Auto-sync is handled by RgbRepository decorator on post_send
        self.on_success_cfa()

    def on_psbt_signed_and_finalized_success(self, finalized_psbt: str):
        """
        Callback after PSBT is signed and finalized.
        Now broadcast the transaction.
        """
        self.hw_dialog_update.emit(
            INFO_TX_BROADCAST, PsbtStatus.BROADCASTING,
        )
        self.send_end(finalized_psbt)

    def send_end(self, signed_psbt: str, skip_sync: bool = False):
        """
        Finalize and broadcast the signed PSBT.
        Calls RgbRepository.send_end to broadcast the transaction.
        """
        self.send_cfa_button_clicked.emit(True)
        request = BroadcastPsbtRequestModel(
            signed_psbt=signed_psbt, skip_sync=skip_sync,
        )
        self.run_in_thread(
            RgbRepository.send_end,
            {
                'args': [request],
                'callback': self.on_success_cfa,
                'error_callback': self.on_error,
            },
        )

    def cancel_operation(self):
        """
        Called when the user clicks Cancel on the hardware wallet dialog.
        Sets a cancel flag and emits send_cfa_button_clicked(False) to close the dialog.
        """
        self.send_cfa_button_clicked.emit(False)
        hardware_client_store.stop_client()
