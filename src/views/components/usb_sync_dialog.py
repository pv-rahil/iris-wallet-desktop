"""
USB sync dialog for selecting USB drives and confirming sync operations.

This module provides a dialog interface for USB synchronization,
allowing users to select from available USB drives and confirm sync operations.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.utils.usb_detector import USBDrive
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton


class USBSyncDialog(QDialog):
    """
    A custom USB sync dialog for selecting USB drives and confirming sync operations.

    This dialog displays available USB drives and allows users to select one
    for synchronization. It uses a frameless window design with a blur effect.
    """

    def __init__(self, usb_drives: list[USBDrive], parent: QWidget):
        """
        Initialize the USB sync dialog.

        Args:
            usb_drives: List of detected USB drives.
            parent: Parent widget for this dialog.
        """
        super().__init__(parent)
        self.parent_widget = parent if parent else QWidget()
        self.usb_drives = usb_drives
        self.selected_drive = None

        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(10)

        self.setObjectName('usb_sync_dialog')
        self.setMinimumSize(QSize(400, 100))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setStyleSheet(
            load_stylesheet('views/qss/usb_sync_dialog.qss'),
        )

        dialog_layout = QVBoxLayout(self)

        # Title label
        self.title_label = QLabel(self)
        self.title_label.setObjectName('title_label')
        dialog_layout.addWidget(self.title_label)

        # Message label
        self.message_label = QLabel(self)
        self.message_label.setObjectName('message_label')
        self.message_label.setWordWrap(True)
        dialog_layout.addWidget(self.message_label)

        # USB drive selection row
        usb_row_layout = QHBoxLayout()
        usb_row_layout.setContentsMargins(6, 0, 6, 0)
        usb_row_layout.setSpacing(5)

        # USB name label
        self.usb_name_label = QLabel(self)
        self.usb_name_label.setObjectName('usb_name_label')
        self.usb_name_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'selected_device', None,
            ),
        )
        self.usb_name_label.setMinimumWidth(90)
        usb_row_layout.addWidget(self.usb_name_label)

        if len(self.usb_drives) > 1:
            # Dropdown for multiple drives
            self.drive_combobox = QComboBox(self)
            self.drive_combobox.setObjectName('drive_combobox')
            self.drive_combobox.setMinimumSize(QSize(200, 35))
            self.drive_combobox.setMaximumSize(QSize(400, 35))
            for i, drive in enumerate(self.usb_drives):
                drive_text = drive.name
                self.drive_combobox.addItem(drive_text, i)
            usb_row_layout.addWidget(self.drive_combobox, 1)
        else:
            # Single drive name
            self.drive_combobox = QComboBox(self)
            self.drive_combobox.setObjectName('drive_combobox')
            self.drive_combobox.setMinimumSize(QSize(200, 35))
            self.drive_combobox.setMaximumSize(QSize(400, 35))
            self.drive_combobox.setEnabled(False)
            drive = self.usb_drives[0]
            self.drive_combobox.addItem(drive.name)

            # Hide dropdown arrow
            self.drive_combobox.setStyleSheet("""
                QComboBox::drop-down {
                    border: 0px;
                    width: 0px;
                }
                QComboBox::down-arrow {
                    image: none;
                }
            """)
            usb_row_layout.addWidget(self.drive_combobox, 1)

        dialog_layout.addLayout(usb_row_layout)

        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName('button_layout')
        self.button_layout.setContentsMargins(6, 6, 6, 12)

        self.cancel_button = SecondaryButton()
        self.cancel_button.setMinimumSize(QSize(180, 35))
        self.cancel_button.setMaximumSize(QSize(200, 35))
        self.button_layout.addWidget(self.cancel_button)

        self.continue_button = PrimaryButton()
        self.continue_button.setMinimumSize(QSize(180, 35))
        self.continue_button.setMaximumSize(QSize(200, 35))
        self.button_layout.addWidget(self.continue_button)

        dialog_layout.addLayout(self.button_layout)
        self.setup_connections()
        self.retranslate_ui()

    def setup_connections(self):
        """Set up signal connections for UI elements."""
        self.continue_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def retranslate_ui(self):
        """Retranslate UI elements with localized text."""
        self.title_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_detected_sync_prompt', None,
            ),
        )
        self.message_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'confirm_usb_sync', None,
            ),
        )
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'sync', None,
            ),
        )
        self.cancel_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel', None,
            ),
        )

    def get_selected_drive(self) -> USBDrive | None:
        """
        Get the selected USB drive.

        Returns:
            USBDrive | None: The selected USB drive or None if no selection.
        """
        if len(self.usb_drives) == 1:
            return self.usb_drives[0]
        if hasattr(self, 'drive_combobox'):
            current_index = self.drive_combobox.currentIndex()
            if current_index >= 0:
                return self.usb_drives[current_index]
        return None

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

    def reject(self):
        """Handle the Cancel button click, remove blur, and reject the dialog."""
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        super().reject()
