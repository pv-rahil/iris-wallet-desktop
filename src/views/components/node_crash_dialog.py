# pylint: disable=too-few-public-methods
"""This module contains the class for Message box which is displayed when node is crashed"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from src.utils.constant import GITHUB_ISSUE_LINK
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


class CrashDialogBox:
    """Displays a dialog when the RGB Lightning Node crashes, exits, or is killed.

    This dialog informs the user about the failure, provides a link to report the issue,
    and offers options to restart the node or close the application.
    """

    def __init__(self):
        """Initializes the crash dialog with a critical error icon, a message, and action buttons.

        The dialog presents:
        - A message explaining the node failure with a link to report the issue.
        - A 'Restart Node' button to retry the connection.
        - A 'Close Application' button to exit the app.
        """
        super().__init__()

        self.message_box = QMessageBox()

        self.message_box.setIcon(QMessageBox.Icon.Critical)
        self.message_box.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'rgb_ln_node_connection_failed', None,
            ).format(f"<a href='{GITHUB_ISSUE_LINK}'>GitHub</a>", '<br><br>'),
        )
        self.message_box.setTextFormat(Qt.TextFormat.RichText)
        self.message_box.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction,
        )
        self.retry_button = self.message_box.addButton(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'crash_dialog_restart_node', None,
            ),
            QMessageBox.AcceptRole,
        )
        self.close_button = self.message_box.addButton(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'crash_dialog_close_app', None,
            ),
            QMessageBox.RejectRole,
        )
        self.message_box.setDefaultButton(self.retry_button)

        self.message_box.exec()
