# pylint: disable=too-many-instance-attributes, too-many-statements
"""
Dialog for entering xpubs and fingerprint for Watch-Only wallet mode.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QVBoxLayout

from accessible_constant import WATCH_ONLY_CANCEL_BUTTON
from accessible_constant import WATCH_ONLY_CHECKBOX
from accessible_constant import WATCH_ONLY_CONTINUE_BUTTON
from accessible_constant import WATCH_ONLY_DIALOG
from accessible_constant import WATCH_ONLY_MASTER_FINGERPRINT
from accessible_constant import WATCH_ONLY_XPUB_COLORED
from accessible_constant import WATCH_ONLY_XPUB_VANILLA
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.helpers import load_stylesheet
from src.utils.helpers import validate_xpub
from src.utils.local_store import local_store
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton


class WatchOnlyDialog(QDialog):
    """
    Dialog for entering xpubs and fingerprint for Watch-Only wallet mode.
    """

    def __init__(self, parent=None):
        """
        Initialize the WatchOnlyDialog.
        """
        super().__init__(parent)
        self.setObjectName('watch_only_xpub_dialog')
        self.setModal(True)
        self.setAccessibleName(WATCH_ONLY_DIALOG)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint,
        )
        self.setStyleSheet(load_stylesheet('views/qss/watch_only_dialog.qss'))
        self.setMinimumSize(500, 420)

        self.dialog_box_vertical_layout = QVBoxLayout(self)
        self.dialog_box_vertical_layout.setContentsMargins(28, 24, 28, 28)

        # Header
        self.header_label = QLabel()
        self.header_label.setObjectName('header_label')
        self.dialog_box_vertical_layout.addWidget(self.header_label)

        self.info_label = QLabel()
        self.info_label.setMaximumWidth(460)
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName('info_label')
        self.dialog_box_vertical_layout.addWidget(self.info_label)

        # Input Frame (single frame for all fields)
        self.input_frame = QFrame(self)
        self.input_frame.setFrameShape(QFrame.StyledPanel)
        self.input_frame.setFrameShadow(QFrame.Raised)
        self.input_frame.setFixedHeight(250)
        self.input_layout = QVBoxLayout(self.input_frame)
        self.input_layout.setContentsMargins(10, 0, 12, -1)

        # Xpub Vanilla
        self.xpub_vanilla_label = QLabel()
        self.xpub_vanilla_label.setObjectName('xpub_vanilla_label')
        self.xpub_vanilla_input = QLineEdit()
        self.xpub_vanilla_input.setAccessibleName(WATCH_ONLY_XPUB_VANILLA)
        self.input_layout.addWidget(self.xpub_vanilla_label)
        self.input_layout.addWidget(self.xpub_vanilla_input)

        # Xpub Colored
        self.xpub_colored_label = QLabel()
        self.xpub_colored_label.setObjectName('xpub_colored_label')
        self.xpub_colored_input = QLineEdit()
        self.xpub_colored_input.setAccessibleName(WATCH_ONLY_XPUB_COLORED)
        self.input_layout.addWidget(self.xpub_colored_label)
        self.input_layout.addWidget(self.xpub_colored_input)

        # Master Fingerprint
        self.fingerprint_label = QLabel()
        self.fingerprint_label.setObjectName('fingerprint_label')
        self.fingerprint_input = QLineEdit()
        self.fingerprint_input.setAccessibleName(WATCH_ONLY_MASTER_FINGERPRINT)
        self.input_layout.addWidget(self.fingerprint_label)
        self.input_layout.addWidget(self.fingerprint_input)

        self.dialog_box_vertical_layout.addWidget(self.input_frame)

        # Error label
        self.error_label = QLabel()
        self.error_label.setObjectName('error_label')
        self.error_label.setVisible(False)
        self.dialog_box_vertical_layout.addWidget(self.error_label)

        # Checkbox
        self.check_box = QCheckBox()
        self.check_box.setCursor(QCursor(Qt.PointingHandCursor))
        self.check_box.setAccessibleName(WATCH_ONLY_CHECKBOX)
        self.dialog_box_vertical_layout.addWidget(self.check_box)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 15, 0, 0)
        self.cancel_btn = SecondaryButton()
        self.cancel_btn.setAccessibleName(WATCH_ONLY_CANCEL_BUTTON)
        self.cancel_btn.setMinimumSize(QSize(120, 35))
        self.cancel_btn.setMaximumSize(QSize(200, 35))
        self.cancel_btn.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_btn)
        self.continue_btn = PrimaryButton()
        self.continue_btn.setAccessibleName(WATCH_ONLY_CONTINUE_BUTTON)
        self.continue_btn.setMinimumSize(QSize(120, 35))
        self.continue_btn.setMaximumSize(QSize(200, 35))
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self.handle_submit)
        self.button_layout.addWidget(self.continue_btn)
        self.dialog_box_vertical_layout.addLayout(self.button_layout)

        self.check_box.stateChanged.connect(self.handle_continue_button)

        self.retranslate_ui()

    def retranslate_ui(self):
        """
        Set all translatable UI text for the dialog.
        """
        self.setWindowTitle(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'enter_watch_only_wallet_details',
            ),
        )
        self.header_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'watch_only_wallet_setup',
            ),
        )
        self.info_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'watch_only_wallet_info',
            ),
        )
        self.xpub_vanilla_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_vanilla',
            ),
        )
        self.xpub_vanilla_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'enter_account_xpub_vanilla',
            ),
        )
        self.xpub_colored_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_colored',
            ),
        )
        self.xpub_colored_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'enter_account_xpub_colored',
            ),
        )
        self.fingerprint_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint',
            ),
        )
        self.fingerprint_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'enter_master_fingerprint',
            ),
        )
        self.check_box.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'verify_watch_only_info',
            ),
        )
        self.cancel_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel',
            ),
        )
        self.continue_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
            ),
        )

    def handle_continue_button(self):
        """
        Enable or disable the continue button based on the checkbox state and input validation.
        """
        vanilla = self.xpub_vanilla_input.text().strip()
        colored = self.xpub_colored_input.text().strip()
        fingerprint = self.fingerprint_input.text().strip()

        def show_error(key: str):
            self.error_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, key,
                ),
            )
            self.error_label.setVisible(True)
            self.setMinimumSize(480, 490)
            self.continue_btn.setEnabled(False)
            self.check_box.setChecked(False)

        if not vanilla or not colored or not fingerprint:
            show_error('all_fields_required')
            return

        if not validate_xpub(vanilla) or not validate_xpub(colored):
            show_error('invalid_xpub')
            return

        if len(fingerprint) != 8 or not all(c in '0123456789abcdefABCDEF' for c in fingerprint):
            show_error('fingerprint_should_be_8_chars')
            return

        # All validations passed
        self.error_label.setVisible(False)
        self.setMinimumSize(480, 420)
        self.continue_btn.setEnabled(
            self.check_box.isChecked() and not self.error_label.isVisible(),
        )

    def handle_submit(self):
        """
        Validate input fields and save xpubs and fingerprint if valid.
        """
        vanilla = self.xpub_vanilla_input.text().strip()
        colored = self.xpub_colored_input.text().strip()
        fingerprint = self.fingerprint_input.text().strip()
        # Save to ini
        self.error_label.setVisible(False)
        self.setMinimumSize(480, 420)
        local_store.set_value(ACCOUNT_XPUB_VANILLA, vanilla)
        local_store.set_value(ACCOUNT_XPUB_COLORED, colored)
        local_store.set_value(MASTER_FINGERPRINT, fingerprint)
        self.accept()
