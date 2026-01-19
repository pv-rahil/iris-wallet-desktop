# pylint: disable=too-many-instance-attributes, too-many-statements, too-few-public-methods
"""
Multisig setup page.
"""
from __future__ import annotations

import os
import re

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QScrollArea
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget
from rgb_lib import Cosigner
from rgb_lib import CosignerData

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import InitRequestModel
from src.model.enums.enums_model import WalletAccessType
from src.utils.build_app_path import app_paths
from src.utils.clickable_frame import ClickableFrame
from src.utils.common_utils import copy_text
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import MASTER_XPUB
from src.utils.constant import MNEMONIC_KEY
from src.utils.constant import VANILLA_KEYCHAIN
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.helpers import load_stylesheet
from src.utils.keyring_storage import get_value as keyring_get
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.page_navigation_events import PageNavigationEventManager
from src.utils.wallet_credential_encryption import mnemonic_store
from src.views.components.buttons import PrimaryButton
from src.views.components.wallet_logo_frame import WalletLogoFrame


class CosignerDetailCard(ClickableFrame):
    """Card widget for displaying/editing a single cosigner's details."""

    def __init__(self, index, parent=None, is_editable=True):
        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.index = index
        self.is_editable = is_editable

        # UI Elements
        self.fp_input = None
        self.keychain_input = None
        self.vanilla_xpub_input = None
        self.colored_xpub_input = None
        self.string_input = None
        self.import_btn = None
        self.content_widget = None
        # Connect click signal from ClickableFrame to toggle
        self.clicked.connect(
            lambda _id, _name, _path,
            _type: self.toggle_content(),
        )

        self.setObjectName('cosigner_card')
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Header Section ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Arrow Indicator (Visual only, state tracked by is_expanded)
        self.is_expanded = True
        self.arrow_lbl = QLabel('▼')
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
        layout.addLayout(header_layout)

        # --- Content Section (Collapsible) ---
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Row 1: Fingerprint | Keychain
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self.fp_field, self.fp_input = self._create_field(
            'master_fingerprint', 'e.g., a1b2c3d4',
        )
        self.keychain_field, self.keychain_input = self._create_field(
            'keychain', '0',
        )

        row1.addLayout(self.fp_field)
        row1.addLayout(self.keychain_field)
        content_layout.addLayout(row1)

        # Row 2: Vanilla XPUB
        self.vanilla_field, self.vanilla_xpub_input = self._create_field(
            'account_xpub_vanilla', 'xpub...',
        )
        content_layout.addLayout(self.vanilla_field)

        # Row 3: Colored XPUB
        self.colored_field, self.colored_xpub_input = self._create_field(
            'account_xpub_colored', 'xpub...',
        )
        content_layout.addLayout(self.colored_field)

        # Hidden String Input
        if self.is_editable:
            self.string_field, self.string_input = self._create_field(
                'Cosigner String', 'Paste cosigner string here', editable=True,
            )
            content_layout.addLayout(self.string_field)

        layout.addWidget(self.content_widget)

        # --- Footer Section (Import Button) ---
        if self.is_editable:
            footer_layout = QHBoxLayout()
            footer_layout.setContentsMargins(0, 0, 0, 0)
            footer_layout.addStretch()  # Push button to right

            self.import_btn = PrimaryButton()
            self.import_btn.setIcon(QIcon(':/assets/get_faucets.png'))
            self.import_btn.setLayoutDirection(Qt.RightToLeft)
            self.import_btn.setFixedSize(QSize(100, 36))
            self.import_btn.setCursor(
                QCursor(Qt.CursorShape.PointingHandCursor),
            )
            footer_layout.addWidget(self.import_btn)
            self.import_btn.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'import',
                ) + ' ',
            )

            content_layout.addLayout(footer_layout)

    def toggle_content(self):
        """Toggle visibility of the content widget."""
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.arrow_lbl.setText('▼' if self.is_expanded else '▶')

    def _create_field(self, title_key, placeholder, editable=False):
        """Helper to create a standard labeled input field with optional copy button."""
        title_text = title_key
        if '_' in title_key or title_key.islower():
            title_text = QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, title_key,
            )
            if not title_text:
                title_text = title_key

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(title_text)
        lbl.setObjectName('ms_label')
        layout.addWidget(lbl)

        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        inp = QLineEdit()
        inp.setObjectName('ms_input')
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(40)
        inp.setFrame(False)  # Important for specific styling

        if not editable:
            inp.setReadOnly(True)
            inp.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

        input_layout.addWidget(inp)

        if not editable:
            # Add Copy Button
            copy_btn = QPushButton()
            copy_btn.setObjectName('copy_button')
            copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            copy_btn.setFixedSize(QSize(50, 40))
            ic = QIcon()
            ic.addFile(':/assets/copy.png', QSize(), QIcon.Normal, QIcon.Off)
            copy_btn.setIcon(ic)
            copy_btn.clicked.connect(lambda: copy_text(inp))
            input_layout.addWidget(copy_btn)
        layout.addWidget(input_container)
        return layout, inp

        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.toggle_btn.setText('▼' if self.is_expanded else '▶')

    def _create_field(self, title_key, placeholder, editable=False):
        """Helper to create a standard labeled input field."""
        # Check if title_key is a translation key or raw string
        # Simple heuristic or try/except, but for now assuming key if not capitalized
        title_text = title_key
        if '_' in title_key or title_key.islower():
            title_text = QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, title_key,
            )
        # Fallback if empty (meaning likely not a key in this contest)
            if not title_text:
                title_text = title_key

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(title_text)
        label.setObjectName('form_label')  # Consistent form label style
        layout.addWidget(label)

        input_container = QHBoxLayout()
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setSpacing(0)

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(40)
        inp.setReadOnly(not editable)
        if not editable:
            inp.setObjectName('ms_input')
            # Add Copy Button
            copy_btn = QPushButton()
            copy_btn.setObjectName('copy_button')
            copy_btn.setFixedSize(QSize(50, 40))
            copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            copy_btn.setIcon(QIcon(':/assets/copy.png'))
            copy_btn.clicked.connect(lambda: copy_text(inp))
            input_container.addWidget(inp)
            input_container.addWidget(copy_btn)
        else:
            inp.setObjectName('ms_input')
            input_container.addWidget(inp)

        layout.addLayout(input_container)

        return layout, inp


