# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the ReceiveBitcoinWidget class,
 which represents the UI for receive bitcoin.
 """
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

import src.resources_rc
from src.utils.common_utils import copy_text
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.loading_screen import LoadingTranslucentScreen
from src.views.components.receive_asset import ReceiveAssetWidget


class ReceiveBitcoinWidget(QWidget):
    """This class represents all the UI elements of the Receive bitcoin page."""

    def __init__(self, view_model):
        super().__init__()
        self.render_timer = RenderTimer(
            task_name='BitcoinReceiveAsset Rendering',
        )
        self.render_timer.start()
        self._view_model: MainViewModel = view_model
        self._loading_translucent_screen = None

        self.receive_bitcoin_page = ReceiveAssetWidget(
            self._view_model, 'bitcoin_page', 'address_info',
        )
        # Adding the receive asset widget to the layout of this widget
        layout = QVBoxLayout()
        layout.addWidget(self.receive_bitcoin_page)
        self.setLayout(layout)

        self.setup_ui_connection()

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.show_receive_bitcoin_loading()
        self._view_model.receive_bitcoin_view_model.get_bitcoin_address(
            is_hard_refresh=True,
        )
        self.receive_bitcoin_page.copy_button.clicked.connect(
            lambda: copy_text(self.receive_bitcoin_page.receiver_address),
        )
        self.receive_bitcoin_page.receive_asset_close_button.clicked.connect(
            self.close_button_navigation,
        )
        self._view_model.receive_bitcoin_view_model.address.connect(
            self.update_address,
        )
        self._view_model.receive_bitcoin_view_model.is_loading.connect(
            self.hide_bitcoin_loading_screen,
        )

    def close_button_navigation(self):
        """
        Navigate to the specified page when the close button is clicked.
        """
        self._view_model.page_navigation.bitcoin_page()

    def update_address(self, address: str):
        """This method used to update new address"""
        self.receive_bitcoin_page.update_qr_and_address(address)

    def show_receive_bitcoin_loading(self):
        """This method handled show loading screen on receive bitcoin page"""
        self.receive_bitcoin_page.label.hide()
        self.receive_bitcoin_page.receiver_address.hide()
        self._loading_translucent_screen = LoadingTranslucentScreen(
            parent=self, description_text='Getting address',
        )
        self._loading_translucent_screen.set_description_label_direction(
            'Bottom',
        )
        self._loading_translucent_screen.start()
        self.receive_bitcoin_page.copy_button.hide()

    def hide_bitcoin_loading_screen(self, is_loading):
        """This method handled stop loading screen on receive bitcoin page"""
        if not is_loading:
            self.receive_bitcoin_page.label.show()
            self.receive_bitcoin_page.receiver_address.show()
            self.render_timer.stop()
            self._loading_translucent_screen.stop()
            self.receive_bitcoin_page.copy_button.show()
