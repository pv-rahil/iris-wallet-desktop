# pylint: disable=too-few-public-methods
"""Displays a warning dialog for rgb lib incompatibility issues."""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QMessageBox

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


class RgbLibIncompatibilityDialog:
    """Shows a dialog when the rgb lib is incompatible.

    Options:
    - **Delete App Data:** Resets the wallet.
    - **Quit App:** Closes the application.
    """

    def __init__(self):
        """Initializes and configures the dialogs."""
        super().__init__()

        self.rgb_lib_incompatibility_dialog = QMessageBox()
        self.rgb_lib_incompatibility_dialog.setIcon(QMessageBox.Icon.Warning)
        self.delete_app_data_button = self.rgb_lib_incompatibility_dialog.addButton(
            'delete', QMessageBox.AcceptRole,
        )
        self.close_button = self.rgb_lib_incompatibility_dialog.addButton(
            'close', QMessageBox.RejectRole,
        )
        self.rgb_lib_incompatibility_dialog.setDefaultButton(self.close_button)

        self.confirmation_dialog = QMessageBox()
        self.confirmation_dialog.setIcon(QMessageBox.Icon.Critical)
        self.confirm_delete_button = self.confirmation_dialog.addButton(
            'confirm_delete', QMessageBox.AcceptRole,
        )
        self.cancel = self.confirmation_dialog.addButton(
            'cancel_delete', QMessageBox.RejectRole,
        )

        self.retranslate_ui()

    def show_rgb_lib_incompatibility_dialog(self):
        """Displays the warning dialog."""
        self.rgb_lib_incompatibility_dialog.exec()

    def retranslate_ui(self):
        """Sets localized text for the dialogs."""
        self.delete_app_data_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'delete_app_data',
            ),
        )
        self.rgb_lib_incompatibility_dialog.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'rgb_lib_incompatibility_dialog_desc',
            ),
        )
        self.close_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'crash_dialog_close_app',
            ),
        )
        self.confirmation_dialog.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'confirm_app_data_deletion',
            ),
        )
        self.confirm_delete_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'delete_app_data',
            ),
        )
        self.cancel.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel',
            ),
        )

    def show_confirmation_dialog(self):
        """Displays a confirmation dialog before deleting data."""
        self.confirmation_dialog.exec()