class MultisigSetupPage(QWidget):
    """UI-only Multisig setup page (card), no business logic.

    Presents M-of-N threshold and placeholder cosigner fields.
    Color scheme matches wallet summary style.
    """

    def __init__(self, view_model):
        super().__init__()
        self._view_model = view_model

        # Retrieve password from keyring (already set in Set Password page)
        network = SettingRepository.get_wallet_network()
        self._password = keyring_get(WALLET_PASSWORD_KEY, network.value)

        if not self._password:
            # This shouldn't happen in normal flow, but handle it
            logger.error('Multisig setup accessed without password set!')
            PageNavigationEventManager.get_instance().selection_page_signal.emit()
            return

        # Continue with UI setup
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/multisig_setup_page.qss',
            ),
        )
        # Initialize state early so any helper calls can safely reference it
        self._threshold_locked = False
        self._current_step = 1  # dynamic steps; 1: threshold, 2: review or cosigners

        # Root grid
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)

        # Wallet logo top
        self.logo = WalletLogoFrame(self)
        # Grid: place logo spanning center column
        self.grid.addWidget(self.logo, 0, 0, 1, 2)

        # Left spacer
        self.left_spacer = QSpacerItem(
            268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum,
        )
        self.grid.addItem(self.left_spacer, 1, 0)

        # Card container (larger on Step 1 for better spacing; grows/shrinks per step)
        self.card = QWidget(self)
        self.card.setObjectName('ms_page_card')
        self.card.setMinimumSize(QSize(770, 530))
        self.card.setMaximumSize(QSize(770, 530))
        self.v = QVBoxLayout(self.card)
        # No horizontal margins so header/footer lines touch both edges
        self.v.setContentsMargins(0, 12, 0, 20)
        self.v.setSpacing(10)
        # Expose a SelectionPage-like attribute so breadcrumb bar can attach
        self.vertical_layout = self.v
        self.breadcrumb_widget = None

        # Prepare footer button early so validation can reference it safely
        self.continue_button = PrimaryButton()
        self.continue_button.setFixedSize(QSize(100, 40))
        self.continue_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Title with left margin
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(30, 9, 30, 0)
        self.title = QLabel()
        self.title.setObjectName('ms_title')
        self.title.setMinimumSize(QSize(415, 63))
        self.title.setMaximumSize(QSize(415, 63))
        title_layout.addWidget(self.title)
        title_layout.addStretch()
        # Close button to return to breadcrumb/selection page
        self.close_btn = QPushButton()
        self.close_btn.setObjectName('close_button')
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setIcon(QIcon(':/assets/x_circle.png'))
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.clicked.connect(
            self._view_model.page_navigation.selection_page,
        )
        title_layout.addWidget(self.close_btn)
        self.v.addLayout(title_layout)
        # Close button is visible on Step 1 only (hide it on other steps)
        self.close_btn.show()
        self.above_line = QFrame(self.card)
        self.above_line.setObjectName('above_line_frame')

        self.above_line.setFrameShape(QFrame.HLine)
        self.above_line.setFrameShadow(QFrame.Sunken)
        self.v.addWidget(self.above_line)

        # Threshold card (Step 1)
        self.threshold_frame = QFrame(self.card)
        self.threshold_frame.setObjectName('capabilities_frame')
        self.t_v = QVBoxLayout(self.threshold_frame)
        self.t_v.setContentsMargins(34, 14, 34, 6)
        self.t_v.setSpacing(10)

        # Info box
        self.info_box = QFrame(self.threshold_frame)
        self.info_box.setObjectName('ms_info_box')
        self.info_box.setFixedWidth(700)
        info_h = QHBoxLayout(self.info_box)
        info_h.setContentsMargins(14, 10, 14, 10)
        info_h.setSpacing(12)
        info_badge = QLabel('i')
        info_badge.setObjectName('ms_info_badge')
        info_badge.setFixedSize(22, 22)
        info_badge.setAlignment(Qt.AlignCenter)
        info_h.addWidget(info_badge)
        info_v = QVBoxLayout()
        info_v.setContentsMargins(0, 0, 0, 0)
        info_v.setSpacing(4)
        self.info_title = QLabel()
        self.info_title.setObjectName('ms_label')
        self.info_sub = QLabel()
        self.info_sub.setObjectName('ms_helper')
        self.info_sub.setWordWrap(True)
        info_v.addWidget(self.info_title)
        info_v.addWidget(self.info_sub)
        info_h.addLayout(info_v)
        self.t_v.addWidget(self.info_box)

        # Total Cosigners block
        total_signer_block = QVBoxLayout()
        total_signer_block.setContentsMargins(0, 0, 0, 0)
        total_signer_block.setSpacing(10)
        self.tot_lbl = QLabel()
        self.tot_lbl.setObjectName('ms_label')
        total_signer_block.addWidget(self.tot_lbl)
        self.total_signer_input = QLineEdit()
        self.total_signer_input.setObjectName('ms_input')
        self.total_signer_input.setText('3')
        self.total_signer_input.setFixedWidth(700)
        self.total_signer_input.setFixedHeight(40)
        self.total_signer_input.setFrame(False)
        self.total_signer_input.setValidator(QIntValidator(2, 15, self))
        total_signer_block.addWidget(self.total_signer_input)
        self.total_signer_help = QLabel()
        self.total_signer_help.setObjectName('ms_helper')
        # Add a little top padding so it doesn't touch the input field
        total_signer_block.addWidget(self.total_signer_help)
        self.t_v.addLayout(total_signer_block)

        # Required Signatures block
        required_signer_block = QVBoxLayout()
        required_signer_block.setContentsMargins(0, 0, 0, 0)
        required_signer_block.setSpacing(10)
        self.req_lbl = QLabel()
        self.req_lbl.setObjectName('ms_label')
        required_signer_block.addWidget(self.req_lbl)
        self.required_signer_input = QLineEdit()
        self.required_signer_input.setObjectName('ms_input')
        self.required_signer_input.setText('3')
        self.required_signer_input.setFixedWidth(700)
        self.required_signer_input.setFixedHeight(40)
        self.required_signer_input.setFrame(False)
        self.required_signer_input.setValidator(QIntValidator(2, 15, self))
        required_signer_block.addWidget(self.required_signer_input)
        self.required_signer_help = QLabel()
        self.required_signer_help.setObjectName('ms_helper')
        required_signer_block.addWidget(self.required_signer_help)
        self.t_v.addLayout(required_signer_block)

        # Configuration summary box
        self.summary_box = QFrame(self.threshold_frame)
        self.summary_box.setFixedWidth(700)
        self.summary_box.setObjectName('ms_summary_box')
        sum_h = QHBoxLayout(self.summary_box)
        sum_h.setContentsMargins(14, 12, 14, 12)
        self.summary_text = QLabel()
        self.summary_text.setObjectName('ms_label')
        sum_h.addWidget(self.summary_text)
        sum_h.addStretch()
        self.t_v.addWidget(self.summary_box)

        self.v.addWidget(self.threshold_frame)

        # Review info card (Step 2 when not Watch-Only): Master FP, Keychain, Path, XPUB
        self.review_frame = QFrame(self.card)
        self.review_frame.setObjectName('capabilities_frame')
        self.review_frame.hide()
        self.r_v = QVBoxLayout(self.review_frame)
        self.r_v.setContentsMargins(34, 0, 34, 6)
        self.r_v.setSpacing(14)
        self.review_frame_title_label = QLabel()
        self.review_frame_title_label.setObjectName('ms_label')
        self.review_frame_title_label.setContentsMargins(0, 4, 0, 10)
        self.review_frame_title_label.setText(
            'Review your wallet info and copy fields as needed.',
        )
        self.r_v.addWidget(self.review_frame_title_label)
        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(12)
        self.row2 = QHBoxLayout()
        self.row2.setContentsMargins(0, 0, 0, 0)
        self.row2.setSpacing(12)

        self.fp_display, self.fp_value_widget = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint',
            ),
            '',
        )
        self.keychain_display, self.keychain_value_widget = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keychain',
            ),
            '',
        )
        self.row1.addLayout(self.fp_display)
        self.row1.addLayout(self.keychain_display)
        self.r_v.addLayout(self.row1)

        # Row 2: Account XPUB (vanilla)
        self.path_display, self.path_value_widget = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'derivation_path',
            ),
            '',
        )
        self.xpub_vanilla_display, self.xpub_vanilla_value_widget = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_vanilla',
            ),
            '',
        )
        self.row2.addLayout(self.xpub_vanilla_display)
        self.r_v.addLayout(self.row2)

        # Row 3: Account XPUB (colored)
        self.row3 = QHBoxLayout()
        self.row3.setContentsMargins(0, 0, 0, 0)
        self.row3.setSpacing(12)
        self.xpub_colored_display, self.xpub_colored_value_widget = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_colored',
            ),
            '',
        )
        self.row3.addLayout(self.xpub_colored_display)
        self.r_v.addLayout(self.row3)

        # Row 4: Master XPUB
        self.row4 = QHBoxLayout()
        self.row4.setContentsMargins(0, 0, 0, 0)
        self.row4.setSpacing(12)
        self.master_xpub_display, self.master_xpub_value_widget = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_xpub',
            ),
            '',
        )
        self.row4.addLayout(self.master_xpub_display)
        self.r_v.addLayout(self.row4)

        # Row 5: Cosigner string (new)
        self.row5 = QHBoxLayout()
        self.row5.setContentsMargins(0, 0, 0, 0)
        self.row5.setSpacing(12)
        self.cosigner_string_display, self.cosigner_string_value_widget = self._create_wallet_detail_field(
            'Cosigner String',
            '',
        )

        self.row5.addLayout(self.cosigner_string_display)
        self.r_v.addLayout(self.row5)

        self.r_v.addStretch()

        self.v.addWidget(self.review_frame)

        # Creator setup (legacy holder - kept for compatibility, hidden)
        self.creator = {
            'mode': None, 'xpub': '',
            'fingerprint': '', 'derivation': '',
        }
        self.creator_ready = False
        self.creator_frame = QFrame(self.card)
        self.creator_frame.setObjectName('capabilities_frame')
        self.creator_frame.hide()
        self.creator_v = QVBoxLayout(self.creator_frame)
        self.creator_v.setContentsMargins(35, 0, 20, 0)

        # Action row for selected mode
        self.creator_actions = QHBoxLayout()
        # Left gutter to align with labels
        self.creator_actions.setContentsMargins(35, 0, 0, 0)
        self.creator_actions.setSpacing(12)

        self.creator_v.addLayout(self.creator_actions)
        self.v.addWidget(self.creator_frame)

        # Cosigners card (Step 3; initially hidden)
        self.cos_frame = QFrame(self.card)
        self.cos_frame.setObjectName('capabilities_frame')
        self.cos_frame.hide()  # Hide until threshold confirmed
        # Keep hidden frame from expanding vertical space
        self.cos_frame.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Minimum,
        )
        self.c_v = QVBoxLayout(self.cos_frame)
        # Align with 700px content area and add generous paddings for Step 2
        self.c_v.setContentsMargins(34, 14, 34, 16)
        self.c_v.setSpacing(16)

        # Scrollable area for cosigner rows
        scroll = QScrollArea()
        scroll.setObjectName('ms_scroll')
        self.cos_scroll = scroll
        scroll.setStyleSheet(load_stylesheet('views/qss/scrollbar.qss'))
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setMinimumHeight(220)
        # Allow the scroll area to expand naturally with the layout
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setFrameShape(QFrame.NoFrame)
        # Start with no gutter; we'll toggle based on scrollbar visibility
        scroll.setViewportMargins(0, 0, 0, 0)

        # Build scroll content AFTER setting margins
        scroll_content = QWidget()
        self.cosigners_v = QVBoxLayout(scroll_content)
        # Start with no right margin; we'll toggle with scrollbar visibility
        self.cosigners_v.setContentsMargins(0, 0, 16, 0)
        # More space between cosigner rows
        self.cosigners_v.setSpacing(16)
        self.cosigners_v.addStretch()
        scroll.setWidget(scroll_content)
        self.c_v.addWidget(scroll)

        self.cosigner_rows = []
        self.v.addWidget(self.cos_frame)

        # Footer with Back and Next/Continue
        self.footer = QHBoxLayout()
        # Reduce top margin so button sits closer to content
        self.footer.setContentsMargins(0, 4, 35, 12)
        # Back button (hidden on step 1) — match PrimaryButton styling
        # Validation error label (shown to the left of buttons)
        self.validation_error = QLabel()
        self.validation_error.setObjectName('ms_error')
        self.validation_error.setWordWrap(True)
        self.validation_error.hide()
        self.export_button = PrimaryButton()
        self.export_button.setIcon(QIcon(':/assets/upload.png'))
        self.export_button.setLayoutDirection(Qt.RightToLeft)
        self.export_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_button.setFixedSize(QSize(100, 40))
        self.export_button.hide()
        self.export_button.clicked.connect(self._export_cosigner_to_file)
        self.footer.addSpacing(35)
        self.footer.addWidget(self.export_button)
        self.back_button = PrimaryButton()
        self.back_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_button.setFixedSize(QSize(100, 40))
        self.back_button.clicked.connect(self._go_back)
        # Place buttons on the right with Back to the left of Continue
        self.footer.addStretch()
        self.footer.addWidget(self.validation_error)
        self.footer.addSpacing(12)
        self.footer.addWidget(self.back_button)
        self.footer.addSpacing(12)
        # Continue functions as Next on step 1 and Continue on step 2
        self.continue_button.clicked.connect(self._go_next)
        self.footer.addWidget(self.continue_button)
        self.v.addLayout(self.footer)

        # Center the card vertically with top/bottom spacers (tighter)
        self.top_spacer = QSpacerItem(
            20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding,
        )
        self.bottom_spacer = QSpacerItem(
            20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding,
        )
        self.right_spacer = QSpacerItem(
            268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum,
        )
        self.grid.addItem(self.top_spacer, 0, 1)
        self.grid.addWidget(self.card, 1, 1)
        self.grid.addItem(self.bottom_spacer, 2, 1)
        self.grid.addItem(self.right_spacer, 1, 2)

        # Initial state
        self._threshold_locked = False
        self._current_step = 1
        self._is_watch_only = (
            SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
        )
        self._steps_total = 2 if self._is_watch_only else 3
        self.back_button.hide()
        self._update_summary()
        self._update_continue_enabled()
        self.retranslate_ui()

        # React to threshold changes
        self.required_signer_input.textChanged.connect(self._update_summary)
        self.total_signer_input.textChanged.connect(self._update_summary)
        # Also update validation state live on edits
        self.required_signer_input.textChanged.connect(
            self._update_continue_enabled,
        )
        self.total_signer_input.textChanged.connect(
            self._update_continue_enabled,
        )

        # Restore saved threshold if available
        saved_m, saved_n = SettingRepository.get_multisig_config()
        if saved_m and saved_n:
            self.required_signer_input.setText(str(saved_m))
            self.total_signer_input.setText(str(saved_n))

            # If threshold is locked (implied by workflow, though logic here is loose), we should perform confirmation logic
            # or minimally check if we have cosigner data to restore.
            # Ideally, if M/N are set, we might want to prompt user or just auto-lock if complete?
            # For now, let's just restore cosigner inputs if we have them.
            stored_cosigners = SettingRepository.get_cosigners()
            if stored_cosigners:
                self._restore_cosigner_inputs(stored_cosigners)

    def retranslate_ui(self):
        """Set or refresh all translatable UI strings."""
        # Title
        self.title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'multisig_setup_title',
            ),
        )
        self.back_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'back',
            ),
        )
        self.export_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'export',
            ) + ' ',
        )
        self.total_signer_help.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_cosigners_help',
            ),
        )
        self.req_lbl.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'required_signatures_label',
            ),
        )
        self.info_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'configure_signature_requirements',
            ),
        )
        self.info_sub.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'choose_number_of_signatures',
            ),
        )
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
            ),
        )
        self.tot_lbl.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_cosigners_label',
            ),
        )

    def _on_confirm_threshold(self):
        """Lock threshold and create exact N cosigner fields."""
        n = self._get_total_signer()
        m = self._get_required_signer()
        if m > n or m < 1 or n < 2:
            return

        # Lock threshold inputs
        self.required_signer_input.setEnabled(False)
        self.total_signer_input.setEnabled(False)
        self._threshold_locked = True

        SettingRepository.set_multisig_config(m, n)

        # Generate wallet keys for non-watch-only wallets
        if not self._is_watch_only:
            try:
                # Check if mnemonic file already exists (keys already generated)
                if os.path.exists(app_paths.mnemonic_file_path):
                    # Keys already generated, don't regenerate
                    print(
                        'Keys already exist - skipping generation to preserve mnemonic.',
                    )
                else:
                    # Fresh - generate keys
                    # Get the current network from SettingRepository
                    network = get_bitcoin_network_from_enum(
                        SettingRepository.get_wallet_network(),
                    )

                    # Generate keys
                    keys = CommonOperationRepository.init(
                        InitRequestModel(password='', network=network),
                    )

                    # Store the keys data in local_store
                    local_store.set_value(
                        MASTER_FINGERPRINT, keys.master_fingerprint,
                    )
                    local_store.set_value(MASTER_XPUB, keys.xpub)
                    local_store.set_value(
                        ACCOUNT_XPUB_VANILLA, keys.account_xpub_vanilla,
                    )
                    local_store.set_value(
                        ACCOUNT_XPUB_COLORED, keys.account_xpub_colored,
                    )

                    # Encrypt mnemonic IMMEDIATELY with password
                    encrypted = mnemonic_store.encrypt(
                        self._password, keys.mnemonic,
                    )

                    # Save to PERMANENT location
                    local_store.write_to_file(
                        file_name=MNEMONIC_KEY,
                        file_path=app_paths.mnemonic_file_path,
                        value=encrypted,
                    )

                    print('Fresh setup - encrypted and saved mnemonic.')
            except Exception as e:
                print(f"Error generating/loading wallet keys: {e}")

        # Clear existing cosigner rows
        # Remove widgets from layout
        for card in self.cosigner_rows:
            self.cosigners_v.removeWidget(card)
            card.deleteLater()
        self.cosigner_rows.clear()

        # Add rows for cosigners 2..N based on total_signer
        # We assume #1 is "Me" (handled elsewhere or implied? Current UI implies #1 is user, cosigners start at #2?)
        # Wait, the current logic starts index at 2.
        for i in range(2, n + 1):
            self._add_cosigner_row(i)

        self.validation_error.hide()
        self.continue_button.setEnabled(False)
        self._threshold_locked = True
        self.required_signer_input.setEnabled(False)
        self.total_signer_input.setEnabled(False)
        # Do NOT show cosigner section yet in the 3-step flow
        self.cos_frame.hide()
        self._update_summary()
        self._update_continue_enabled()

    def _go_next(self):
        if self._current_step == 1:
            self._on_confirm_threshold()
            self.threshold_frame.hide()
            self.creator_frame.hide()
            self.back_button.show()
            self.close_btn.hide()

            if self._is_watch_only:
                # Skip review; go directly to cosigners
                self.cos_frame.show()
                self._current_step = 2
                self.card.setMinimumSize(QSize(770, 640))
                self.card.setMaximumSize(QSize(770, 640))
                self._update_continue_enabled()
                self._adjust_cosigner_input_widths()
                self.continue_button.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
                    ),
                )
            else:
                # Show review page as Step 2 of 3
                self._populate_wallet_review_fields()  # Populate with actual data
                self.review_frame.show()
                self.cos_frame.hide()
                self._current_step = 2
                self.export_button.show()  # Show export button on review page
                self.card.setMinimumSize(QSize(770, 670))
                self.card.setMaximumSize(QSize(770, 670))
                self.continue_button.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
                    ),
                )
        elif self._current_step == 2:
            if self._is_watch_only:
                # In 2-step flow, save cosigners before finishing
                self._save_cosigners_data()
                self._view_model.page_navigation.welcome_page()
            else:
                # Move to cosigners (Step 3)
                self.review_frame.hide()
                self.cos_frame.show()
                self.export_button.hide()  # Hide export button on cosigner page
                self._current_step = 3
                total_singer = self._get_total_signer()
                if total_singer > 2:
                    self.card.setMinimumSize(QSize(770, 640))
                    self.card.setMaximumSize(QSize(770, 640))
                else:
                    self.card.setMinimumSize(QSize(770, 520))
                    self.card.setMaximumSize(QSize(770, 520))
                self.continue_button.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
                    ),
                )
        elif self._current_step == 3:
            # Save cosigner data before navigating away
            self._save_cosigners_data()
            self._view_model.page_navigation.welcome_page()

    def _populate_wallet_review_fields(self):
        """Populate wallet review fields with actual wallet data from local_store."""
        # Get wallet data from local_store
        master_fp = local_store.get_value(MASTER_FINGERPRINT) or ''
        master_xpub = local_store.get_value(MASTER_XPUB) or ''
        account_xpub_vanilla = local_store.get_value(
            ACCOUNT_XPUB_VANILLA,
        ) or ''
        account_xpub_colored = local_store.get_value(
            ACCOUNT_XPUB_COLORED,
        ) or ''

        # Use the standard multisig derivation path
        derivation_path = "m/48'/0'/0'/2'"

        # For keychain, default to 0
        keychain = local_store.get_value(VANILLA_KEYCHAIN)
        keychain_str = str(keychain) if keychain is not None else '0'

        # Update the QLineEdit widgets with truncated XPUBs
        self.fp_value_widget.setText(master_fp)
        self.keychain_value_widget.setText(keychain_str)
        self.path_value_widget.setText(derivation_path)
        self.xpub_vanilla_value_widget.setText(account_xpub_vanilla)
        self.xpub_vanilla_value_widget.setCursorPosition(0)
        self.xpub_colored_value_widget.setText(account_xpub_colored)
        self.xpub_colored_value_widget.setCursorPosition(0)
        self.master_xpub_value_widget.setText(master_xpub)
        self.master_xpub_value_widget.setCursorPosition(0)

        # Generate and display cosigner string
        try:
            # keychain is optional int, ensure it's None if not set (though we default to 0 above/in usage)
            keychain_val = int(keychain) if keychain is not None else 0

            data = CosignerData(
                master_fingerprint=master_fp,
                account_xpub_vanilla=account_xpub_vanilla,
                account_xpub_colored=account_xpub_colored,
                vanilla_keychain=keychain_val,
            )
            cosigner_str = Cosigner.from_data(data).cosigner_string()
            self.cosigner_string_value_widget.setText(cosigner_str)
            self.cosigner_string_value_widget.setCursorPosition(0)
        except Exception as e:
            logger.error('Failed to generate cosigner string: %s', e)
            self.cosigner_string_value_widget.setText(
                'Error generating string',
            )

    def _save_cosigners_data(self):
        """Collect and save all cosigner data from the UI."""
        cosigners_data = []

        for card in self.cosigner_rows:
            fp = card.fp_input.text().strip()
            vanilla_xpub = card.vanilla_xpub_input.text().strip()
            colored_xpub = card.colored_xpub_input.text().strip()
            keychain_text = card.keychain_input.text().strip()

            # Parse keychain as int if provided
            keychain = None
            if keychain_text and keychain_text.isdigit():
                keychain = int(keychain_text)

            cosigner_dict = {
                'index': card.index,
                MASTER_FINGERPRINT: fp,
                ACCOUNT_XPUB_VANILLA: vanilla_xpub,
                ACCOUNT_XPUB_COLORED: colored_xpub,
                VANILLA_KEYCHAIN: keychain,
            }
            cosigners_data.append(cosigner_dict)

        # Save to SettingRepository
        SettingRepository.set_cosigners(cosigners_data)

    def _go_back(self):
        if self._current_step == 2:
            # Back to step 1 from review/cosigners depending on mode
            self.required_signer_input.setEnabled(True)
            self.total_signer_input.setEnabled(True)
            self.cos_frame.hide()
            self.review_frame.hide()
            self.threshold_frame.show()
            self.creator_frame.hide()
            self.back_button.hide()
            self.export_button.hide()  # Hide export button on Step 1
            self._current_step = 1
            # Restore Step 1 card size
            self.card.setMinimumSize(QSize(770, 520))
            self.card.setMaximumSize(QSize(770, 520))
            self._update_summary()
            self._update_continue_enabled()
            self.close_btn.show()
            SettingRepository.set_multisig_config(None, None)
            self.continue_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
                ),
            )
        elif self._current_step == 3:
            # From cosigners back to review
            self.cos_frame.hide()
            self.review_frame.show()
            self.export_button.show()  # Show export button on review step
            self._current_step = 2
            self.card.setMinimumSize(QSize(770, 670))
            self.card.setMaximumSize(QSize(770, 670))

    def _get_required_signer(self) -> int:
        try:
            return int(self.required_signer_input.text())
        except Exception:
            return 0

    def _get_total_signer(self) -> int:
        try:
            return int(self.total_signer_input.text())
        except Exception:
            return 0

    def _add_cosigner_row(self, index: int):
        """Add a row for a cosigner details."""
        card = CosignerDetailCard(index, self, is_editable=True)

        # Connect Import Button
        if card.import_btn:
            card.import_btn.clicked.connect(
                lambda: self._import_cosigner_from_file(card.string_input),
            )

        # Connect String Input Parser
        if card.string_input:
            card.string_input.textChanged.connect(
                lambda text, c=card: self._on_cosigner_string_changed(text, c),
            )

        self.cosigner_rows.append(card)

        self.cosigners_v.insertWidget(self.cosigners_v.count() - 1, card)

        if index == 2 and card.string_input:
            card.string_input.setFocus()

    def _on_cosigner_string_changed(self, text, row_w):
        """Parse cosigner string and populate fields."""
        text = text.strip()
        if not text:
            # Clear fields? Or keep them? Let's clear to indicate invalid state if needed
            # But maybe user is just editing.
            return

        try:
            data = Cosigner(text).cosigner_data()
            row_w.fp_input.setText(data.master_fingerprint)
            row_w.vanilla_xpub_input.setText(data.account_xpub_vanilla)
            row_w.colored_xpub_input.setText(data.account_xpub_colored)

            val = data.vanilla_keychain
            row_w.keychain_input.setText(str(val) if val is not None else '0')

            # Check validation
            self._update_continue_enabled()
        except Exception:
            # Invalid string, ignore or show error
            pass

    def _restore_cosigner_inputs(self, cosigners_data: list[dict]):
        """
        Restore cosigner inputs from stored data.
        Assumes threshold is already locked (or we lock it here).
        """
        # Ensure we are in a state to accept cosigners
        if not self._threshold_locked:
            self._on_confirm_threshold()

        # Iterate through data and populate cards
        for data in cosigners_data:
            idx = data.get('index')
            if not idx:
                continue

            # Find row with this index
            target_card = None
            for card in self.cosigner_rows:
                if card.index == idx:
                    target_card = card
                    break

            if target_card:
                if MASTER_FINGERPRINT in data:
                    target_card.fp_input.setText(data[MASTER_FINGERPRINT])
                if VANILLA_KEYCHAIN in data:
                    val = data[VANILLA_KEYCHAIN]
                    target_card.keychain_input.setText(
                        str(val) if val is not None else '0',
                    )
                if ACCOUNT_XPUB_VANILLA in data:
                    target_card.vanilla_xpub_input.setText(
                        data[ACCOUNT_XPUB_VANILLA],
                    )
                if ACCOUNT_XPUB_COLORED in data:
                    target_card.colored_xpub_input.setText(
                        data[ACCOUNT_XPUB_COLORED],
                    )

        # Ensure N/M inputs are disabled
        self.required_signer_input.setEnabled(False)
        self.total_signer_input.setEnabled(False)
        # No manual width adjustment needed anymore!

    def _update_continue_enabled(self):
        """
        Enable continue button if M/N are valid
        """
        # Step 1: Enable Next if M/N are valid
        if self._current_step == 1:
            n = self._get_total_signer()
            m = self._get_required_signer()
            # Enforce 2 ≤ M ≤ N ≤ 15
            valid = (3 <= n <= 15) and (2 <= m <= n)
            self.continue_button.setEnabled(valid)
            # Update error label instead of tooltip
            if valid:
                self.validation_error.clear()
                self.validation_error.hide()
            else:
                self.validation_error.setText(
                    'Enter valid M and N (2 ≤ M ≤ N ≤ 15)',
                )
                self.validation_error.show()
            return

        # Step 2: Enable Continue only when all cosigner rows are valid (if on cosigner step)
        # Or review step (handled loosely)
        if self.cos_frame.isVisible():
            n = self._get_total_signer()
            n_rows = len(self.cosigner_rows)
            all_filled = True
            all_valid = True
            any_duplicates = False
            seen = set()

            # Iterate over Card components
            for card in self.cosigner_rows:
                txt = card.vanilla_xpub_input.text().strip()
                ok = self._is_valid_xpub(txt)
                all_filled &= (txt != '')
                all_valid &= ok
                if txt:
                    if txt in seen:
                        any_duplicates = True
                    else:
                        seen.add(txt)

            enable = all_filled and all_valid and not any_duplicates and (
                n_rows == n - 1
            )
            self.continue_button.setEnabled(enable)

            # Give quick reason if disabled
            reason = ''
            if not enable:
                if any_duplicates:
                    reason = 'Remove duplicate cosigner entries'
                elif not all_filled:
                    reason = 'Fill all cosigner xpubs'
                elif not all_valid:
                    reason = 'One or more xpubs look invalid'

            if reason:
                self.validation_error.setText(reason)
                self.validation_error.show()
            else:
                self.validation_error.clear()
                self.validation_error.hide()
        else:
            # Review step or other
            self.continue_button.setEnabled(True)

    def _on_xpub_changed(self):
        """
        Update continue button and summary on xpub change
        """
        self._update_continue_enabled()
        self._update_summary()

    def _is_valid_xpub(self, s: str) -> bool:
        """
        Check if xpub is valid
        """
        if not s:
            return False
        # Very relaxed: must contain bracketed section and end token containing 'pub'
        has_brackets = '[' in s and ']' in s
        has_pub = bool(re.search(r'[a-zA-Z]pub', s))
        return has_brackets and has_pub

    def _update_summary(self):
        """
        Update summary text and validators
        """
        n = self._get_total_signer()
        m = self._get_required_signer()
        # Keep N clamped to 2–15
        self.total_signer_input.setValidator(QIntValidator(3, 15, self))
        # Clamp M to 2–min(N,15)
        max_m = max(2, min(n, 15))
        self.required_signer_input.setValidator(QIntValidator(2, max_m, self))

        # Update helper text and summary as before
        self.required_signer_help.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'minimum_signatures_needed',
            ).format(max_m),
        )

        m_disp = m if m >= 1 else 0
        n_disp = n if n >= 1 else 0
        if self.summary_text is not None:
            self.summary_text.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'configuration_note',
                ).format(m_disp, n_disp),
            )

    def _create_wallet_detail_field(self, title: str, placeholder: str, editable: bool = False) -> tuple[QGridLayout, QLineEdit]:
        """
        Create a wallet detail field with copy button.
        Used primarily for the Review Frame widgets.
        """
        wallet_detail_grid_layout = QGridLayout()
        wallet_detail_grid_layout.setContentsMargins(0, 0, 0, 0)
        wallet_detail_grid_layout.setSpacing(10)
        wallet_detail_label = QLabel(title)
        wallet_detail_label.setObjectName('ms_label')
        wallet_detail_grid_layout.addWidget(wallet_detail_label, 0, 0)
        wallet_detail_horizontal_layout = QHBoxLayout()
        wallet_detail_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        wallet_detail_horizontal_layout.setSpacing(0)
        wallet_detail_input = QLineEdit()
        wallet_detail_input.setObjectName('wallet_detail_input')
        wallet_detail_input.setFixedHeight(40)
        wallet_detail_input.setReadOnly(not editable)
        wallet_detail_input.setFrame(False)
        wallet_detail_input.setClearButtonEnabled(False)
        wallet_detail_input.setPlaceholderText(placeholder)
        wallet_detail_horizontal_layout.addWidget(wallet_detail_input)
        if not editable:
            wallet_detail_input.setStyleSheet("""
                    padding-left: 10px;
                    font: 15px "Inter";
                    color: rgb(102, 108, 129);
                    background-color: rgb(36, 44, 70);
                    border: none;
                    border-radius: 4px;
                    border-top-right-radius: 0px;
                    border-bottom-right-radius: 0px;
                """)
            wallet_detail_input.setCursor(
                QCursor(Qt.CursorShape.ForbiddenCursor),
            )
            copy_btn = QPushButton()
            copy_btn.setObjectName('copy_button')
            copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            copy_btn.setMinimumSize(QSize(50, 0))
            copy_btn.setMaximumSize(QSize(50, 40))
            ic = QIcon()
            ic.addFile(':/assets/copy.png', QSize(), QIcon.Normal, QIcon.Off)
            copy_btn.setIcon(ic)
            copy_btn.clicked.connect(lambda: copy_text(wallet_detail_input))
            wallet_detail_horizontal_layout.addWidget(copy_btn)
        wallet_detail_grid_layout.addLayout(
            wallet_detail_horizontal_layout, 1, 0,
        )
        return wallet_detail_grid_layout, wallet_detail_input

    def _export_cosigner_to_file(self):
        """Export cosigner string to a text file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Cosigner Data',
            'cosigner.txt',
            'Text Files (*.txt);;All Files (*)',
        )

        if file_path:
            try:
                cosigner_string = self.cosigner_string_value_widget.text()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cosigner_string)
                QMessageBox.information(
                    self,
                    'Success',
                    'Cosigner data exported successfully!',
                )
            except Exception as e:
                logger.error('Failed to export cosigner data: %s', e)
                QMessageBox.critical(
                    self,
                    'Error',
                    f"Failed to export cosigner data: {str(e)}",
                )

    def _import_cosigner_from_file(self, target_input):
        """Import cosigner string from a text file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Import Cosigner Data',
            '',
            'Text Files (*.txt);;All Files (*)',
        )

        if file_path:
            try:
                with open(file_path, encoding='utf-8') as f:
                    cosigner_string = f.read().strip()

                # Set the text in the input field (which will trigger parsing)
                target_input.setText(cosigner_string)

                QMessageBox.information(
                    self,
                    'Success',
                    'Cosigner data imported successfully!',
                )
            except Exception as e:
                logger.error('Failed to import cosigner data: %s', e)
                QMessageBox.critical(
                    self,
                    'Error',
                    f"Failed to import cosigner data: {str(e)}",
                )
