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
from rgb_lib import RespondToOperation

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import InflateRequestModel
from src.model.rgb_model import IssueAssetIfaRequestModel
from src.model.rgb_model import IssueAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_AUTHENTICATION
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
from src.utils.error_message import ERROR_FIELD_MISSING
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.hardware_client_store import hardware_client_store
from src.utils.info_message import INFO_ASSET_ISSUED
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_POST_TO_BRIDGE
from src.utils.info_message import INFO_REGISTER_WALLET_AND_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_TX_BROADCAST
from src.utils.worker import ThreadManager
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
        if SettingRepository.get_key_storage_type() != KeyStorageType.HARDWARE_WALLET and \
                SettingRepository.get_wallet_signature_type() != WalletSignatureType.MULTI_SIG_WALLET:
            description = error.message if isinstance(
                error, CommonException,
            ) else ERROR_SOMETHING_WENT_WRONG
            ToastManager.error(description=description)
        else:
            self.hw_dialog_update.emit(
                str(error), PsbtStatus.ERROR,
            )

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
        if SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            unsigned_psbt = result.psbt
            self.operation_idx = result.operation_idx
        else:
            unsigned_psbt = result
            self.operation_idx = None
        if SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY:
            self.unsigned_psbt.emit(unsigned_psbt)
            return

        is_hw = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET

        if is_hw and is_online and SettingRepository.get_wallet_signature_type() == WalletSignatureType.STANDARD_TYPE_WALLET or\
            SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET and \
                SettingRepository.get_key_storage_type() == KeyStorageType.ON_DEVICE:
            self.hw_dialog_update.emit(
                INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )
            hardware_client_store.set_rgb_mode(True)
        elif is_hw and SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            self.hw_dialog_update.emit(
                INFO_REGISTER_WALLET_AND_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )
            hardware_client_store.set_rgb_mode(True)

        if SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            self.run_in_thread(
                CommonOperationRepository.sign_psbt,
                {
                    'args': [unsigned_psbt],
                    'callback': self.on_multisig_psbt_signed,
                    'error_callback': self.on_error,
                },
            )
        else:
            self.run_in_thread(
                CommonOperationRepository.sign_and_finalize_psbt,
                {
                    'args': [unsigned_psbt],
                    'callback': self.on_psbt_signed_and_finalized_success,
                    'error_callback': self.on_error,
                },
            )

    def on_multisig_psbt_signed(self, signed_psbt: str):
        """
        Callback after multisig PSBT is signed (partially).
        Now post to bridge.
        """
        self.hw_dialog_update.emit(
            INFO_POST_TO_BRIDGE, PsbtStatus.BROADCASTING,
        )
        self.run_in_thread(
            RgbRepository.respond_to_operation,
            {
                'args': [self.operation_idx, RespondToOperation.ACK(signed_psbt)],
                'callback': self.on_success_multisig_post,
                'error_callback': self.on_error,
            },
        )

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
