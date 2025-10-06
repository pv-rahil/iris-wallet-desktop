# pylint: disable=too-many-statements
"""Confirmation dialog box module"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import CONFIRMATION_DIALOG_CANCEL_BUTTON
from accessible_constant import CONFIRMATION_DIALOG_CHECKBOX
from accessible_constant import CONFIRMATION_DIALOG_CONTINUE_BUTTON
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton


class ConfirmationDialog(QDialog):
    """
    A custom confirmation dialog with a message and two buttons: Continue and Cancel.

    This dialog is designed to display a message to the user and allow them to confirm
    or cancel an action. It uses a frameless window design with a blur effect and is modal.
    """

    def __init__(self, message: str, parent, icon_type=None):
        super().__init__(parent)
        self.parent_widget = parent if parent else QWidget()
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(10)
        self.icon_type = icon_type
        self.check_box = None

        self.setObjectName('confirmation_dialog')
        self.setAccessibleName(CONFIRMATION_DIALOG)
        self.resize(300, 200)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/confirmation_dialog.qss',
            ),
        )

        dialog_layout = QVBoxLayout(self)

        # Header/message area
        if self.icon_type == 'warning':
            header_layout = QHBoxLayout()
            header_layout.setObjectName('header_layout')
            header_layout.setContentsMargins(6, 0, 5, 0)
            header_layout.setSpacing(0)

            self.icon_label = QLabel(self)
            self.icon_label.setObjectName('icon_label')
            pixmap = QPixmap(':/assets/warning_yellow.png')
            if not pixmap.isNull():
                self.icon_label.setPixmap(
                    pixmap.scaled(
                        72, 72, Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    ),
                )
            header_layout.addWidget(
                self.icon_label, Qt.AlignmentFlag.AlignCenter,
            )

            self.message_label = QLabel(message, self)
            self.message_label.setObjectName('message_label')
            self.message_label.setStyleSheet(
                'padding-bottom:25px;',
            )
            self.message_label.setMinimumSize(QSize(400, 110))
            self.message_label.setWordWrap(True)
            header_layout.addWidget(self.message_label)

            dialog_layout.addLayout(header_layout)

            # Confirmation checkbox (enables Continue when checked)
            self.check_box = QCheckBox(self)
            self.check_box.setObjectName('check_box')
            self.check_box.setAccessibleName(CONFIRMATION_DIALOG_CHECKBOX)
            dialog_layout.addWidget(self.check_box)
        else:
            self.message_label = QLabel(message, self)
            self.message_label.setObjectName('message_label')
            self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.message_label.setWordWrap(True)

            dialog_layout.addWidget(self.message_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName('button_layout')
        self.button_layout.setContentsMargins(6, 6, 6, 12)

        self.confirmation_dialog_cancel_button = SecondaryButton()
        self.confirmation_dialog_cancel_button.setAccessibleName(
            CONFIRMATION_DIALOG_CANCEL_BUTTON,
        )
        self.confirmation_dialog_cancel_button.setMinimumSize(QSize(220, 35))
        self.confirmation_dialog_cancel_button.setMaximumSize(QSize(300, 35))
        self.button_layout.addWidget(self.confirmation_dialog_cancel_button)

        self.confirmation_dialog_continue_button = PrimaryButton()
        self.confirmation_dialog_continue_button.setAccessibleName(
            CONFIRMATION_DIALOG_CONTINUE_BUTTON,
        )
        self.confirmation_dialog_continue_button.setMinimumSize(QSize(220, 35))
        self.confirmation_dialog_continue_button.setMaximumSize(QSize(300, 35))
        self.button_layout.addWidget(self.confirmation_dialog_continue_button)

        dialog_layout.addLayout(self.button_layout)

        # If warning, disable Continue until confirmed
        if self.icon_type == 'warning':
            self.confirmation_dialog_continue_button.setEnabled(False)
            if self.check_box:
                self.check_box.stateChanged.connect(
                    self.handle_continue_button,
                )

        self.setup_ui_connection()
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslate UI."""
        self.confirmation_dialog_continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue', None,
            ),
        )
        self.confirmation_dialog_cancel_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel', None,
            ),
        )
        if self.check_box:
            self.check_box.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'sync_confirmation_checkbox_message', None,
                ),
            )

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.confirmation_dialog_continue_button.clicked.connect(self.accept)
        self.confirmation_dialog_cancel_button.clicked.connect(self.reject)

    def handle_continue_button(self):
        """Enable/disable Continue based on checkbox state (only for warning)."""
        if self.check_box:
            self.confirmation_dialog_continue_button.setEnabled(
                self.check_box.isChecked(),
            )

    def showEvent(self, event):  # pylint:disable=invalid-name
        """Apply the blur effect to the parent widget when the dialog is shown."""
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(self.blur_effect)
        super().showEvent(event)

    def closeEvent(self, event):  # pylint:disable=invalid-name
        """Remove the blur effect from the parent widget when the dialog is closed."""
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        super().closeEvent(event)

    def accept(self):
        """Handle the Continue button click, remove blur, and accept the dialog."""
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        super().accept()
