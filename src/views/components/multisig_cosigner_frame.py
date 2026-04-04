"""
Cosigner frame component for multisig setup page.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QScrollArea
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.utils.helpers import load_stylesheet


class CosignerFrame(QFrame):
    """Frame for managing cosigner inputs in multisig setup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('capabilities_frame')
        self.hide()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.cosigner_rows: list = []
        self._setup_ui()

    def _setup_ui(self):
        """Build the cosigner frame UI."""
        c_v = QVBoxLayout(self)
        c_v.setContentsMargins(34, 14, 34, 16)
        c_v.setSpacing(16)

        scroll = QScrollArea()
        scroll.setObjectName('ms_scroll')
        self.scroll = scroll
        scroll.setStyleSheet(load_stylesheet('views/qss/scrollbar.qss'))
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setMinimumHeight(220)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setViewportMargins(0, 0, 0, 0)

        scroll_content = QWidget()
        self.cosigners_v = QVBoxLayout(scroll_content)
        self.cosigners_v.setContentsMargins(0, 0, 16, 0)
        self.cosigners_v.setSpacing(16)
        self.cosigners_v.addStretch()
        scroll.setWidget(scroll_content)
        c_v.addWidget(scroll)

    def add_cosigner_row(self, card: QWidget):
        """Add a cosigner card to the frame."""
        self.cosigner_rows.append(card)
        # Insert before the stretch
        self.cosigners_v.insertWidget(self.cosigners_v.count() - 1, card)

    def clear_cosigner_rows(self):
        """Clear all cosigner rows."""
        for card in self.cosigner_rows:
            card.deleteLater()
        self.cosigner_rows.clear()

    def get_cosigner_rows(self) -> list:
        """Get all cosigner row widgets."""
        return self.cosigner_rows
