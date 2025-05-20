"""This module contains the TermsViewModel class, which represents the view model
for the term and conditions page activities.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal


class TermsViewModel(QObject):
    """This class represents the activities of the term and conditions page."""

    accept_button_clicked = Signal(str)  # Signal to update in the view
    decline_button_clicked = Signal(str)

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation

    def on_accept_click(self):
        """This method handled to navigate welcome page"""
        self._page_navigation.welcome_page()

    def on_decline_click(self):
        """This method is used for decline the terms and conditions."""
        QCoreApplication.instance().quit()
