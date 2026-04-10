# pylint: disable=too-few-public-methods, too-many-instance-attributes
"""
Review frame component for multisig setup page.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QVBoxLayout

from accessible_constant import MULTISIG_COLORED_XPUB_COPY_BUTTON
from accessible_constant import MULTISIG_COSIGNER_STRING_COPY_BUTTON
from accessible_constant import MULTISIG_REVIEW_COSIGNER_STRING_INPUT
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


class DetailField:
    """Helper class to create labelled read-only fields with optional copy button."""

    @staticmethod
    def create(
        title: str, placeholder: str = '',
        show_copy_btn: bool = False,
        info_text: str | None = None,
        full_width: bool = False,
    ) -> tuple[QGridLayout, QLineEdit, QPushButton | None]:
        """Create a labelled read-only field with an optional copy button."""
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        copy_btn = None

        label_container, _ = DetailField._build_label_container(
            title, info_text,
        )
        grid.addWidget(label_container, 0, 0)

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        inp = QLineEdit()
        if show_copy_btn:
            inp.setObjectName('wallet_detail_input_with_copy')
        else:
            inp.setObjectName('wallet_detail_input')
        inp.setFixedHeight(40)
        if full_width:
            inp.setFixedWidth(694 if not show_copy_btn else 654)
        else:
            inp.setFixedWidth(336)
        inp.setPlaceholderText(placeholder)
        inp.setReadOnly(True)
        h.addWidget(inp)

        if show_copy_btn:
            copy_btn = DetailField._create_copy_button()
            h.addWidget(copy_btn)

        h.addStretch()

        grid.addLayout(h, 1, 0)
        return grid, inp, copy_btn

    @staticmethod
    def _build_label_container(title: str, info_text: str | None) -> tuple[QFrame, QLabel]:
        """Build the label container with optional info button."""
        label_container = QFrame()
        lbl_layout = QHBoxLayout(label_container)
        lbl_layout.setContentsMargins(0, 0, 0, 0)
        lbl_layout.setSpacing(8)

        lbl = QLabel(title[:-1] if title.endswith(':') else title)
        lbl.setObjectName('ms_label')
        lbl_layout.addWidget(lbl)

        if info_text:
            info_btn = DetailField._create_info_button(info_text)
            lbl_layout.addWidget(info_btn)

        lbl_layout.addStretch()
        return label_container, lbl

    @staticmethod
    def _create_info_button(tooltip: str) -> QPushButton:
        """Create an info button with tooltip."""
        info_btn = QPushButton()
        info_btn.setObjectName('ms_info_button')
        info_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        info_btn.setFlat(True)
        info_btn.setIcon(QIcon(':/assets/info_circle.png'))
        info_btn.setIconSize(QSize(20, 20))
        info_btn.setFixedSize(QSize(20, 20))
        info_btn.setToolTip(tooltip)
        return info_btn

    @staticmethod
    def _create_copy_button() -> QPushButton:
        """Create a copy button."""
        copy_btn = QPushButton()
        copy_btn.setObjectName('copy_button')
        copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        copy_btn.setFlat(True)
        copy_btn.setIcon(QIcon(':/assets/copy.png'))
        copy_btn.setIconSize(QSize(20, 20))
        copy_btn.setFixedSize(QSize(40, 40))
        return copy_btn


class ReviewFrame(QFrame):
    """Frame for reviewing wallet info in multisig setup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('capabilities_frame')
        self.hide()
        self._setup_ui()

    def _setup_ui(self):
        """Build the review frame UI."""
        self.r_v = QVBoxLayout(self)
        self.r_v.setContentsMargins(34, 0, 34, 6)
        self.r_v.setSpacing(14)

        title_lbl = QLabel(
            'Review your wallet info and copy fields as needed.',
        )
        title_lbl.setObjectName('ms_label')
        title_lbl.setContentsMargins(0, 4, 0, 10)
        self.r_v.addWidget(title_lbl)

        # Row 1: Fingerprint and Keychain
        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(12)

        self.fp_display, self.fp_value_widget, _ = DetailField.create(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint',
            ), '',
        )
        self.keychain_display, self.keychain_value_widget, _ = DetailField.create(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keychain',
            ), '',
        )
        self.row1.addLayout(self.fp_display)
        self.row1.addLayout(self.keychain_display)
        self.r_v.addLayout(self.row1)

        # Row 2: Derivation path and Vanilla XPUB
        self.row2 = QHBoxLayout()
        self.row2.setContentsMargins(0, 0, 0, 0)
        self.row2.setSpacing(12)

        self.path_display, self.path_value_widget, _ = DetailField.create(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'derivation_path',
            ), '',
        )
        self.xpub_vanilla_display, self.xpub_vanilla_value_widget, _ = DetailField.create(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_vanilla',
            ), '',
            full_width=True,
        )
        self.row2.addLayout(self.xpub_vanilla_display)
        self.r_v.addLayout(self.row2)

        # Row 3: Colored XPUB
        self.row3 = QHBoxLayout()
        self.row3.setContentsMargins(0, 0, 0, 0)
        self.row3.setSpacing(12)

        self.xpub_colored_display, self.xpub_colored_value_widget, self.xpub_colored_copy_btn = DetailField.create(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_colored',
            ), '',
            show_copy_btn=True,
            info_text=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'colored_xpub_info_text',
                'Share this with the bridge operator to sync with the multisig bridge',
            ),
            full_width=True,
        )
        if self.xpub_colored_copy_btn:
            self.xpub_colored_copy_btn.setAccessibleName(
                MULTISIG_COLORED_XPUB_COPY_BUTTON,
            )
        self.row3.addLayout(self.xpub_colored_display)
        self.r_v.addLayout(self.row3)

        # Row 5: Cosigner string
        self.row5 = QHBoxLayout()
        self.row5.setContentsMargins(0, 0, 0, 0)
        self.row5.setSpacing(12)

        self.cosigner_string_display, self.cosigner_string_value_widget, self.cosigner_string_copy_btn = DetailField.create(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'signer_details',
            ), '',
            show_copy_btn=True,
            info_text=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'signer_details_explanation',
            ),
            full_width=True,
        )
        if self.cosigner_string_value_widget:
            self.cosigner_string_value_widget.setAccessibleName(
                MULTISIG_REVIEW_COSIGNER_STRING_INPUT,
            )
        if self.cosigner_string_copy_btn:
            self.cosigner_string_copy_btn.setAccessibleName(
                MULTISIG_COSIGNER_STRING_COPY_BUTTON,
            )
        self.row5.addLayout(self.cosigner_string_display)
        self.r_v.addLayout(self.row5)
        self.r_v.addStretch()

    def clear_fields(self):
        """Clear all field values."""
        self.fp_value_widget.clear()
        self.keychain_value_widget.clear()
        self.path_value_widget.clear()
        self.xpub_vanilla_value_widget.clear()
        self.xpub_colored_value_widget.clear()
        self.cosigner_string_value_widget.clear()

    def populate(self, data: dict):
        """Populate fields with wallet data."""
        self.fp_value_widget.setText(data.get('master_fingerprint', ''))
        self.keychain_value_widget.setText(data.get('keychain', ''))
        self.path_value_widget.setText(data.get('derivation_path', ''))
        self.xpub_vanilla_value_widget.setText(
            data.get('account_xpub_vanilla', ''),
        )
        self.xpub_colored_value_widget.setText(
            data.get('account_xpub_colored', ''),
        )
        self.cosigner_string_value_widget.setText(
            data.get('cosigner_string', ''),
        )
