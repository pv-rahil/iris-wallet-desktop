# pylint: disable=too-many-instance-attributes,too-many-statements
"""
USB sync dialog for selecting USB drives and confirming sync operations.

This module provides a dialog interface for USB synchronization,
allowing users to select from available USB drives and confirm sync operations.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from accessible_constant import USB_SYNC_DIALOG
from accessible_constant import USB_SYNC_DIALOG_CANCEL_BUTTON
from accessible_constant import USB_SYNC_DIALOG_CONTINUE_BUTTON
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletEntryType
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.utils.logging import logger
from src.utils.usb_detector import USBDetector
from src.utils.usb_detector import USBDrive
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton


class USBSyncDialog(QDialog):
    """
    A custom USB sync dialog for selecting USB drives and confirming sync operations.

    This dialog displays available USB drives and allows users to select one
    for synchronization. It uses a frameless window design with a blur effect.
    """

    def __init__(self, usb_drives: list[USBDrive], parent: QWidget, is_from_header: bool = False):
        """
        Initialize the USB sync dialog.

        Args:
            usb_drives: List of detected USB drives.
            parent: Parent widget for this dialog.
            is_from_header: Boolean indicating if the dialog is opened from the header.
        """
        super().__init__(parent)
        self.parent_widget = parent if parent else QWidget()
        self.usb_drives = usb_drives
        self.selected_drive = None
        self.usb_detector = USBDetector()
        self.usb_row_layout = None
        self.fingerprint_row_layout = None
        self.is_from_header = is_from_header

        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(10)

        self.setObjectName('usb_sync_dialog')
        self.setAccessibleName(USB_SYNC_DIALOG)
        self.setMinimumSize(QSize(400, 100))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setStyleSheet(
            load_stylesheet('views/qss/usb_sync_dialog.qss'),
        )

        # Setup timer for USB detection
        self.usb_check_timer = QTimer(self)
        self.usb_check_timer.timeout.connect(self.check_usb_devices)
        self.usb_check_timer.start(5000)  # Check every 5 seconds

        dialog_layout = QVBoxLayout(self)

        # Title label
        self.title_label = QLabel(self)
        self.title_label.setObjectName('title_label')
        self.usb_name_label = QLabel(self)
        self.usb_name_label.setObjectName('usb_name_label')
        self.drive_combobox = QComboBox(self)
        self.drive_combobox.setObjectName('drive_combobox')
        self.drive_combobox.hide()
        # Master fingerprint widgets
        self.fingerprint_label = QLabel(self)
        self.fingerprint_label.setObjectName('fingerprint_label')
        self.fingerprint_value_label = QLabel(self)
        self.fingerprint_value_label.setObjectName('fingerprint_value_label')
        dialog_layout.addWidget(self.title_label)

        # Message label
        self.message_label = QLabel(self)
        self.message_label.setObjectName('message_label')
        self.message_label.setWordWrap(True)
        dialog_layout.addWidget(self.message_label)

        if self.usb_drives:
            if SettingRepository.get_wallet_entry_type() == WalletEntryType.LOAD and not self.is_from_header:
                self.fingerprint_row_layout = self._create_fingerprint_row()
                dialog_layout.addLayout(self.fingerprint_row_layout)
            self.usb_row_layout = self._create_usb_selection_row()
            dialog_layout.addLayout(self.usb_row_layout)

        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName('button_layout')
        self.button_layout.setContentsMargins(6, 6, 6, 12)

        self.cancel_button = SecondaryButton()
        self.cancel_button.setAccessibleName(USB_SYNC_DIALOG_CANCEL_BUTTON)
        self.cancel_button.setMinimumSize(QSize(180, 35))
        self.cancel_button.setMaximumSize(QSize(200, 35))
        self.button_layout.addWidget(self.cancel_button)

        self.continue_button = PrimaryButton()
        self.continue_button.setAccessibleName(USB_SYNC_DIALOG_CONTINUE_BUTTON)
        self.continue_button.setMinimumSize(QSize(180, 35))
        self.continue_button.setMaximumSize(QSize(200, 35))
        self.button_layout.addWidget(self.continue_button)

        dialog_layout.addLayout(self.button_layout)
        self.setup_connections()
        self.retranslate_ui()

    def _create_usb_selection_row(self) -> QHBoxLayout:
        """Create and return a USB drive selection layout."""
        usb_row_layout = QHBoxLayout()
        usb_row_layout.setContentsMargins(6, 5, 6, 5)
        usb_row_layout.setSpacing(5)

        self.usb_name_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'selected_device', None,
            ),
        )
        self.usb_name_label.setMinimumWidth(90)
        usb_row_layout.addWidget(self.usb_name_label)
        self.drive_combobox.show()
        self.drive_combobox.setMinimumSize(QSize(200, 35))
        self.drive_combobox.setMaximumSize(QSize(400, 35))

        if len(self.usb_drives) > 1:
            for i, drive in enumerate(self.usb_drives):
                usb_row_layout.addWidget(self.drive_combobox, 1)
                self.drive_combobox.addItem(drive.name, i)
        else:
            self.drive_combobox.setEnabled(False)
            self.drive_combobox.addItem(self.usb_drives[0].name)
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

        return usb_row_layout

    def _create_fingerprint_row(self) -> QHBoxLayout:
        """Create and return a master fingerprint row with a static value label."""
        fp_row_layout = QHBoxLayout()
        fp_row_layout.setContentsMargins(6, 0, 6, 0)
        fp_row_layout.setSpacing(5)

        # Label
        self.fingerprint_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'device_master_fingerprint', None,
            ),
        )
        self.fingerprint_label.setMinimumWidth(90)
        fp_row_layout.addWidget(self.fingerprint_label)

        # Value label
        self.refresh_fingerprint_value()
        fp_row_layout.addWidget(self.fingerprint_value_label, 1)

        return fp_row_layout

    def check_usb_devices(self):
        """Check for USB devices and update UI if needed."""
        try:
            current_usb_drives = self.usb_detector.detect_usb_drives()
            # Check if USB status has changed
            if bool(current_usb_drives) != bool(self.usb_drives):
                self.usb_drives = current_usb_drives
                self.update_usb_list()
        except Exception:
            # Silently handle any USB detection errors
            pass

    def update_usb_list(self):
        """Update the UI when USB status changes."""
        if self.usb_row_layout:
            while self.usb_row_layout.count():
                item = self.usb_row_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.usb_row_layout.deleteLater()
            self.usb_row_layout = None

        # Remove fingerprint row if exists
        if self.fingerprint_row_layout:
            while self.fingerprint_row_layout.count():
                item = self.fingerprint_row_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.fingerprint_row_layout.deleteLater()
            self.fingerprint_row_layout = None

        dialog_layout = self.layout()
        if dialog_layout and self.usb_drives:
            self.usb_row_layout = self._create_usb_selection_row()
            dialog_layout.insertLayout(2, self.usb_row_layout)
            # Insert fingerprint row just below USB selection row
            self.fingerprint_row_layout = self._create_fingerprint_row()
            dialog_layout.insertLayout(3, self.fingerprint_row_layout)

        self.retranslate_ui()

    def setup_connections(self):
        """Set up signal connections for UI elements."""
        self.continue_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        # Refresh fingerprint value when drive selection changes
        if hasattr(self, 'drive_combobox'):
            self.drive_combobox.currentIndexChanged.connect(
                self.refresh_fingerprint_value,
            )

    def refresh_fingerprint_value(self):
        """Update the fingerprint value label based on currently selected drive."""
        selected_index = 0
        if self.usb_drives and len(self.usb_drives) > 1 and hasattr(self, 'drive_combobox'):
            selected_index = max(0, self.drive_combobox.currentIndex())
        if self.usb_drives and 0 <= selected_index < len(self.usb_drives):
            drive = self.usb_drives[selected_index]
            fingerprints = self.list_usb_zip_files(drive)
            value = fingerprints[0] if fingerprints else ''
        else:
            value = ''
        self.fingerprint_value_label.setText(value)

    def retranslate_ui(self):
        """Retranslate UI elements with localized text."""
        if self.usb_drives:
            # USB drives are available - show sync dialog
            self.title_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'sync_prompt', None,
                ),
            )
            self.message_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'confirm_usb_sync', None,
                ),
            )
            self.continue_button.setEnabled(True)
            self.resize(400, 201)
        else:
            # No USB drives detected - show no USB message
            self.title_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'no_usb_detected', None,
                ),
            )
            self.message_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'no_usb_detected_message', None,
                ),
            )
            self.resize(400, 160)
            self.continue_button.setEnabled(False)
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
        if not self.usb_drives:
            return None
        if len(self.usb_drives) == 1:
            return self.usb_drives[0]
        if hasattr(self, 'drive_combobox'):
            current_index = self.drive_combobox.currentIndex()
            if current_index >= 0:
                return self.usb_drives[current_index]
        return None

    def list_usb_zip_files(self, usb_drive: USBDrive) -> list[str]:
        """List all wallet ZIP files on the USB (excluding *_temp.zip)."""
        try:
            if not usb_drive or not usb_drive.path:
                return []

            files = []
            for f in os.listdir(usb_drive.path):
                if f.endswith('.zip') and not f.endswith('_temp.zip'):
                    files.append(os.path.splitext(f)[0])

            return files
        except Exception as exc:
            logger.error('Error listing USB zip files: %s', exc)
            return []

    def showEvent(self, event):  # pylint:disable=invalid-name
        """Apply the blur effect to the parent widget when the dialog is shown."""
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(self.blur_effect)
        super().showEvent(event)

    def closeEvent(self, event):  # pylint:disable=invalid-name
        """Remove the blur effect from the parent widget when the dialog is closed."""
        # Stop the USB check timer
        if hasattr(self, 'usb_check_timer'):
            self.usb_check_timer.stop()
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        super().closeEvent(event)

    def accept(self):
        """Handle the Continue button click, remove blur, and accept the dialog."""
        # Stop the USB check timer
        if hasattr(self, 'usb_check_timer'):
            self.usb_check_timer.stop()
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        super().accept()

    def reject(self):
        """Handle the Cancel button click, remove blur, and reject the dialog."""
        # Stop the USB check timer
        if hasattr(self, 'usb_check_timer'):
            self.usb_check_timer.stop()
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        super().reject()
