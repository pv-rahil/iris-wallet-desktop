from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCursor, QGuiApplication, QIntValidator, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
import re

from src.utils.helpers import load_stylesheet
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletAccessType, KeyStorageType
from src.views.components.buttons import PrimaryButton, SecondaryButton
from src.views.components.wallet_logo_frame import WalletLogoFrame


class MultisigSetupPage(QWidget):
    """UI-only Multisig setup page (card), no business logic.

    Presents M-of-N threshold and placeholder cosigner fields.
    Color scheme matches wallet summary style.
    """

    def __init__(self, view_model):
        super().__init__()
        self._view_model = view_model
        self.setStyleSheet(load_stylesheet('views/qss/multisig_setup_page.qss'))
        # Initialize state early so any helper calls can safely reference it
        self._threshold_locked = False
        self._current_step = 1  # 1: threshold, 2: cosigners

        # Root grid
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)

        # Wallet logo top
        self.logo = WalletLogoFrame(self)
        # Grid: place logo spanning center column
        self.grid.addWidget(self.logo, 0, 0,1,2)

        # Left spacer
        self.left_spacer = QSpacerItem(268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.grid.addItem(self.left_spacer, 1, 0)

        # Card container (smaller like Broadcast page; grows on step 2)
        self.card = QWidget(self)
        self.card.setObjectName('ms_page_card')
        self.card.setMinimumSize(QSize(595, 350))
        self.card.setMaximumSize(QSize(595, 350))
        self.v = QVBoxLayout(self.card)
        # No horizontal margins so header/footer lines touch both edges
        self.v.setContentsMargins(0, 16, 0, 20)
        self.v.setSpacing(12)
        # Expose a SelectionPage-like attribute so breadcrumb bar can attach
        self.vertical_layout = self.v
        self.breadcrumb_widget = None

        # Prepare footer button early so validation can reference it safely
        self.continue_button = PrimaryButton()
        self.continue_button.setText('Continue')
        self.continue_button.setFixedSize(QSize(100, 40))
        self.continue_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Title with left margin
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(30, 9, 30, 0)
        self.title = QLabel('Multisig Setup')
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
        self.close_btn.clicked.connect(self._handle_close)
        title_layout.addWidget(self.close_btn)
        self.v.addLayout(title_layout)
        # Close button is visible on Step 1 only (hide it on other steps)
        self.close_btn.show()
        self.above_line = QFrame(self.card)
        self.above_line.setObjectName('above_line_frame')

        self.above_line.setFrameShape(QFrame.HLine)
        self.above_line.setFrameShadow(QFrame.Sunken)
        self.v.addWidget(self.above_line)
        

        # Threshold card
        self.threshold_frame = QFrame(self.card)
        self.threshold_frame.setObjectName('capabilities_frame')
        self.t_v = QVBoxLayout(self.threshold_frame)
        self.t_v.setContentsMargins(35, 8, 20, 8)
        self.t_v.setSpacing(8)

        self.th_title = QLabel('Choose the number of signatures needed to unlock funds in your wallet:')
        # Smaller subtitle style to avoid competing with the page title
        self.th_title.setObjectName('ms_label')
        self.th_title.setWordWrap(True)
        self.th_title.setStyleSheet('font-size: 16px; font-weight: 500;')
        self.t_v.addWidget(self.th_title)

        mn_v = QHBoxLayout()
        mn_v.setContentsMargins(0, 0, 0, 0)
        mn_v.setSpacing(12)

        row_n = QHBoxLayout()
        row_n.setContentsMargins(0, 0, 0, 0)
        row_n.setSpacing(12)
        tot_lbl = QLabel('Total cosigners')
        tot_lbl.setObjectName('ms_label')
        row_n.addWidget(tot_lbl)
        self.n_input = QLineEdit()
        self.n_input.setObjectName('ms_input')
        self.n_input.setText('2')
        self.n_input.setFixedWidth(50)
        self.n_input.setMinimumHeight(36)
        self.n_input.setFrame(False)
        self.n_input.setToolTip('Total number of cosigners')
        row_n.addWidget(self.n_input)
        row_n.addStretch()
        mn_v.addLayout(row_n)

        row_m = QHBoxLayout()
        row_m.setContentsMargins(0, 0, 0, 0)
        row_m.setSpacing(12)
        req_lbl = QLabel('Required signatures')
        req_lbl.setObjectName('ms_label')
        row_m.addWidget(req_lbl)
        self.m_input = QLineEdit()
        self.m_input.setObjectName('ms_input')
        self.m_input.setText('2')
        self.m_input.setFixedWidth(50)
        self.m_input.setMinimumHeight(36)
        self.m_input.setFrame(False)
        row_m.addWidget(self.m_input)
        row_m.addStretch()
        mn_v.addLayout(row_m)
        mn_v.addStretch()

        self.t_v.addLayout(mn_v)
        
        
        self.v.addWidget(self.threshold_frame)


        # Creator setup (Step 2) — choose how to get the creator's keys
        self.creator = { 'mode': None, 'xpub': '', 'fingerprint': '', 'derivation': '' }
        self.creator_ready = False
        self.creator_frame = QFrame(self.card)
        self.creator_frame.setObjectName('capabilities_frame')
        self.creator_frame.hide()
        self.creator_v = QVBoxLayout(self.creator_frame)
        self.creator_v.setContentsMargins(35, 0, 20, 0)

        c_title = QLabel('Set up the wallet (first cosigner)')
        c_title.setMinimumSize(QSize(440, 40))
        c_title.setMaximumSize(QSize(440, 40))
        c_title.setObjectName('ms_label')
        self.creator_v.addWidget(c_title)

        # Action row for selected mode
        self.creator_actions = QHBoxLayout()
        # Left gutter to align with labels
        self.creator_actions.setContentsMargins(35, 0, 0, 0)
        self.creator_actions.setSpacing(12)

        self.seed_row_widget = QWidget()
        self.seed_row_widget.hide()
        self.seed_row = QHBoxLayout(self.seed_row_widget)
        self.seed_row.setContentsMargins(0, 0, 20, 0)
        self.seed_row.setSpacing(8)
        self.seed_input = QLineEdit()
        self.seed_input.setObjectName('ms_input')
        self.seed_input.setPlaceholderText('Enter 12 word seed phrase')
        self.seed_input.setMinimumHeight(36)
        self.seed_input.setFixedWidth(460)
        self.seed_row.addWidget(self.seed_input)
        self.seed_row.addStretch()
        self.seed_input.textChanged.connect(self._update_continue_enabled)
        self.note_row_widget = QWidget()
        self.note_row_widget.hide()
        self.note_row = QHBoxLayout(self.note_row_widget)
        self.note_row.setContentsMargins(0, 6, 20, 0)
        self.note_row.setSpacing(8)
        self.seed_note_lbl = QLabel('Already have a seed? Paste or type it above.')
        self.seed_note_lbl.setObjectName('ms_label')
        self.note_row.addWidget(self.seed_note_lbl)
        self.note_row.addStretch()

        # Generate button on its own row, left-aligned with content
        self.gen_row_widget = QWidget()
        self.gen_row_widget.hide()
        self.gen_row = QHBoxLayout(self.gen_row_widget)
        self.gen_row.setContentsMargins(0, 6, 20, 0)
        self.gen_row.setSpacing(8)
        self.btn_gen_seed = QPushButton()
        self.btn_gen_seed.setText('Generate new seed')
        self.btn_gen_seed.setObjectName('secondary_button')
        self.btn_gen_seed.setMinimumSize(QSize(200, 40))
        self.gen_row.addWidget(self.btn_gen_seed)
        self.gen_row.addStretch()

        # Default: do not skip creator unless explicitly watch-only
        self._skip_creator = False
        try:
            access_type = SettingRepository.get_wallet_access_type()
            storage_type = SettingRepository.get_key_storage_type()
            if access_type == WalletAccessType.WATCH_ONLY:
                initial_mode = 'device'  # default UI mode, but we'll skip the step
                self._skip_creator = True
            elif storage_type == KeyStorageType.HARDWARE_WALLET:
                initial_mode = 'hardware'
            else:
                initial_mode = 'device'
        except Exception:
            initial_mode = 'device'
        self._set_creator_mode(initial_mode)

        # Connect signals for actions
        self.btn_gen_seed.clicked.connect(lambda: self._mark_creator_ready('device', 'seed:new'))

        # Order: seed field, note row, generate row, then action row (used for hw/watch)
        self.creator_v.addWidget(self.seed_row_widget)
        self.creator_v.addWidget(self.note_row_widget)
        self.creator_v.addWidget(self.gen_row_widget)
        self.creator_v.addLayout(self.creator_actions)
        self.v.addWidget(self.creator_frame)


        # Cosigners card (Step 3; initially hidden)
        self.cos_frame = QFrame(self.card)
        self.cos_frame.setObjectName('capabilities_frame')
        self.cos_frame.hide()  # Hide until threshold confirmed
        self.c_v = QVBoxLayout(self.cos_frame)
        self.c_v.setContentsMargins(35, 20, 20, 20)
        self.c_v.setSpacing(12)


        # Scrollable area for cosigner rows
        scroll = QScrollArea()
        scroll.setObjectName('ms_scroll')
        scroll.setStyleSheet(load_stylesheet('views/qss/scrollbar.qss'))
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setMinimumHeight(220)
        # Allow the scroll area to expand naturally with the layout
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        self.cosigners_v = QVBoxLayout(scroll_content)
        self.cosigners_v.setContentsMargins(0, 0, 0, 0)
        self.cosigners_v.setSpacing(12)
        self.cosigners_v.addStretch()
        scroll.setWidget(scroll_content)
        self.c_v.addWidget(scroll)
        
        self._cosigner_rows = []  # track (row_widget, label_widget, line_edit, error_label)

        self.v.addWidget(self.cos_frame)

        # Footer with Back and Next/Continue
        self.footer = QHBoxLayout()
        self.footer.setContentsMargins(0, 20, 35, 10)
        # Back button (hidden on step 1) — match PrimaryButton styling
        self.back_button = PrimaryButton()
        self.back_button.setText('Back')
        self.back_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_button.setFixedSize(QSize(100, 40))
        self.back_button.clicked.connect(self._go_back)
        # Place buttons on the right with Back to the left of Continue
        self.footer.addStretch()
        self.footer.addWidget(self.back_button)
        self.footer.addSpacing(12)
        # Continue functions as Next on step 1 and Continue on step 2
        self.continue_button.setText('Next')
        self.continue_button.clicked.connect(self._go_next)
        self.footer.addWidget(self.continue_button)
        self.v.addLayout(self.footer)

        # Center the card vertically with top/bottom spacers (tighter)
        self.top_spacer = QSpacerItem(20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.bottom_spacer = QSpacerItem(20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_spacer = QSpacerItem(268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.grid.addItem(self.top_spacer, 0, 1)
        self.grid.addWidget(self.card, 1, 1)
        self.grid.addItem(self.bottom_spacer, 2, 1)
        self.grid.addItem(self.right_spacer, 1, 2)

        # Initial state
        self._threshold_locked = False
        self._current_step = 1  # 1: threshold, 2: cosigners
        self.back_button.hide()
        self._update_summary()
        self._update_continue_enabled()

        # React to threshold changes
        self.m_input.textChanged.connect(self._update_summary)
        self.n_input.textChanged.connect(self._update_summary)

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
        for (row_w, _l, _le, _err) in self._cosigner_rows:
            self.cosigners_v.removeWidget(row_w)
            row_w.setParent(None)
            row_w.deleteLater()
        self._cosigner_rows.clear()
        
        # Create exactly N rows
        for i in range(n):
            self._add_cosigner_row(i + 1)
        # Do NOT show cosigner section yet in the 3-step flow
        self.cos_frame.hide()
        self._update_summary()
        self._update_continue_enabled()

    def _go_next(self):
        if self._current_step == 1:
            self._on_confirm_threshold()
            # If hardware wallet mode, go directly to hardware connect page
            if self.creator.get('mode') == 'hardware':
                self.threshold_frame.hide()
                self.close_btn.hide()
                self._view_model.page_navigation.hardware_wallet_connect_page(True)
                self._current_step = 2
                return
            self.threshold_frame.hide()
            self.creator_frame.hide()
            self.cos_frame.show()
            self.back_button.show()
            self.continue_button.setText('Continue')
            self._current_step = 2
            # Grow card for cosigner input step
            self.card.setMinimumSize(QSize(530, 520))
            self.card.setMaximumSize(QSize(530, 520))
            self._update_continue_enabled()
            self.close_btn.hide()
        elif self._current_step == 2:
            self._view_model.page_navigation.welcome_page()

    def _go_back(self):
        if self._current_step == 2:
            # Return to step 1: unlock and show threshold
            self.m_input.setEnabled(True)
            self.n_input.setEnabled(True)
            self.cos_frame.hide()
            self.threshold_frame.show()
            self.creator_frame.hide()
            self.back_button.hide()
            self.continue_button.setText('Next')
            self._current_step = 1
            # Shrink card back for compact threshold step
            self.card.setMinimumSize(QSize(595, 350))
            self.card.setMaximumSize(QSize(595, 350))
            self._update_summary()
            self._update_continue_enabled()
            self.close_btn.show()
            SettingRepository.set_multisig_config(None, None)

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
        row_v.setContentsMargins(0, 0, 0, 0)
        row_v.setSpacing(8)

        header_h = QHBoxLayout()
        header_h.setContentsMargins(0, 0, 10, 0)
        header_h.setSpacing(8)

        label = QLabel(f'Cosigner {index} Extended xpub')
        label.setObjectName('ms_label')
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_h.addWidget(label)
        header_h.addStretch()

        paste_btn = QPushButton('Paste')
        paste_btn.setCursor(QCursor(Qt.PointingHandCursor))
        paste_btn.setFixedHeight(28)
        paste_btn.setToolTip('Paste from clipboard')
        # header_h.addWidget(paste_btn)

        row_v.addLayout(header_h)

        xpub = QLineEdit()
        xpub.setPlaceholderText('[fingerprint/derivation_path]xpub')
        xpub.setObjectName('ms_input')
        # Fix width and left-align so it doesn't stretch to full card width
        xpub.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        xpub.setFixedWidth(460)
        xpub.setMinimumHeight(42)
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(0)
        input_row.addWidget(xpub)
        input_row.addStretch()
        row_v.addLayout(input_row)
        xpub.textChanged.connect(self._on_xpub_changed)
        xpub.editingFinished.connect(lambda le=xpub: le.setText(le.text().strip()))

        # Error label
        err = QLabel('Please include [fingerprint/derivation_path] and xpub')
        err.setObjectName('ms_error')
        err.hide()
        row_v.addWidget(err)

        paste_btn.clicked.connect(lambda: self._paste_into(xpub))

        # Insert before the stretch at the end
        self.cosigners_v.insertWidget(self.cosigners_v.count() - 1, row_w)
        self._cosigner_rows.append((row_w, label, xpub, err))
        
        if index == 1:
            xpub.setFocus()


    def _update_continue_enabled(self):
        # # Step 1: Enable Next if M/N are valid
        # if self._current_step == 1:
        #     n = self._get_n()
        #     m = self._get_m()
        #     valid = (1 <= m <= n) and (n >= 2)
        #     self.continue_button.setEnabled(valid)
        #     self.continue_button.setToolTip('' if valid else 'Enter valid M and N (M ≤ N, N ≥ 2)')
        #     return

        # # Step 2: Enable Continue only when all cosigner rows are valid
        # n = self._get_n()
        # n_rows = len(self._cosigner_rows)
        # all_filled = True
        # all_valid = True
        # any_duplicates = False
        # seen = set()
        # for (_w, _l, le, err) in self._cosigner_rows:
        #     txt = le.text().strip()
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
        #     if err:
        #         # Prefer duplicate message if applicable
        #         if (txt != '') and dup:
        #             err.setText('Duplicate cosigner detected')
        #             err.show()
        #         else:
        #             err.setText('Please include [fingerprint/derivation_path] and xpub')
        #             err.setVisible((txt != '') and not ok)

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
        # self.continue_button.setToolTip(reason)
        self.continue_button.setEnabled(True)

    def _set_creator_mode(self, mode: str):
        # Clear actions and add relevant controls
        while self.creator_actions.count():
            item = self.creator_actions.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        if mode == 'device':
            self.creator['mode'] = 'device'
            # Show seed input and note; show generate button on its own row
            self.seed_row_widget.show()
            self.note_row_widget.show()
            self.gen_row_widget.show()
        elif mode == 'hardware':
            self.creator['mode'] = 'hardware'
            # Hide seed-based UI when hardware is used
            self.seed_row_widget.hide()
            self.note_row_widget.hide()
            self.gen_row_widget.hide()
        else:
            # watch-only path removed; default to device/hardware paths
            self.creator['mode'] = 'device'
            self.seed_row_widget.show()
            self.note_row_widget.show()
            self.gen_row_widget.show()
        # Mode changed resets ready state
        self.creator_ready = False
        self._update_continue_enabled()

    def _mark_creator_ready(self, mode: str, note: str):
        # For now, just mark ready and set placeholder xpub; integrate with real flows later
        self.creator['mode'] = mode
        self.creator['xpub'] = f'{note}'
        self.creator_ready = True
        self._update_continue_enabled()

    def _is_creator_ready(self) -> bool:
        if self.creator.get('mode') == 'device' and self.seed_row_widget.isVisible():
            # Ready if a seed is provided OR user chose to generate a new one
            return bool(self.seed_input.text().strip()) or self.creator_ready
        return self.creator_ready

    def _on_xpub_changed(self):
        self._update_continue_enabled()
        self._update_summary()

    def _paste_into(self, line_edit: QLineEdit):
        txt = QGuiApplication.clipboard().text() or ''
        line_edit.setText(txt.strip())

    def _handle_close(self):
        # Return to breadcrumb/selection page
        try:
            self._view_model.page_navigation.selection_page()
        except Exception:
            pass

    def _is_valid_xpub(self, s: str) -> bool:
        if not s:
            return False
        # Very relaxed: must contain bracketed section and end token containing 'pub'
        has_brackets = '[' in s and ']' in s
        has_pub = bool(re.search(r"[a-zA-Z]pub", s))
        return has_brackets and has_pub

    def _update_summary(self):
        n = self._get_n()
        m = self._get_m()
        if self._threshold_locked:
            n_rows = len(self._cosigner_rows)
            filled = sum(1 for (_w, _l, le, _err) in self._cosigner_rows if le.text().strip())
            # No summary label; keep logic for potential future use
            _ = (m, n, filled, n_rows)
        else:
            _ = (m, n)


