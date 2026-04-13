# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the SendRGBAssetWidget class,
 which represents the UI for send rgb assets
 """
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget
from rgb_lib import AssetSchema
from rgb_lib import Invoice
from rgb_lib import InvoiceData
from rgb_lib import RgbLibError

import src.resources_rc
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_card_repository import SettingCardRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import ReceiveAssetModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import DecodeRgbInvoiceRequestModel
from src.model.rgb_model import ListTransferAssetWithBalanceResponseModel
from src.model.setting_model import DefaultFeeRate
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NOT_ENOUGH_UNCOLORED
from src.utils.error_message import ERROR_SEND_ASSET
from src.utils.error_message import ERROR_UNEXPECTED
from src.utils.helpers import register_multisig_button
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_UTXO_CREATION_REQUIRED_FOR_SENDING
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.confirmation_dialog import ConfirmationDialog
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.loading_screen import LoadingTranslucentScreen
from src.views.components.send_asset import SendAssetWidget
from src.views.components.toast import ToastManager


class SendRGBAssetWidget(QWidget):
    """This class represents all the UI elements of the send RGB assets page."""

    def __init__(self, view_model, draft_data=None):
        self.render_timer = RenderTimer(task_name='RGBSendAsset Rendering')
        super().__init__()
        self._view_model: MainViewModel = view_model
        self.asset_spendable_balance = None
        self.image_path = None
        self.asset_id = None
        self.asset_type = None
        self.asset_name = None
        self.loading_performer = None
        self.rgb_asset_fee_rate_loading_screen = None
        self.send_rgb_hw_dialog = None
        self.value_of_default_fee_rate: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
        self.send_rgb_asset_page = SendAssetWidget(
            self._view_model, 'blind_utxo',
        )
        self.send_rgb_asset_page.fee_rate_value.setText(
            str(self.value_of_default_fee_rate.fee_rate),
        )

        key_storage_type = SettingRepository.get_key_storage_type()
        self.is_hardware_wallet = key_storage_type == KeyStorageType.HARDWARE_WALLET
        self.is_online_wallet = SettingRepository.get_wallet_type(
        ) == WalletType.ONLINE_TYPE_WALLET
        self.is_watch_only = SettingRepository.get_wallet_access_type(
        ) == WalletAccessType.WATCH_ONLY
        self.is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        self._hw_operation_dialog = None
        self._retry_after_utxo = False
        self._utxo_dialog_active = False

        layout = QVBoxLayout()
        layout.addWidget(self.send_rgb_asset_page)
        self.setLayout(layout)
        self.set_originating_page(self._view_model.cfa_view_model.asset_type)
        self.setup_ui_connection()
        self.set_asset_balance()
        self.handle_button_enabled()
        self.handle_spendable_balance_validation()

        if draft_data:
            self.asset_id = draft_data.get('asset_id')
            recipient = draft_data.get('recipient_id')
            amount = draft_data.get('amount')
            if recipient:
                self.send_rgb_asset_page.asset_address_value.setText(recipient)
            if amount:
                self.send_rgb_asset_page.asset_amount_value.setText(
                    str(amount),
                )
        self.sidebar = None
        self.__loading_translucent_screen = LoadingTranslucentScreen(
            parent=self, description_text='Loading',
        )

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        if not self.is_multisig:
            self.send_rgb_asset_page.send_btn.clicked.connect(
                self.send_rgb_asset_button,
            )
        else:
            register_multisig_button(
                self._view_model,
                self.send_rgb_asset_page.send_btn,
                self.send_rgb_asset_button,
            )
        self.send_rgb_asset_page.close_button.clicked.connect(
            self.rgb_asset_page_navigation,
        )
        self._view_model.cfa_view_model.message.connect(
            self.show_cfa_message,
        )
        self.send_rgb_asset_page.asset_address_value.textChanged.connect(
            self.validate_rgb_invoice,
        )
        self.send_rgb_asset_page.asset_amount_value.textChanged.connect(
            self.handle_button_enabled,
        )
        self.send_rgb_asset_page.asset_address_value.textChanged.connect(
            self.handle_button_enabled,
        )
        self._view_model.cfa_view_model.is_loading.connect(
            self.update_loading_state,
        )
        self.send_rgb_asset_page.refresh_button.clicked.connect(
            self.refresh_asset,
        )
        self._view_model.cfa_view_model.txn_list_loaded.connect(
            self.set_asset_balance,
        )
        self._view_model.cfa_view_model.txn_list_loaded.connect(
            self.handle_spendable_balance_validation,
        )
        self._view_model.estimate_fee_view_model.loading_status.connect(
            self.fee_estimation_loader,
        )
        self.send_rgb_asset_page.fee_rate_value.textChanged.connect(
            self.handle_button_enabled,
        )
        self._view_model.cfa_view_model.hw_dialog_update.connect(
            self.handle_send_rgb_hw_dialog_update,
        )
        self._view_model.cfa_view_model.unsigned_psbt.connect(
            self.show_send_rgb_psbt_page,
        )
        self._view_model.utxo_creation_view_model.unsigned_psbt.connect(
            self._on_utxo_unsigned_psbt,
        )
        self._view_model.utxo_creation_view_model.hw_dialog_update.connect(
            self.handle_send_rgb_hw_dialog_update,
        )
        self._view_model.utxo_creation_view_model.utxo_created.connect(
            self._on_utxo_created_and_retry,
        )
        self._view_model.utxo_creation_view_model.psbt_posted_to_bridge.connect(
            self._on_utxo_posted_to_bridge,
        )

    def refresh_asset(self):
        """This method handle the refresh asset on send asset page"""
        self.loading_performer = 'REFRESH_BUTTON'
        view_model = self._view_model.cfa_view_model
        view_model.on_refresh_click()
        self.asset_id = view_model.asset_id
        self.asset_name = view_model.asset_name
        self.image_path = view_model.image_path
        self.asset_type = view_model.asset_type
        self._view_model.cfa_view_model.get_cfa_asset_detail(
            asset_id=self.asset_id, asset_name=self.asset_name, image_path=self.image_path, asset_type=self.asset_type,
        )

    def set_originating_page(self, asset_type):
        """This method sets the originating page for when closing send asset"""
        if asset_type == AssetSchema.NIA:
            self.asset_type = AssetSchema.NIA
        elif asset_type == AssetSchema.IFA:
            self.asset_type = AssetSchema.IFA

    def rgb_asset_page_navigation(self):
        """Navigate to the collectibles asset page."""
        self.sidebar = self._view_model.page_navigation.sidebar()
        if self.asset_type == AssetSchema.NIA:
            self.sidebar.my_fungibles.setChecked(True)
            self._view_model.page_navigation.fungibles_asset_page()
        elif self.asset_type == AssetSchema.IFA:
            self.sidebar.my_inflatable.setChecked(True)
            self._view_model.page_navigation.inflatable_asset_page()
        else:
            self.sidebar.my_collectibles.setChecked(True)
            self._view_model.page_navigation.collectibles_asset_page()

    def send_rgb_asset_button(self):
        """Handle the send RGB asset button click event
        and send the RGB asset to the particular address"""
        try:
            self.loading_performer = 'SEND_BUTTON'
            provided_invoice = self.send_rgb_asset_page.asset_address_value.text()
            amount = self.send_rgb_asset_page.asset_amount_value.text()
            fee_rate = self.send_rgb_asset_page.fee_rate_value.text()
            default_min_confirmation = SettingCardRepository.get_default_min_confirmation()

            # Attempt to decode the RGB invoice
            decoded_rgb_invoice: InvoiceData = RgbRepository.decode_invoice(
                DecodeRgbInvoiceRequestModel(invoice=provided_invoice),
            )
            amount = int(amount.replace(',', ''))
            assignment = type(decoded_rgb_invoice.assignment)(
                amount=int(amount),
            )
            try:
                if (self.is_hardware_wallet and self.is_online_wallet) or self.is_watch_only or self.is_multisig:
                    self._view_model.cfa_view_model.send_begin(
                        decoded_rgb_invoice.recipient_id, decoded_rgb_invoice.transport_endpoints, fee_rate, default_min_confirmation.min_confirmation,
                        assignment,
                    )
                else:
                    self._view_model.cfa_view_model.on_send_click(
                        decoded_rgb_invoice.recipient_id, decoded_rgb_invoice.transport_endpoints, fee_rate, default_min_confirmation.min_confirmation,
                        assignment,
                    )
                # Success toast or indicator can be added here if needed
            except CommonException as e:
                # Handle any errors during the sending process
                ToastManager.error(
                    description=ERROR_SEND_ASSET.format(str(e)),
                )
        except CommonException as e:
            # Handle any unexpected errors during the button click processing
            ToastManager.error(
                description=ERROR_UNEXPECTED.format(str(e.message)),
            )

    def show_cfa_message(self, msg_type: ToastPreset, message: str):
        """Handle show message"""
        if msg_type == ToastPreset.ERROR:
            ToastManager.error(message)
        else:
            ToastManager.success(message)

    def handle_button_enabled(self):
        """Updates the enabled state of the send button."""

        def is_valid_value(value):
            """Checks if the given value is neither empty nor equal to '0'."""
            return bool(value) and value != '0'

        def is_spendable_amount_valid():
            """Checks if the spendable balance is greater than 0 and enough for the transaction."""
            return self.asset_spendable_balance > 0 and self.asset_spendable_balance >= self.send_rgb_asset_page.pay_amount

        def are_fields_valid():
            """Checks if required fields are filled and valid."""
            return (
                is_valid_value(self.send_rgb_asset_page.asset_address_value.text()) and
                # Check if the validation label is hidden
                not self.send_rgb_asset_page.asset_address_validation_label.isVisible() and
                is_valid_value(self.send_rgb_asset_page.asset_amount_value.text()) and
                is_valid_value(self.send_rgb_asset_page.fee_rate_value.text())
            )

        # Now use the helper functions for the condition
        if are_fields_valid() and is_spendable_amount_valid():
            self.send_rgb_asset_page.send_btn.setDisabled(False)
        else:
            self.send_rgb_asset_page.send_btn.setDisabled(True)

    def update_loading_state(self, is_loading: bool):
        """
        Updates the loading state of the proceed_wallet_password object.

        This method handles the loading state by starting or stopping
        the loading animation of the proceed_wallet_password object based
        on the value of is_loading.
        """
        def handle_refresh_button_loading(start: bool):
            """This method starts the loader when refresh button is clicked"""
            self.__loading_translucent_screen.make_parent_disabled_during_loading(
                start,
            )
            if start:
                self.__loading_translucent_screen.start()
            else:
                self.__loading_translucent_screen.stop()

        def handle_send_button_loading(start: bool):
            """This method starts the loader in the send button when it is clicked"""
            if start:
                self.render_timer.start()
                self.send_rgb_asset_page.send_btn.start_loading()
            else:
                self.render_timer.stop()
                self.send_rgb_asset_page.send_btn.stop_loading()

        def handle_fee_estimation_loading(start: bool):
            """This method starts the loader when fee estimation checkbox is clicked"""
            if start:
                self.rgb_asset_fee_rate_loading_screen = LoadingTranslucentScreen(
                    parent=self, description_text='Getting Fee Rate',
                )
                self.rgb_asset_fee_rate_loading_screen.start()
                self.rgb_asset_fee_rate_loading_screen.make_parent_disabled_during_loading(
                    True,
                )
            else:
                self.rgb_asset_fee_rate_loading_screen.stop()
                self.rgb_asset_fee_rate_loading_screen.make_parent_disabled_during_loading(
                    False,
                )

        if self.loading_performer == 'REFRESH_BUTTON':
            handle_refresh_button_loading(is_loading)
        elif self.loading_performer == 'SEND_BUTTON':
            handle_send_button_loading(is_loading)
        elif self.loading_performer == 'FEE_ESTIMATION':
            handle_fee_estimation_loading(is_loading)

    def handle_show_message(self, msg_type: ToastPreset, message: str):
        """Handle show message"""
        if msg_type == ToastPreset.ERROR:
            ToastManager.error(message)
        else:
            ToastManager.success(message)

    def set_asset_balance(self):
        """Set the spendable and total balance of the asset"""
        view_model = self._view_model.cfa_view_model
        asset_transactions: ListTransferAssetWithBalanceResponseModel = view_model.txn_list
        self.asset_spendable_balance = asset_transactions.asset_balance.spendable
        self.send_rgb_asset_page.asset_balance_label_total.setText(
            str(asset_transactions.asset_balance.future),
        )
        self.send_rgb_asset_page.asset_balance_label_spendable.setText(
            str(asset_transactions.asset_balance.spendable),
        )
        if asset_transactions.asset_balance.spendable == 0:
            self.send_rgb_asset_page.send_btn.setDisabled(True)
        else:
            self.send_rgb_asset_page.send_btn.setDisabled(False)

    def handle_spendable_balance_validation(self):
        """This method handle the spendable balance validation message visibility"""
        if self.asset_spendable_balance > 0:
            self.send_rgb_asset_page.spendable_balance_validation.hide()
            self.disable_buttons_on_fee_rate_loading(False)

        if self.asset_spendable_balance == 0:
            self.send_rgb_asset_page.spendable_balance_validation.show()
            self.disable_buttons_on_fee_rate_loading(True)

    def fee_estimation_loader(self, is_loading):
        """This method sets loading performer to FEE_ESTIMATION and starts or stops the loader"""
        self.loading_performer = 'FEE_ESTIMATION'
        self.update_loading_state(is_loading)

    def disable_buttons_on_fee_rate_loading(self, button_status: bool):
        'This method is used to disable the checkboxes and the send button on spendable validation'
        update_button_status = button_status
        if self.asset_spendable_balance == 0:
            update_button_status = True

        self.send_rgb_asset_page.slow_checkbox.setDisabled(
            update_button_status,
        )
        self.send_rgb_asset_page.medium_checkbox.setDisabled(
            update_button_status,
        )
        self.send_rgb_asset_page.fast_checkbox.setDisabled(
            update_button_status,
        )
        self.send_rgb_asset_page.custom_checkbox.setDisabled(
            update_button_status,
        )
        self.send_rgb_asset_page.send_btn.setDisabled(update_button_status)
        self.handle_button_enabled()

    def validate_rgb_invoice(self):
        """
        Validates the RGB invoice input.

        - Hides the validation label initially.
        - Checks if the entered invoice is valid.
        - Displays an error message if the invoice is invalid.
        """
        invoice = self.send_rgb_asset_page.asset_address_value.text().strip()

        if not invoice:
            self.send_rgb_asset_page.asset_address_validation_label.hide()
            return
        try:
            Invoice(invoice)
            self.send_rgb_asset_page.asset_address_validation_label.hide()

        except RgbLibError.InvalidInvoice:
            self.send_rgb_asset_page.asset_address_validation_label.show()
            self.send_rgb_asset_page.send_btn.setDisabled(True)
            self.send_rgb_asset_page.asset_address_validation_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'invalid_invoice',
                ),
            )

    def handle_send_rgb_hw_dialog_update(self, message: str | None, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler."""
        if not self.isVisible():
            return
        self.send_rgb_hw_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        if dialog_type == PsbtStatus.ERROR and message:
            if ('NoAvailableUtxos' in message) or (ERROR_NOT_ENOUGH_UNCOLORED in message):
                # Save draft transfer if UTXOs missing, to avoid manual re-entry
                try:
                    wallet_service = WalletDataService.get_session()
                    if wallet_service is not None:
                        wallet_service.upsert_draft_transfer(
                            asset_id=self._view_model.cfa_view_model.asset_id,
                            recipient_id=self.send_rgb_asset_page.asset_address_value.text(),
                            amount=int(
                                self.send_rgb_asset_page.asset_amount_value.text(),
                            ),
                            fee_rate=SettingCardRepository.get_default_fee_rate().fee_rate,
                            min_confirmation=SettingCardRepository.get_default_min_confirmation().min_confirmation,
                        )
                except Exception as e:
                    print(f"Failed to save draft: {e}")

                self._retry_after_utxo = True
                if self.is_multisig or self.is_watch_only:
                    if self._utxo_dialog_active:
                        return
                    self._utxo_dialog_active = True
                    dialog = ConfirmationDialog(
                        message=INFO_UTXO_CREATION_REQUIRED_FOR_SENDING,
                        parent=self,
                        icon_type='info',
                    )
                    accepted = dialog.exec() == QDialog.Accepted
                    self._utxo_dialog_active = False

                    if not accepted:
                        self._retry_after_utxo = False
                        return
                # For single-sig online wallets, create only 1 UTXO
                is_single_sig_online = (
                    SettingRepository.get_wallet_signature_type(
                    ) == WalletSignatureType.STANDARD_TYPE_WALLET
                    and SettingRepository.get_wallet_access_type() != WalletAccessType.WATCH_ONLY
                    and SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET
                )
                num_utxos = 1 if is_single_sig_online else 3
                self._view_model.utxo_creation_view_model.create_utxos_begin(
                    purpose='send_rgb', num=num_utxos,
                )
                return

        if dialog_type == PsbtStatus.SUCCESS:
            self.send_rgb_hw_dialog.accept()
            return
        self.send_rgb_hw_dialog.update_dialog(message, dialog_type)
        if not self.send_rgb_hw_dialog.isVisible():
            self.send_rgb_hw_dialog.show()

    def _on_utxo_unsigned_psbt(self, psbt: str):
        """Navigate to the receive asset page and display the UTXO creation PSBT."""
        if self._view_model.utxo_creation_view_model.current_purpose != 'send_rgb':
            return
        if psbt:
            self.show_send_rgb_psbt_page(psbt)

    def show_send_rgb_psbt_page(self, psbt):
        """Navigate back and show a success toast for the PSBT."""
        if not self.isVisible():
            return
        if self.asset_type == AssetSchema.NIA:
            page_name = 'NIA page'
        elif self.asset_type == AssetSchema.IFA:
            page_name = 'IFA page'
        else:
            page_name = 'CFA page'
        if psbt:
            if self.is_multisig:
                ToastManager.success(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt_created_successfully', 'PSBT created successfully',
                    ),
                )
                self.rgb_asset_page_navigation()
            else:
                self._view_model.page_navigation.receive_asset_page(
                    ReceiveAssetModel(
                        page_name=page_name,
                        address_info='psbt_info', psbt=psbt, is_signed=False,
                    ),
                )

    def _on_utxo_created_and_retry(self, ok: bool):
        """Retry sending after UTXO creation completes from UI flow."""
        if not ok or not self._retry_after_utxo:
            return
        self._retry_after_utxo = False
        self.send_rgb_asset_button()

    def _on_utxo_posted_to_bridge(self):
        """Handle signal when UTXO creation PSBT is posted to bridge (Multisig)."""
        current_purpose = self._view_model.utxo_creation_view_model.current_purpose
        if current_purpose != 'send_rgb' or not self.isVisible():
            return

        if self.send_rgb_hw_dialog:
            self.send_rgb_hw_dialog.accept()
        ToastManager.success(
            description=INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE,
        )
        # Redirect users back to the asset page (fungible/collectible list)
        self.rgb_asset_page_navigation()
