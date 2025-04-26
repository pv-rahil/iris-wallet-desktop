# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import,implicit-str-concat
"""
Custom dialog box for backup when google auth token not found in specified location
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.views.components.on_close_progress_dialog import OnCloseDialogBox


class BackupConfigureDialog(QDialog):
    """Custom dialog box for backup when google auth token not found in specified location"""

    def __init__(self, page_navigate):
        super().__init__()
        self.setObjectName('custom_dialog')
        self._page_navigate = page_navigate
        # Hide the title bar and close button
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(301, 160)
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/backup_configure_dialog_style.qss',
            ),
        )
        self.configure_backup_widget_grid_layout = QGridLayout(self)
        self.configure_backup_widget_grid_layout.setObjectName('gridLayout')
        self.configure_backup_widget_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.mnemonic_frame = QFrame(self)
        self.mnemonic_frame.setObjectName('mnemonic_frame')
        self.mnemonic_frame.setMinimumSize(QSize(370, 155))
        self.mnemonic_frame.setMaximumSize(QSize(16777215, 155))
        self.mnemonic_frame.setFrameShape(QFrame.StyledPanel)
        self.mnemonic_frame.setFrameShadow(QFrame.Raised)
        self.vertical_layout_frame = QVBoxLayout(self.mnemonic_frame)
        self.vertical_layout_frame.setSpacing(40)
        self.vertical_layout_frame.setObjectName('vertical_layout_frame')
        self.vertical_layout_frame.setContentsMargins(21, -1, 25, -1)
        self.mnemonic_detail_text_label = QLabel(self.mnemonic_frame)
        self.mnemonic_detail_text_label.setObjectName(
            'mnemonic_detail_text_label',
        )
        self.mnemonic_detail_text_label.setMinimumSize(QSize(332, 84))
        self.mnemonic_detail_text_label.setMaximumSize(QSize(332, 84))
        self.mnemonic_detail_text_label.setWordWrap(True)

        self.vertical_layout_frame.addWidget(self.mnemonic_detail_text_label)

        self.horizontal_button_layout_backup = QHBoxLayout()
        self.horizontal_button_layout_backup.setSpacing(20)
        self.horizontal_button_layout_backup.setContentsMargins(25, 1, 1, 1)
        self.horizontal_button_layout_backup.setObjectName(
            'horizontal_button_layout',
        )
        self.cancel_button = QPushButton(self.mnemonic_frame)
        self.cancel_button.setObjectName('cancel_button')
        self.cancel_button.setMinimumSize(QSize(74, 38))
        self.cancel_button.setMaximumSize(QSize(74, 38))
        self.horizontal_button_layout_backup.addWidget(self.cancel_button)

        self.continue_button = QPushButton(self.mnemonic_frame)
        self.continue_button.setObjectName('continue_button')
        self.continue_button.setMinimumSize(QSize(74, 38))

        self.horizontal_button_layout_backup.addWidget(self.continue_button)

        self.vertical_layout_frame.addLayout(
            self.horizontal_button_layout_backup,
        )

        self.vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.vertical_layout_frame.addItem(self.vertical_spacer)

        self.configure_backup_widget_grid_layout.addWidget(
            self.mnemonic_frame, 0, 0, 1, 1,
        )
        self.setup_ui_connection()
        self.retranslate_ui()

    # setupUi
    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.continue_button.clicked.connect(self.handle_configure)
        self.cancel_button.clicked.connect(self.handle_cancel)

    def retranslate_ui(self):
        """Retranslate ui"""
        self.mnemonic_detail_text_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'google_auth_not_found_message',
                None,
            ),
        )
        self.cancel_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ignore_button', None,
            ),
        )
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'configure_backup', None,
            ),
        )

    def handle_configure(self):
        """Re-direct the backup page for configuration"""
        self._page_navigate.backup_page()
        self.close()

    def handle_cancel(self):
        """Close when user ignore"""
        self.accept()
        self.close()
        progress_dialog = OnCloseDialogBox(self)
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.exec()
