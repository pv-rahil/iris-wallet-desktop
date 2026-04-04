# pylint: disable=too-many-instance-attributes, too-many-statements, too-few-public-methods
"""
Cosigner Detail Card component for multisig configuration.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from accessible_constant import MULTISIG_COSIGNER_CARD
from accessible_constant import MULTISIG_COSIGNER_IMPORT_BUTTON
from accessible_constant import MULTISIG_COSIGNER_RESET_BUTTON
from accessible_constant import MULTISIG_COSIGNER_STRING_INPUT
from src.utils.clickable_frame import ClickableFrame
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton


class CosignerDetailCard(ClickableFrame):
    """Card widget for displaying/editing a single cosigner's details."""

    def __init__(self, index, parent=None):
        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.index = index

        # UI Elements
        self.fp_input = None
        self.keychain_input = None
        self.vanilla_xpub_input = None
        self.colored_xpub_input = None
        self.string_input = None
        self.import_btn = None
        self.content_widget = None
        self._collapsible = None

        # Data storage for validation
        self.vanilla_xpub_str = None
        self.colored_xpub_str = None

        # Connect click signal from ClickableFrame to toggle
        self.clicked.connect(
            lambda _id, _name, _path,
            _type: self.toggle_content(),
        )

        self.setObjectName('cosigner_card')
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setAccessibleName(f'{MULTISIG_COSIGNER_CARD}_{index}')

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Header Section ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Arrow Indicator (Visual only, state tracked by is_expanded)
        self.is_expanded = False
        self.arrow_lbl = QLabel('▶')
        self.arrow_lbl.setStyleSheet(
            'font-weight: bold; font-size: 16px; color: #666C81;',
        )
        header_layout.addWidget(self.arrow_lbl)

        # Title: "Cosigner #N"
        title = QLabel(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cosigner_index',
            ).format(self.index),
        )
        title.setObjectName('h3_title')
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Import Button (Moved to Header)
        self.import_btn = PrimaryButton()
        self.import_btn.setIcon(QIcon(':/assets/import.png'))
        self.import_btn.setIconSize(QSize(18, 18))
        self.import_btn.setLayoutDirection(Qt.RightToLeft)
        self.import_btn.setFixedSize(QSize(100, 36))
        self.import_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.import_btn.setAccessibleName(
            f'{MULTISIG_COSIGNER_IMPORT_BUTTON}_{index}',
        )
        self.import_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'import',
            ) + ' ',
        )
        header_layout.addWidget(self.import_btn)

        # Reset Button (Hidden by default, shown when valid data is present)
        self.reset_btn = SecondaryButton()
        self.reset_btn.setIcon(QIcon(':/assets/x_cross.png'))
        self.reset_btn.setIconSize(QSize(18, 18))
        self.reset_btn.setLayoutDirection(Qt.RightToLeft)
        self.reset_btn.setFixedSize(QSize(100, 36))
        self.reset_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.reset_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'reset',
            ) + ' ',
        )
        self.reset_btn.setAccessibleName(
            f'{MULTISIG_COSIGNER_RESET_BUTTON}_{index}',
        )
        self.reset_btn.setVisible(False)
        header_layout.addWidget(self.reset_btn)

        layout.addLayout(header_layout)

        self.content_widget = QWidget()
        self.content_widget.setVisible(False)  # Collapsed by default
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Row 0: String Input
        self.string_field, self.string_input = self._create_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cosigner_details',
            ), 'Paste cosigner details here', editable=True,
        )
        self.string_input.setAccessibleName(
            f'{MULTISIG_COSIGNER_STRING_INPUT}_{index}',
        )
        content_layout.addLayout(self.string_field)

        # Row 1: Fingerprint | Keychain
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self.fp_field, self.fp_input = self._create_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint',
            ), 'e.g., a1b2c3d4',
        )
        self.keychain_field, self.keychain_input = self._create_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keychain',
            ), '0',
        )

        row1.addLayout(self.fp_field)
        row1.addLayout(self.keychain_field)
        content_layout.addLayout(row1)

        # Row 2: Vanilla XPUB
        self.vanilla_field, self.vanilla_xpub_input = self._create_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_vanilla',
            ), 'xpub...',
        )
        content_layout.addLayout(self.vanilla_field)

        # Row 3: Colored XPUB
        self.colored_field, self.colored_xpub_input = self._create_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_colored',
            ), 'xpub...',
        )
        content_layout.addLayout(self.colored_field)

        layout.addWidget(self.content_widget)

        # Error Label (Moved to bottom)
        self.error_label = QLabel()
        self.error_label.setObjectName('ms_error')
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

    def show_error(self, message):
        """Show error message on the card."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def clear_error(self):
        """Clear error message from the card."""
        self.error_label.clear()
        self.error_label.setVisible(False)

    def set_collapsible(self, collapsible: bool):
        """Enable or disable collapsibility."""
        self._collapsible = collapsible
        if not collapsible:
            self.arrow_lbl.hide()
            self.setCursor(QCursor(Qt.ArrowCursor))
            if not self.is_expanded:
                self.is_expanded = True
                self.content_widget.setVisible(True)
        else:
            self.arrow_lbl.show()
            self.setCursor(QCursor(Qt.PointingHandCursor))

    def toggle_content(self):
        """Toggle visibility of the content widget."""
        if hasattr(self, '_collapsible') and not self._collapsible:
            return

        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.arrow_lbl.setText('▼' if self.is_expanded else '▶')

    def _create_field(self, title_key, placeholder, editable=False):
        """Helper to create a standard labeled input field with optional copy button."""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel()
        label.setObjectName('form_label')  # Consistent form label style
        label.setText(title_key[:-1] if title_key.endswith(':') else title_key)
        layout.addWidget(label)

        input_container = QHBoxLayout()
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setSpacing(0)

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(40)
        inp.setCursorPosition(0)
        inp.setReadOnly(not editable)
        inp.setObjectName('ms_input')
        if not editable:
            inp.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))
        input_container.addWidget(inp)

        layout.addLayout(input_container)

        return layout, inp
