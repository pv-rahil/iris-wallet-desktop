# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the ReceiveRGBAssetWidget class,
 which represents the UI for receive CFA.
 """
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget
from rgb_lib import AssetSchema

import src.resources_rc
from src.data.repository.setting_card_repository import SettingCardRepository
from src.model.common_operation_model import ReceiveAssetModel
from src.model.enums.enums_model import Enum
from src.model.enums.enums_model import ToastPreset
from src.model.selection_page_model import AssetDataModel
from src.model.setting_model import DefaultProxyEndpoint
from src.utils.common_utils import copy_text
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.info_message import INFO_UTXO_REQUIRED
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.loading_screen import LoadingTranslucentScreen
from src.views.components.receive_asset import ReceiveAssetWidget
from src.views.components.toast import ToastManager


class ReceiveRGBAssetWidget(QWidget):
    """This class represents all the UI elements of the Receive rgb asset page."""

    def __init__(self, view_model, params: AssetDataModel):
        super().__init__()
        self.render_timer = RenderTimer(task_name='ReceiveRGBAsset Rendering')
        self.render_timer.start()
        self._view_model: MainViewModel = view_model
        self.originating_page = params.asset_type
        self.asset_id = params.asset_id
        self.close_page_navigation = params.close_page_navigation
        self.default_min_confirmation = SettingCardRepository.get_default_min_confirmation()
        self.receive_rgb_asset_page = ReceiveAssetWidget(
            view_model=self._view_model,
            params=ReceiveAssetModel(
                page_name='CFA page',
                address_info='cfa_address_info',
            ),
        )
        self.__loading_translucent_screen = LoadingTranslucentScreen(
            parent=self, description_text='Loading', dot_animation=True,
        )
        # Adding the receive asset widget to the layout of this widget
        layout = QVBoxLayout()
        layout.addWidget(self.receive_rgb_asset_page)
        self.setLayout(layout)
        self.generate_invoice()
        self.setup_ui_connection()

    def generate_invoice(self):
        """Call get rgb invoice to get invoice"""
        if self.originating_page in [
            AssetSchema.NIA,
            'fungibles',
            AssetSchema.CFA,
            'collectibles',
            'view_unspent_list',
            'faucets',
            'settings',
            'help',
            'about',
            'backup',
        ]:
            proxy_endpoint: DefaultProxyEndpoint = SettingCardRepository.get_default_proxy_endpoint()
            self._view_model.receive_cfa_view_model.get_rgb_invoice(
                minimum_confirmations=self.default_min_confirmation.min_confirmation, asset_id=self.asset_id, transport_endpoints=[
                    proxy_endpoint.endpoint,
                ],
            )

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.show_receive_rgb_loading()
        self.receive_rgb_asset_page.copy_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy_rgb_invoice', None,
            ),
        )
        self.receive_rgb_asset_page.address_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'rgb_invoice_label', None,
            ),
        )
        self.receive_rgb_asset_page.copy_button.clicked.connect(
            lambda: copy_text(self.receive_rgb_asset_page.receiver_address),
        )
        self.receive_rgb_asset_page.copy_button.clicked.connect(
            lambda: self.receive_rgb_asset_page.copy_button.setText('Copied!'),
        )
        self.receive_rgb_asset_page.receive_asset_close_button.clicked.connect(
            self.close_button_navigation,
        )
        self._view_model.receive_cfa_view_model.address.connect(
            self.update_address,
        )
        self._view_model.receive_cfa_view_model.message.connect(
            self.handle_message,
        )
        self._view_model.receive_cfa_view_model.hide_loading.connect(
            self.hide_loading_screen,
        )
        # Connect to UTXO creation started signal to suppress error toasts during UTXO creation
        self._view_model.utxo_creation_view_model.utxo_creation_started.connect(
            self._view_model.receive_cfa_view_model.on_utxo_creation_started,
        )
        # Connect to hardware wallet dialog signals
        self._view_model.utxo_creation_view_model.hw_dialog_update.connect(
            self.handle_receive_cfa_hw_dialog_update,
        )
        self._view_model.utxo_creation_view_model.utxo_created.connect(
            self.handle_receive_cfa_utxo_created,
        )
        self._view_model.utxo_creation_view_model.utxo_required.connect(
            self.handle_receive_cfa_utxo_required,
        )
        self._view_model.utxo_creation_view_model.psbt_finalized.connect(
            self.show_receive_cfa_psbt_page,
        )

    def close_button_navigation(self):
        """
        Navigate to the specified page when the close button is clicked.
        """
        if self.close_page_navigation == AssetSchema.CFA:
            self._view_model.page_navigation.collectibles_asset_page()
        elif self.close_page_navigation == AssetSchema.NIA:
            self._view_model.page_navigation.fungibles_asset_page()
        else:
            navigation_map = {
                'NIA': self._view_model.page_navigation.fungibles_asset_page,
                'fungibles': self._view_model.page_navigation.fungibles_asset_page,
                'CFA': self._view_model.page_navigation.collectibles_asset_page,
                'collectibles': self._view_model.page_navigation.collectibles_asset_page,
                'view_unspent_list': self._view_model.page_navigation.view_unspent_list_page,
                'faucets': self._view_model.page_navigation.faucets_page,
                'settings': self._view_model.page_navigation.settings_page,
                'help': self._view_model.page_navigation.help_page,
                'about': self._view_model.page_navigation.about_page,
                'backup': self._view_model.page_navigation.backup_page,
            }
            receive_asset_navigation = navigation_map.get(
                self.originating_page,
            )
            if receive_asset_navigation:
                receive_asset_navigation()
            else:
                ToastManager.error(
                    description=f'No navigation defined for {
                        self.originating_page
                    }',
                )

    def update_address(self, address: str):
        """This method used to update new address"""
        self.receive_rgb_asset_page.update_qr_and_address(address)

    def handle_message(self, msg_type: int, message: str):
        """This method handled to show message."""
        if msg_type == ToastPreset.ERROR:
            ToastManager.error(message)
        else:
            ToastManager.success(message)

    def show_receive_rgb_loading(self):
        """This method handled show loading screen on receive assets page"""
        self.receive_rgb_asset_page.label.hide()
        self.receive_rgb_asset_page.receiver_address.hide()
        self.__loading_translucent_screen.set_description_label_direction(
            'Bottom',
        )
        self.__loading_translucent_screen.start()
        self.receive_rgb_asset_page.copy_button.hide()

    def hide_loading_screen(self):
        """This method handled stop loading screen on receive assets page"""
        self.render_timer.stop()
        self.receive_rgb_asset_page.label.show()
        self.receive_rgb_asset_page.receiver_address.show()
        self.__loading_translucent_screen.stop()
        self.receive_rgb_asset_page.copy_button.show()

    def handle_receive_cfa_hw_dialog_update(self, message: str, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler for receive CFA."""
        receive_cfa_hw_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        receive_cfa_hw_dialog.update_dialog(message, dialog_type)
        if not receive_cfa_hw_dialog.isVisible():
            receive_cfa_hw_dialog.show()

    def handle_receive_cfa_utxo_created(self):
        """Close the hardware wallet dialog after UTXO creation for receive CFA."""
        dlg = HardwareWalletOperationDialog.get_instance(parent=self)
        if dlg.isVisible():
            dlg.accept()

    def handle_receive_cfa_utxo_required(self):
        """Shows the dialog for utxo require for receive CFA"""
        receive_cfa_utxo_required_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        receive_cfa_utxo_required_dialog.set_utxo_required_dialog(
            INFO_UTXO_REQUIRED,
        )
        receive_cfa_utxo_required_dialog.done_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
            ),
        )
        receive_cfa_utxo_required_dialog.done_button.clicked.connect(
            self._view_model.utxo_creation_view_model.create_utxos_begin,
        )
        receive_cfa_utxo_required_dialog.cancel_button.clicked.connect(
            receive_cfa_utxo_required_dialog.reject,
        )
        receive_cfa_utxo_required_dialog.exec()

    def show_receive_cfa_psbt_page(self, psbt):
        """Navigate to the receive asset page and display the PSBT as a QR code for receive CFA."""
        self._view_model.page_navigation.receive_asset_page(
            ReceiveAssetModel(
                page_name='Receive CFA page',
                address_info='psbt_info', psbt=psbt,
            ),
        )
        self.receive_rgb_asset_page.receive_asset_close_button.clicked.connect(
            self.close_button_navigation,
        )
