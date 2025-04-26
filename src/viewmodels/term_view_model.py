"""This module contains the TermsViewModel class, which represents the view model
for the term and conditions page activities.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.model.enums.enums_model import WalletType
from src.model.selection_page_model import SelectionPageModel


class TermsViewModel(QObject):
    """This class represents the activities of the term and conditions page."""

    accept_button_clicked = Signal(str)  # Signal to update in the view
    decline_button_clicked = Signal(str)

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation

    def on_accept_click(self):
        """This method handled to navigate wallet selection"""
        # title = 'connection_type'
        # embedded_logo = ':/assets/embedded.png'
        # logo_1_title = WalletType.EMBEDDED_TYPE_WALLET.value
        # connect_logo = ':/assets/remote.png'
        # logo_2_title = WalletType.REMOTE_TYPE_WALLET.value
        # params = SelectionPageModel(
        #     title=title,
        #     logo_1_path=embedded_logo,
        #     logo_1_title=logo_1_title,
        #     logo_2_path=connect_logo,
        #     logo_2_title=logo_2_title,
        #     asset_id='none',
        #     callback='none',
        #     back_page_navigation=self._page_navigation.term_and_condition_page,
        # )
        self._page_navigation.welcome_page()

    def on_decline_click(self):
        """This method is used for decline the terms and conditions."""
        QCoreApplication.instance().quit()
