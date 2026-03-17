# pylint: disable=too-many-instance-attributes,invalid-name
"""
Dialog for hardware wallet operation status (signing, broadcasting, success, error).
Styled using hardware_wallet_connect_style.qss.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QMovie
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout

from src.model.enums.enums_model import PsbtStatus
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.hardware_client_store import hardware_client_store
from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton
from src.views.components.hw_device_selection_dialog import HWDeviceSelectionDialog


class HardwareWalletOperationDialog(QDialog):
    """
    Modal dialog for hardware wallet operations (signing, broadcasting, success, error).
    Shows a loader, message, and optional success/error icon. Styled with hardware_wallet_connect_style.qss.
    """

    _instance = None

    def __init__(self, message: str = '', dialog_type: Enum | None = None, parent=None):
        """
        Initialize the hardware wallet operation dialog.

        Args:
            message: The message to display in the dialog.
            dialog_type: The type of operation (signing, broadcasting, success, error).
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.parent_widget = parent

        self.setObjectName('hardware_wallet_device_dialog')
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/hardware_wallet_connect_style.qss',
            ),
        )
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(10)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(32, 0, 32, 32)
        self.layout.addStretch(1)

        self.message_label = QLabel(self)
        self.message_label.setObjectName('message_label')
        self.message_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.message_label.setMinimumWidth(300)
        self.message_label.setMinimumHeight(100)
        self.message_label.setWordWrap(True)
        self.layout.addWidget(self.message_label, alignment=Qt.AlignHCenter)

        self.icon_label = QLabel(self)
        self.icon_label.setMinimumSize(QSize(100, 100))
        self.icon_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.icon_label.setObjectName('icon_label')
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignHCenter)

        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 12, 0, 0)
        self.button_layout.setSpacing(16)
        self.button_layout.setAlignment(Qt.AlignHCenter)
        self.cancel_button = SecondaryButton()
        self.cancel_button.setMinimumWidth(180)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)

        self.done_button = PrimaryButton()
        self.done_button.setVisible(False)
        self.done_button.setMinimumWidth(180)
        self.done_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.done_button)

        self.layout.addLayout(self.button_layout)
        self.layout.addStretch(1)

        self._loader_movie = None
        self._success_pixmap = QPixmap(':/assets/success.png')
        self._error_pixmap = QPixmap(':/assets/x_circle_red.png')
        if dialog_type is not None:
            self._set_dialog_state(message, dialog_type)
        self.retranslate_ui()

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.cancel_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel',
            ),
        )
        self.done_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'done',
            ),
        )

    def _set_dialog_state(self, message: str, dialog_type: Enum):
        """
        Set the dialog state (loading, success, error) based on the dialog type.

        Args:
            message: The message to display.
            dialog_type: The type of operation.
        """
        if dialog_type in (PsbtStatus.SIGNING, PsbtStatus.BROADCASTING):
            self.set_loading(message)
        elif dialog_type == PsbtStatus.ERROR:
            self.set_error(message)

    def set_loading(self, message: str):
        """
        Show loader animation and message. Shows Cancel, hides Done.

        Args:
            message: The message to display.
        """
        if self._loader_movie is None:
            self._loader_movie = QMovie(':/assets/images/button_loading.gif')
        if self._loader_movie is not None:
            self._loader_movie.setScaledSize(QSize(75, 75))
            self.icon_label.setMovie(self._loader_movie)
            self._loader_movie.start()
        self.message_label.setText(message)
        self.cancel_button.setVisible(True)
        self.done_button.setVisible(False)
        self.icon_label.setVisible(True)

    def set_error(self, message: str):
        """
        Show error icon and message. Shows Done, hides Cancel.

        Args:
            message: The error message to display.
        """
        if self._loader_movie is not None:
            self._loader_movie.stop()
        # Map specific hardware wallet error to user-friendly message
        hw_device = HWDeviceSelectionDialog(None)
        message = hw_device.map_hwi_error(message)
        self.icon_label.setPixmap(
            self._error_pixmap.scaled(
                75, 75, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ),
        )
        self.message_label.setText(message)
        self.cancel_button.setVisible(True)
        self.done_button.setVisible(False)
        self.icon_label.setVisible(True)

    def update_dialog(self, message: str, dialog_type: Enum):
        """
        Update the dialog's message and type.

        Args:
            message: The new message to display.
            dialog_type: The new dialog type.
        """
        self._set_dialog_state(message, dialog_type)

    def showEvent(self, event):
        """
        Apply blur effect to parent when dialog is shown.
        """
        if self.parent():
            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(10)
            self.parent().setGraphicsEffect(blur)
        super().showEvent(event)

    def accept(self):
        """
        Accept and close the dialog, remove blur.
        """
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        try:
            hardware_client_store.stop_client()
        except Exception:
            pass
        super().accept()

    def reject(self):
        """
        Reject and close the dialog, remove blur.
        """
        if self.parent_widget:
            self.parent_widget.setGraphicsEffect(None)
        try:
            hardware_client_store.stop_client()
        except Exception:
            pass
        super().reject()

    @classmethod
    def get_instance(cls, parent=None):
        """
        Get or create the singleton instance of the dialog.

        Args:
            parent: Optional parent widget.
        Returns:
            HardwareWalletOperationDialog: The singleton instance.
        """
        is_alive = False
        if cls._instance is not None:
            try:
                # Check if the underlying C++ object is still alive
                cls._instance.objectName()
                is_alive = True
            except RuntimeError:
                cls._instance = None

        if not is_alive:
            cls._instance = HardwareWalletOperationDialog(
                message='', dialog_type=None, parent=parent,
            )
        return cls._instance
