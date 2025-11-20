# pylint: disable=too-many-instance-attributes, too-many-statements, too-few-public-methods
"""
Multisig setup page.
"""
from __future__ import annotations

import re

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QScrollArea
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletAccessType
from src.utils.common_utils import copy_text
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton
from src.views.components.wallet_logo_frame import WalletLogoFrame


class MultisigSetupPage(QWidget):
    """UI-only Multisig setup page (card), no business logic.

    Presents M-of-N threshold and placeholder cosigner fields.
    Color scheme matches wallet summary style.
    """

    def __init__(self, view_model):
        super().__init__()
        self._view_model = view_model
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
        n_block = QVBoxLayout()
        n_block.setContentsMargins(0, 0, 0, 0)
        n_block.setSpacing(10)
        self.tot_lbl = QLabel()
        self.tot_lbl.setObjectName('ms_label')
        n_block.addWidget(self.tot_lbl)
        self.n_input = QLineEdit()
        self.n_input.setObjectName('ms_input')
        self.n_input.setText('2')
        self.n_input.setFixedWidth(700)
        self.n_input.setFixedHeight(40)
        self.n_input.setFrame(False)
        self.n_input.setValidator(QIntValidator(2, 15, self))
        n_block.addWidget(self.n_input)
        self.n_help = QLabel()
        self.n_help.setObjectName('ms_helper')
        # Add a little top padding so it doesn't touch the input field
        n_block.addWidget(self.n_help)
        self.t_v.addLayout(n_block)

        # Required Signatures block
        m_block = QVBoxLayout()
        m_block.setContentsMargins(0, 0, 0, 0)
        m_block.setSpacing(10)
        self.req_lbl = QLabel()
        self.req_lbl.setObjectName('ms_label')
        m_block.addWidget(self.req_lbl)
        self.m_input = QLineEdit()
        self.m_input.setObjectName('ms_input')
        self.m_input.setText('2')
        self.m_input.setFixedWidth(700)
        self.m_input.setFixedHeight(40)
        self.m_input.setFrame(False)
        self.m_input.setValidator(QIntValidator(2, 15, self))
        m_block.addWidget(self.m_input)
        self.m_help = QLabel()
        self.m_help.setObjectName('ms_helper')
        m_block.addWidget(self.m_help)
        self.t_v.addLayout(m_block)

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

        self.fp_display, _ = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint'),
            'f23a7c1d',
        )
        self.keychain_display, _ = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keychain'),
            'xpub keychain (demo)',
        )
        self.row1.addLayout(self.fp_display)
        self.row1.addLayout(self.keychain_display)
        self.r_v.addLayout(self.row1)

        # Row 2: Derivation path | Account XPUB (vanilla)
        self.path_display, _ = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'derivation_path'),
            'm/48\'/0\'/0\'/2\'',
        )
        self.xpub_vanilla_display, _ = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_vanilla'),
            'xpub6CUGRUonZS...',
        )
        self.row2.addLayout(self.path_display)
        self.row2.addLayout(self.xpub_vanilla_display)
        self.r_v.addLayout(self.row2)

        # Row 3: Account XPUB (colored)
        self.row3 = QHBoxLayout()
        self.row3.setContentsMargins(0, 0, 0, 0)
        self.row3.setSpacing(12)
        self.xpub_colored_display, _ = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_colored'),
            'xpub6CUGRUonZS...',
        )
        self.row3.addLayout(self.xpub_colored_display)
        self.r_v.addLayout(self.row3)
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
        self.cosigners_v.setContentsMargins(0, 0, 0, 0)
        # More space between cosigner rows
        self.cosigners_v.setSpacing(16)
        self.cosigners_v.addStretch()
        scroll.setWidget(scroll_content)
        self.c_v.addWidget(scroll)
        # React to scrollbar changes to adjust widths and right gutter
        scroll.verticalScrollBar().rangeChanged.connect(
            lambda _min, _max: self._adjust_cosigner_input_widths(),
        )
        scroll.verticalScrollBar().valueChanged.connect(
            lambda _v: self._adjust_cosigner_input_widths(),
        )

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
        self.m_input.textChanged.connect(self._update_summary)
        self.n_input.textChanged.connect(self._update_summary)
        # Also update validation state live on edits
        self.m_input.textChanged.connect(self._update_continue_enabled)
        self.n_input.textChanged.connect(self._update_continue_enabled)

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
        self.n_help.setText(
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
        n = self._get_n()
        m = self._get_m()
        if m > n or m < 1 or n < 2:
            return

        # Lock threshold inputs
        self.m_input.setEnabled(False)
        self.n_input.setEnabled(False)
        self._threshold_locked = True

        SettingRepository.set_multisig_config(m, n)

        # Clear any existing rows
        for (row_w, _l, _le, _err) in self.cosigner_rows:
            self.cosigners_v.removeWidget(row_w)
            row_w.setParent(None)
            row_w.deleteLater()
        self.cosigner_rows.clear()

        # Create rows starting from Cosigner 2 (Cosigner 1 shown previously)
        for i in range(2, n + 1):
            self._add_cosigner_row(i)
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
                self.review_frame.show()
                self.cos_frame.hide()
                self._current_step = 2
                self.card.setMinimumSize(QSize(770, 470))
                self.card.setMaximumSize(QSize(770, 470))
                self.continue_button.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
                    ),
                )
        elif self._current_step == 2:
            if self._is_watch_only:
                # In 2-step flow, continue finishes
                self._view_model.page_navigation.welcome_page()
            else:
                # Move to cosigners (Step 3)
                self.review_frame.hide()
                self.cos_frame.show()
                self._current_step = 3
                total_singer = self._get_n()
                if total_singer > 2:
                    self.card.setMinimumSize(QSize(770, 640))
                    self.card.setMaximumSize(QSize(770, 640))
                else:
                    self.card.setMinimumSize(QSize(770, 520))
                    self.card.setMaximumSize(QSize(770, 520))
                self._adjust_cosigner_input_widths()
                self.continue_button.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
                    ),
                )
        elif self._current_step == 3:
            self._view_model.page_navigation.welcome_page()

    def _go_back(self):
        if self._current_step == 2:
            # Back to step 1 from review/cosigners depending on mode
            self.m_input.setEnabled(True)
            self.n_input.setEnabled(True)
            self.cos_frame.hide()
            self.review_frame.hide()
            self.threshold_frame.show()
            self.creator_frame.hide()
            self.back_button.hide()
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
            self._current_step = 2
            self.card.setMinimumSize(QSize(770, 470))
            self.card.setMaximumSize(QSize(770, 470))

    def _get_m(self) -> int:
        try:
            return int(self.m_input.text())
        except Exception:
            return 0

    def _get_n(self) -> int:
        try:
            return int(self.n_input.text())
        except Exception:
            return 0

    def _add_cosigner_row(self, index: int):
        """Add a single cosigner row with the given index."""
        row_w = QWidget()
        row_v = QVBoxLayout(row_w)
        row_v.setContentsMargins(0, 10, 0, 14)
        row_v.setSpacing(12)

        # Header: Cosigner N
        header_h = QHBoxLayout()
        header_h.setContentsMargins(0, 0, 0, 0)
        header_h.setSpacing(8)
        cos_label = QLabel()
        cos_label.setObjectName('ms_label')
        header_h.addWidget(cos_label)
        header_h.addStretch()
        row_v.addLayout(header_h)

        # Fingerprint and Derivation Path in one row
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(12)
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(12)
        row3 = QHBoxLayout()
        row3.setContentsMargins(0, 0, 0, 0)
        row3.setSpacing(12)
        fp_field, fp_input = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint'),
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'fingerprint_example'),
            editable=True,
        )
        keychain_field, keychain_input = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keychain'),
            'xpub keychain (demo)',
            editable=True,
        )
        path_field, path_input = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'derivation_path'),
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'derivation_path_example'),
            editable=True,
        )
        xpub_vanilla_field, xpub_vanilla_input = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_vanilla'),
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'xpub_example'),
            editable=True,
        )
        xpub_colored_field, xpub_colored_input = self._create_wallet_detail_field(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_colored'),
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'xpub_example'),
            editable=True,
        )
        row1.addLayout(fp_field)
        row1.addLayout(keychain_field)
        row_v.addLayout(row1)

        row2.addLayout(path_field)
        row2.addLayout(xpub_vanilla_field)
        row_v.addLayout(row2)

        # Third row for colored xpub (full width)
        row3.addLayout(xpub_colored_field)
        row_v.addLayout(row3)

        xpub_vanilla_input.textChanged.connect(self._on_xpub_changed)
        xpub_vanilla_input.editingFinished.connect(
            lambda le=xpub_vanilla_input: le.setText(le.text().strip()),
        )
        xpub_colored_input.textChanged.connect(self._on_xpub_changed)
        xpub_colored_input.editingFinished.connect(
            lambda le=xpub_colored_input: le.setText(le.text().strip()),
        )

        # Insert before the stretch at the end
        self.cosigners_v.insertWidget(self.cosigners_v.count() - 1, row_w)
        # Store references on the row for later width adjustments
        row_w.fp_input = fp_input
        row_w.path_input = path_input
        row_w.vanilla_xpub_input = xpub_vanilla_input
        row_w.colored_xpub_input = xpub_colored_input
        row_w.keychain_input = keychain_input

        self.cosigner_rows.append((row_w, cos_label, xpub_vanilla_field, None))

        if index == 2:
            fp_input.setFocus()
        # Adjust widths after adding the row
        self._adjust_cosigner_input_widths()

        cos_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'cosigner_index',
            ).format(index),
        )

    def _adjust_cosigner_input_widths(self):
        """Toggle right gutter and input widths depending on scrollbar visibility."""
        try:
            if self.cos_scroll is None:
                return
            vsb = self.cos_scroll.verticalScrollBar()
            visible = vsb.isVisible() and (vsb.maximum() > 0)
            # Toggle viewport gutter and inner right margin
            if visible:
                self.cos_scroll.setViewportMargins(0, 0, 16, 0)
                if self.cosigners_v is not None:
                    self.cosigners_v.setContentsMargins(0, 0, 12, 0)
            else:
                self.cos_scroll.setViewportMargins(0, 0, 0, 0)
                if self.cosigners_v is not None:
                    self.cosigners_v.setContentsMargins(0, 0, 0, 0)
            # Adjust each row's widths
            for row_w, _label, _xpub, _err in self.cosigner_rows:
                fp = getattr(row_w, 'fp_input', None)
                path = getattr(row_w, 'path_input', None)
                vanilla_xpub = getattr(row_w, 'vanilla_xpub_input', None)
                colored_xpub = getattr(row_w, 'colored_xpub_input', None)
                keychain = getattr(row_w, 'keychain_input', None)
                if fp and path and vanilla_xpub and keychain:
                    if visible:
                        fp.setFixedWidth(330)
                        path.setFixedWidth(330)
                        vanilla_xpub.setFixedWidth(330)
                        colored_xpub.setFixedWidth(670)
                        keychain.setFixedWidth(330)
                    else:
                        fp.setFixedWidth(344)
                        path.setFixedWidth(344)
                        vanilla_xpub.setFixedWidth(344)
                        colored_xpub.setFixedWidth(700)
                        keychain.setFixedWidth(344)
        except Exception:
            pass

    def _update_continue_enabled(self):
        """
        Enable continue button if M/N are valid
        """
        # Step 1: Enable Next if M/N are valid
        # if self._current_step == 1:
        #     n = self._get_n()
        #     m = self._get_m()
        #     # Enforce 2 ≤ M ≤ N ≤ 15
        #     valid = (2 <= n <= 15) and (2 <= m <= n)
        #     self.continue_button.setEnabled(valid)
        #     # Update error label instead of tooltip
        #     if valid:
        #         self.validation_error.clear()
        #         self.validation_error.hide()
        #     else:
        #         self.validation_error.setText('Enter valid M and N (2 ≤ M ≤ N ≤ 15)')
        #         self.validation_error.show()
        #     return

        # # Step 2: Enable Continue only when all cosigner rows are valid
        # n = self._get_n()
        # n_rows = len(self.cosigner_rows)
        # all_filled = True
        # all_valid = True
        # any_duplicates = False
        # seen = set()
        # # Stored rows are tuples: (row_widget, cos_label, xpub_input)
        # for (_row_w, _cos_label, xpub_input) in self.cosigner_rows:
        #     txt = xpub_input.text().strip()
        #     ok = self._is_valid_xpub(txt)
        #     all_filled &= (txt != '')
        #     all_valid &= ok
        #     dup = False
        #     if txt:
        #         if txt in seen:
        #             any_duplicates = True
        #             dup = True
        #         else:
        #             seen.add(txt)

        # enable = all_filled and all_valid and not any_duplicates and (n_rows == n)
        # self.continue_button.setEnabled(enable)
        # # Give quick reason if disabled
        # reason = ''
        # if not enable:
        #     if any_duplicates:
        #         reason = 'Remove duplicate cosigner entries'
        #     elif not all_filled:
        #         reason = 'Fill all cosigner xpubs'
        #     elif not all_valid:
        #         reason = 'One or more xpubs look invalid'
        # # Show or hide the error label accordingly
        # if reason:
        #     self.validation_error.setText(reason)
        #     self.validation_error.show()
        # else:
        #     self.validation_error.clear()
        #     self.validation_error.hide()
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
        n = self._get_n()
        m = self._get_m()
        # Keep N clamped to 2–15
        self.n_input.setValidator(QIntValidator(2, 15, self))
        # Clamp M to 2–min(N,15)
        max_m = max(2, min(n, 15))
        self.m_input.setValidator(QIntValidator(2, max_m, self))

        # Update helper text and summary as before
        self.m_help.setText(
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
        """Create a wallet detail field with copy button."""
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
                QCursor(Qt.CursorShape.ForbiddenCursor))
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
            wallet_detail_horizontal_layout, 1, 0)
        return wallet_detail_grid_layout, wallet_detail_input
