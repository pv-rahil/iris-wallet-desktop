# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the ReceiveRGBAssetWidget class,
 which represents the UI for receive rgb25.
 """
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget
from rgb_lib import AssetIface

import src.resources_rc
from src.data.repository.setting_card_repository import SettingCardRepository
from src.model.enums.enums_model import ToastPreset
from src.model.selection_page_model import AssetDataModel
from src.model.setting_model import DefaultProxyEndpoint
from src.utils.common_utils import copy_text
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
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
            self._view_model,
            'RGB25 page',
            'rgb25_address_info',
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
            AssetIface.RGB20,
            'fungibles',
            AssetIface.RGB25,
            'collectibles',
            'channel_management',
            'view_unspent_list',
            'faucets',
            'settings',
            'help',
            'about',
            'backup',
        ]:
            proxy_endpoint: DefaultProxyEndpoint = SettingCardRepository.get_default_proxy_endpoint()
            self._view_model.receive_rgb25_view_model.get_rgb_invoice(
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
        self._view_model.receive_rgb25_view_model.address.connect(
            self.update_address,
        )
        self._view_model.receive_rgb25_view_model.message.connect(
            self.handle_message,
        )
        self._view_model.receive_rgb25_view_model.hide_loading.connect(
            self.hide_loading_screen,
        )

    def close_button_navigation(self):
        """
        Navigate to the specified page when the close button is clicked.
        """
        if self.close_page_navigation == AssetIface.RGB25:
            self._view_model.page_navigation.collectibles_asset_page()
        elif self.close_page_navigation == AssetIface.RGB20:
            self._view_model.page_navigation.fungibles_asset_page()
        else:
            navigation_map = {
                'RGB20': self._view_model.page_navigation.fungibles_asset_page,
                'fungibles': self._view_model.page_navigation.fungibles_asset_page,
                'RGB25': self._view_model.page_navigation.collectibles_asset_page,
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
