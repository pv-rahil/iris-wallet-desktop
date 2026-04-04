"""
This module contains the IssueIFAViewModel class, which represents the view model
for the Issue IFA Asset page activities.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from rgb_lib import OperationResult

from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletSignatureType
from src.model.rgb_model import InflateRequestModel
from src.model.rgb_model import IssueAssetIfaRequestModel
from src.model.rgb_model import IssueAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_AUTHENTICATION
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
from src.utils.error_message import ERROR_FIELD_MISSING
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_ASSET_ISSUED
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_TX_BROADCAST
from src.utils.worker import ThreadManager
from src.viewmodels.viewmodel_helpers import handle_viewmodel_error
from src.viewmodels.viewmodel_helpers import post_signed_psbt_to_bridge
from src.viewmodels.viewmodel_helpers import process_psbt_result
from src.views.components.toast import ToastManager


class IssueIFAViewModel(QObject, ThreadManager):
    """This class represents the activities of the Issue IFA Asset page."""

    is_loading = Signal(bool)
    utxo_creation_started = Signal(bool)
    success_page_message = Signal(str)
    secondary_issuance_success = Signal()
    unsigned_psbt = Signal(str)
    hw_dialog_update = Signal(object, Enum)

    def __init__(self, page_navigation: Any) -> None:
        super().__init__()
        self._page_navigation = page_navigation
        self.asset_id: str | None = None
        self.asset_ticker: str | None = None
        self.asset_name: str | None = None
        self.amount: int | None = None
        self.inflation_amounts: int | None = None
        self.fee_rate: int | None = None
        self.min_confirmation: int | None = None
        self.operation_idx = None

    def on_success_native_auth_ifa(self, success: bool):
        """Callback after native authentication for IFA."""
        try:
            if not success:
                raise CommonException(ERROR_AUTHENTICATION)
            if (
                self.asset_ticker is None
                or self.asset_name is None
                or self.amount is None
                or self.inflation_amounts is None
            ):
                raise CommonException(ERROR_FIELD_MISSING)

            request = IssueAssetIfaRequestModel(
                amounts=[int(self.amount)],
                ticker=self.asset_ticker,
                name=self.asset_name,
                precision=0,
                inflation_amounts=[int(self.inflation_amounts)],
            )

            self.run_in_thread(
                RgbRepository.issue_asset_ifa,
                {
                    'args': [request],
                    'callback': self.on_success,
                    'error_callback': self.on_error,
                },
            )
        except CommonException as exc:
            self.is_loading.emit(False)
            ToastManager.error(description=exc.message)
        except Exception:
            self.is_loading.emit(False)
            ToastManager.error(description=ERROR_SOMETHING_WENT_WRONG)

    def on_error_native_auth_ifa(self, error: Exception):
        """Error callback for native auth."""
        self.is_loading.emit(False)
        description = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG
        ToastManager.error(description=description)

    def issue_ifa_asset(
        self,
        asset_ticker: str,
        asset_name: str,
        amount: int,
        inflation_amounts: int,
    ) -> None:
        """Issue an IFA asset with provided details."""
        self.is_loading.emit(True)
        self.asset_ticker = asset_ticker
        self.asset_name = asset_name
        self.amount = amount
        self.inflation_amounts = inflation_amounts
        self.run_in_thread(
            SettingRepository.native_authentication,
            {
                'args': [NativeAuthType.MAJOR_OPERATION],
                'callback': self.on_success_native_auth_ifa,
                'error_callback': self.on_error_native_auth_ifa,
            },
        )

    def on_success(self, response: IssueAssetResponseModel) -> None:
        """Handle success response of IFA issuance."""
        ToastManager.success(
            description=INFO_ASSET_ISSUED.format(response.asset_id),
        )
        self.success_page_message.emit(response.name)
        self.is_loading.emit(False)

    def on_error(self, error) -> None:
        """Handle error response of IFA issuance."""
        self.is_loading.emit(False)
        if isinstance(error, CommonException):
            if getattr(error, 'message', '') == 'NoAvailableUtxos':
                self.utxo_creation_started.emit(True)
                return
        handle_viewmodel_error(self, error)

    def on_success_native_auth_inflate(self, success: bool) -> None:
        """Callback after native authentication for IFA."""
        if success:
            self.is_loading.emit(True)
            try:
                self.run_in_thread(
                    RgbRepository.inflate,
                    {
                        'args': [
                            InflateRequestModel(
                                asset_id=self.asset_id,
                                inflation_amounts=[self.amount],
                                fee_rate=self.fee_rate,
                                min_confirmations=self.min_confirmation,
                            ),
                        ],
                        'callback': self.on_success_inflate,
                        'error_callback': self.on_error,
                    },
                )
            except Exception as e:
                self.on_error(CommonException(message=str(e)))
        else:
            self.is_loading.emit(False)
            ToastManager.error(description=ERROR_AUTHENTICATION_CANCELLED)

    def secondary_issuance(self, asset_id: str, amount: int, fee_rate: int, min_confirmation: int) -> None:
        """Secondary issuance of IFA asset."""
        self.asset_id = asset_id
        self.amount = amount
        self.fee_rate = fee_rate
        self.min_confirmation = min_confirmation
        self.is_loading.emit(True)
        self.run_in_thread(
            SettingRepository.native_authentication,
            {
                'args': [NativeAuthType.MAJOR_OPERATION],
                'callback': self.on_success_native_auth_inflate,
                'error_callback': self.on_error_native_auth_ifa,
            },
        )

    def on_success_inflate(self, response: OperationResult) -> None:
        """Handle success response of IFA second issuance."""
        ToastManager.success(
            description=INFO_ASSET_ISSUED.format(response.txid),
        )
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            self.hw_dialog_update.emit(
                None,
                PsbtStatus.SUCCESS,
            )
        self.secondary_issuance_success.emit()
        self.is_loading.emit(False)

    def secondary_issuance_begin(self, asset_id: str, amount: int, fee_rate: int, min_confirmation: int) -> None:
        """Secondary issuance of IFA asset."""
        self.asset_id = asset_id
        self.amount = amount
        self.fee_rate = fee_rate
        self.min_confirmation = min_confirmation
        self.is_loading.emit(True)
        request = InflateRequestModel(
            asset_id=asset_id,
            inflation_amounts=[amount],
            fee_rate=fee_rate,
            min_confirmations=min_confirmation,
        )
        if SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            self.run_in_thread(
                RgbRepository.inflate_init,
                {
                    'args': [request],
                    'callback': self.on_success_inflate_begin,
                    'error_callback': self.on_error,
                },
            )
        else:
            self.run_in_thread(
                RgbRepository.inflate_begin,
                {
                    'args': [request],
                    'callback': self.on_success_inflate_begin,
                    'error_callback': self.on_error,
                },
            )

    def on_success_inflate_begin(self, result):
        """Handle success response of IFA second issuance."""
        is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        process_psbt_result(self, result, is_multisig)

    def on_multisig_psbt_signed(self, signed_psbt: str):
        """
        Callback after multisig PSBT is signed (partially).
        Now post to bridge.
        """
        post_signed_psbt_to_bridge(self, signed_psbt, self.operation_idx)

    def on_psbt_signed_and_finalized_success(self, finalized_psbt: str):
        """
        Callback after PSBT is signed and finalized.
        Now broadcast the transaction.
        """
        self.hw_dialog_update.emit(
            INFO_TX_BROADCAST, PsbtStatus.BROADCASTING,
        )
        self.inflate_end(finalized_psbt)

    def on_success_multisig_post(self, _=None):
        """Handle success of multisig post"""
        self.hw_dialog_update.emit(None, PsbtStatus.SUCCESS)
        ToastManager.success(INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE)

        # Sync with bridge again and finish
        self.run_in_thread(
            RgbRepository.sync_with_bridge,
            {
                'callback': lambda _: self.secondary_issuance_success.emit(),
                'error_callback': lambda _: self.secondary_issuance_success.emit(),
            },
        )

    def inflate_end(self, signed_psbt: str):
        """
        Finalize and broadcast the signed PSBT.
        Calls RgbRepository.inflate_end to broadcast the transaction.
        """
        self.run_in_thread(
            RgbRepository.inflate_end,
            {
                'args': [signed_psbt],
                'callback': self.on_success_inflate,
                'error_callback': self.on_error,
            },
        )
