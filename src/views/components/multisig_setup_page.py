from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QAbstractSpinBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
import re

from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton


class MultisigSetupPage(QWidget):
    """UI-only Multisig setup page (card), no business logic.

    Presents M-of-N threshold and placeholder cosigner fields.
    Color scheme matches wallet summary style.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(load_stylesheet('views/qss/multisig_setup_page.qss'))

        # Root grid
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)

        # Left spacer
        self.left_spacer = QSpacerItem(268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.grid.addItem(self.left_spacer, 1, 0)

        # Card container
        self.card = QWidget(self)
        self.card.setObjectName('ms_page_card')
        self.card.setMinimumSize(QSize(900, 520))
        self.card.setMaximumWidth(900)
        self.v = QVBoxLayout(self.card)
        self.v.setContentsMargins(0, 24, 24, 24)
        self.v.setSpacing(18)
        # Expose a SelectionPage-like attribute so breadcrumb bar can attach
        self.vertical_layout = self.v
        self.breadcrumb_widget = None

        # Prepare footer button early so validation can reference it safely
        self.continue_button = PrimaryButton()
        self.continue_button.setText('Continue')
        self.continue_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Title with left margin
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(35, 0, 0, 0)
        self.title = QLabel('Multisig Setup')
        self.title.setObjectName('ms_title')
        title_layout.addWidget(self.title)
        title_layout.addStretch()
        self.v.addLayout(title_layout)
        

        # Threshold card
        self.threshold_frame = QFrame(self.card)
        self.threshold_frame.setObjectName('capabilities_frame')
        self.t_v = QVBoxLayout(self.threshold_frame)
        self.t_v.setContentsMargins(35, 20, 20, 20)
        self.t_v.setSpacing(16)

        self.th_title = QLabel('Threshold (M-of-N)')
        self.th_title.setObjectName('ms_section_title')
        self.t_v.addWidget(self.th_title)

        # M and N controls on one line
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        
        req_lbl = QLabel('Required (M):')
        req_lbl.setObjectName('ms_label')
        controls_layout.addWidget(req_lbl)
        self.spin_m = QSpinBox()
        self.spin_m.setObjectName('ms_spin')
        self.spin_m.setRange(1, 15)
        self.spin_m.setValue(2)
        self.spin_m.setFixedWidth(100)
        controls_layout.addWidget(self.spin_m)
        
        controls_layout.addSpacing(30)
        
        tot_lbl = QLabel('Total signers (N):')
        tot_lbl.setObjectName('ms_label')
        controls_layout.addWidget(tot_lbl)
        self.spin_n = QSpinBox()
        self.spin_n.setObjectName('ms_spin')
        self.spin_n.setRange(2, 15)
        self.spin_n.setValue(2)
        self.spin_n.setFixedWidth(100)
        self.spin_n.setToolTip('Total number of cosigners')
        controls_layout.addWidget(self.spin_n)
        controls_layout.addStretch()
        self.t_v.addLayout(controls_layout)
        
        # Confirm button for threshold with padding
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 12, 0, 0)
        self.confirm_threshold_btn = PrimaryButton()
        self.confirm_threshold_btn.setText('Confirm Threshold')
        self.confirm_threshold_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.confirm_threshold_btn.clicked.connect(self._on_confirm_threshold)
        btn_layout.addWidget(self.confirm_threshold_btn, 0, Qt.AlignLeft)
        btn_layout.addStretch()
        self.t_v.addLayout(btn_layout)
        
        self.v.addWidget(self.threshold_frame)

        # Live summary under threshold with left margin
        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(35, 0, 0, 0)
        self.summary_lbl = QLabel('')
        self.summary_lbl.setObjectName('ms_helper')
        summary_layout.addWidget(self.summary_lbl)
        summary_layout.addStretch()
        self.v.addLayout(summary_layout)

        # Cosigners card (initially hidden)
        self.cos_frame = QFrame(self.card)
        self.cos_frame.setObjectName('capabilities_frame')
        self.cos_frame.hide()  # Hide until threshold confirmed
        self.c_v = QVBoxLayout(self.cos_frame)
        self.c_v.setContentsMargins(35, 20, 20, 20)
        self.c_v.setSpacing(12)


        # Scrollable area for cosigner rows
        scroll = QScrollArea()
        scroll.setObjectName('ms_scroll')
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

        # Divider before footer
        divider = QFrame(self.card)
        divider.setObjectName('ms_divider')
        divider.setFixedHeight(1)
        self.v.addWidget(divider)

        # Footer with Continue button
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(self.continue_button)
        self.v.addLayout(footer)

        # Center the card vertically with top/bottom spacers
        self.top_spacer = QSpacerItem(20, 60, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.bottom_spacer = QSpacerItem(20, 60, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_spacer = QSpacerItem(268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.grid.addItem(self.top_spacer, 0, 1)
        self.grid.addWidget(self.card, 1, 1)
        self.grid.addItem(self.bottom_spacer, 2, 1)
        self.grid.addItem(self.right_spacer, 1, 2)

        # Initial state
        self._threshold_locked = False
        self._update_summary()
        self._update_continue_enabled()

        # React to threshold changes
        self.spin_m.valueChanged.connect(self._update_summary)
        self.spin_n.valueChanged.connect(self._update_summary)

    def _on_confirm_threshold(self):
        """Lock threshold and create exact N cosigner fields."""
        n = self.spin_n.value()
        m = self.spin_m.value()
        if m > n or m < 1 or n < 2:
            return
        
        # Lock spinboxes
        self.spin_m.setEnabled(False)
        self.spin_n.setEnabled(False)
        self.confirm_threshold_btn.setEnabled(False)
        self._threshold_locked = True
        
        # Clear any existing rows
        for (row_w, _l, _le, _err) in self._cosigner_rows:
            self.cosigners_v.removeWidget(row_w)
            row_w.setParent(None)
            row_w.deleteLater()
        self._cosigner_rows.clear()
        
        # Create exactly N rows
        for i in range(n):
            self._add_cosigner_row(i + 1)
        
        # Show cosigner section
        self.cos_frame.show()
        self._update_summary()
        self._update_continue_enabled()

    def _add_cosigner_row(self, index: int):
        """Add a single cosigner row with the given index."""
        row_w = QWidget()
        row_v = QVBoxLayout(row_w)
        row_v.setContentsMargins(0, 0, 0, 0)
        row_v.setSpacing(8)

        header_h = QHBoxLayout()
        header_h.setContentsMargins(0, 0, 0, 0)
        header_h.setSpacing(8)

        label = QLabel(f'Cosigner {index} Extended xpub')
        label.setObjectName('ms_label')
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_h.addWidget(label)
        header_h.addStretch()

        paste_btn = QPushButton('Paste')
        paste_btn.setObjectName('ms_small_btn')
        paste_btn.setCursor(QCursor(Qt.PointingHandCursor))
        paste_btn.setFixedHeight(28)
        paste_btn.setToolTip('Paste from clipboard')
        header_h.addWidget(paste_btn)

        row_v.addLayout(header_h)

        xpub = QLineEdit()
        xpub.setPlaceholderText('[fingerprint/derivation_path]xpub')
        xpub.setObjectName('ms_input')
        xpub.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        xpub.setMinimumHeight(42)
        row_v.addWidget(xpub)
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
        # If threshold not locked, disable continue
        if not self._threshold_locked:
            self.continue_button.setEnabled(False)
            self.continue_button.setToolTip('Confirm threshold first')
            return
        
        n = self.spin_n.value()
        m = self.spin_m.value()
        n_rows = len(self._cosigner_rows)
        all_filled = True
        all_valid = True
        any_duplicates = False
        seen = set()
        for (_w, _l, le, err) in self._cosigner_rows:
            txt = le.text().strip()
            ok = self._is_valid_xpub(txt)
            all_filled &= (txt != '')
            all_valid &= ok
            dup = False
            if txt:
                if txt in seen:
                    any_duplicates = True
                    dup = True
                else:
                    seen.add(txt)
            if err:
                # Prefer duplicate message if applicable
                if (txt != '') and dup:
                    err.setText('Duplicate cosigner detected')
                    err.show()
                else:
                    err.setText('Please include [fingerprint/derivation_path] and xpub')
                    err.setVisible((txt != '') and not ok)
        
        enable = all_filled and all_valid and not any_duplicates and (n_rows == n)
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
        self.continue_button.setToolTip(reason)

    def _on_xpub_changed(self):
        self._update_continue_enabled()
        self._update_summary()

    def _paste_into(self, line_edit: QLineEdit):
        txt = QGuiApplication.clipboard().text() or ''
        line_edit.setText(txt.strip())

    def _is_valid_xpub(self, s: str) -> bool:
        if not s:
            return False
        # Very relaxed: must contain bracketed section and end token containing 'pub'
        has_brackets = '[' in s and ']' in s
        has_pub = bool(re.search(r"[a-zA-Z]pub", s))
        return has_brackets and has_pub

    def _update_summary(self):
        n = self.spin_n.value()
        m = self.spin_m.value()
        if self._threshold_locked:
            n_rows = len(self._cosigner_rows)
            filled = sum(1 for (_w, _l, le, _err) in self._cosigner_rows if le.text().strip())
            self.summary_lbl.setText(f"Summary: {m}-of-{n} multisig • {filled}/{n_rows} cosigner(s) filled")
        else:
            self.summary_lbl.setText(f"Preview: {m}-of-{n} multisig")

