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

from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.helpers import load_stylesheet
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
        self.setWindowTitle(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'enter_watch_only_wallet_details',
            ),
        )
        self.setObjectName('watch_only_xpub_dialog')
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint,
        )
        self.setStyleSheet(load_stylesheet('views/qss/watch_only_dialog.qss'))
        self.setMinimumSize(600, 420)

        self.dialog_box_vertical_layout = QVBoxLayout(self)
        self.dialog_box_vertical_layout.setContentsMargins(28, 24, 28, 28)

        # Header
        self.header_label = QLabel()
        self.header_label.setObjectName('header_label')
        self.dialog_box_vertical_layout.addWidget(self.header_label)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName('info_label')
        self.dialog_box_vertical_layout.addWidget(self.info_label)

        # Input Frame (single frame for all fields)
        self.input_frame = QFrame(self)
        self.input_frame.setFrameShape(QFrame.StyledPanel)
        self.input_frame.setFrameShadow(QFrame.Raised)
        self.input_frame.setFixedHeight(200)
        self.input_layout = QVBoxLayout(self.input_frame)
        self.input_layout.setContentsMargins(10, 0, 12, -1)

        # Xpub Vanilla
        self.xpub_vanilla_label = QLabel()
        self.xpub_vanilla_input = QLineEdit()
        self.input_layout.addWidget(self.xpub_vanilla_label)
        self.input_layout.addWidget(self.xpub_vanilla_input)

        # Xpub Colored
        self.xpub_colored_label = QLabel()
        self.xpub_colored_input = QLineEdit()
        self.input_layout.addWidget(self.xpub_colored_label)
        self.input_layout.addWidget(self.xpub_colored_input)

        # Master Fingerprint
        self.fingerprint_label = QLabel()
        self.fingerprint_input = QLineEdit()
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
        self.dialog_box_vertical_layout.addWidget(self.check_box)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 15, 0, 0)
        self.cancel_btn = SecondaryButton()
        self.cancel_btn.setMinimumSize(QSize(120, 35))
        self.cancel_btn.setMaximumSize(QSize(200, 35))
        self.cancel_btn.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_btn)
        self.continue_btn = PrimaryButton()
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
        Enable or disable the continue button based on the checkbox state.
        """
        self.continue_btn.setEnabled(self.check_box.isChecked())

    def handle_submit(self):
        """
        Validate input fields and save xpubs and fingerprint if valid.
        """
        vanilla = self.xpub_vanilla_input.text().strip()
        colored = self.xpub_colored_input.text().strip()
        fingerprint = self.fingerprint_input.text().strip()
        # Basic validation
        if not vanilla or not colored or not fingerprint:
            self.error_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'all_fields_required',
                ),
            )
            self.error_label.setVisible(True)
            self.setMinimumSize(600, 450)
            return
        # if not vanilla.startswith('xpub') or not colored.startswith('xpub'):
        #     self.error_label.setText(
        #         QCoreApplication.translate(
        #             IRIS_WALLET_TRANSLATIONS_CONTEXT, 'xpubs_must_start_with_xpub',
        #         ),
        #     )
        #     self.error_label.setVisible(True)
        #     self.setMinimumSize(600, 450)
        #     return
        if len(fingerprint) != 8:
            self.error_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'fingerprint_should_be_8_chars',
                ),
            )
            self.error_label.setVisible(True)
            self.setMinimumSize(600, 450)
            return
        # Save to ini
        self.error_label.setVisible(False)
        self.setMinimumSize(600, 420)
        local_store.set_value(ACCOUNT_XPUB_VANILLA, vanilla)
        local_store.set_value(ACCOUNT_XPUB_COLORED, colored)
        local_store.set_value(MASTER_FINGERPRINT, fingerprint)
        self.accept()
