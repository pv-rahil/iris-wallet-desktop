"""
Threshold frame component for multisig setup page.
"""
from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QVBoxLayout

from accessible_constant import MULTISIG_REQUIRED_SIGNER_INPUT
from accessible_constant import MULTISIG_TOTAL_SIGNER_INPUT
from src.model.broadcast_transaction_model import MultisigThresholdLabels


class ThresholdFrame(QFrame):
    """Frame for configuring threshold (M-of-N) for multisig wallet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.info_title: QLabel = None
        self.info_sub: QLabel = None
        self.tot_lbl: QLabel = None
        self.total_signer_input: QLineEdit = None
        self.total_signer_help: QLabel = None
        self.req_lbl: QLabel = None
        self.required_signer_input: QLineEdit = None
        self.required_signer_help: QLabel = None
        self.summary_text: QLabel = None

        self.setObjectName('capabilities_frame')

        t_v = QVBoxLayout(self)
        t_v.setContentsMargins(34, 14, 34, 6)
        t_v.setSpacing(10)

        # Info box
        info_box = self._build_info_box()
        t_v.addWidget(info_box)

        # Total signers
        tot_block = self._build_total_signers_block()
        t_v.addLayout(tot_block)

        # Required signers
        req_block = self._build_required_signers_block()
        t_v.addLayout(req_block)

        # Summary box
        summary_box = self._build_summary_box()
        t_v.addWidget(summary_box)

    def _build_info_box(self) -> QFrame:
        """Build the info box with title and subtitle."""
        info_box = QFrame(self)
        info_box.setObjectName('ms_info_box')
        info_box.setFixedWidth(700)
        info_h = QHBoxLayout(info_box)
        info_h.setContentsMargins(14, 10, 14, 10)
        info_h.setSpacing(12)

        info_badge = QPushButton()
        info_badge.setObjectName('ms_info_badge')
        info_badge.setIcon(QIcon(':/assets/info_blue.png'))
        info_badge.setFlat(True)
        info_badge.setIconSize(QSize(30, 30))
        info_badge.setFixedSize(30, 30)
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

        return info_box

    def _build_total_signers_block(self) -> QVBoxLayout:
        """Build the total signers input block."""
        tot_block = QVBoxLayout()
        tot_block.setContentsMargins(0, 0, 0, 0)
        tot_block.setSpacing(10)

        self.tot_lbl = QLabel()
        self.tot_lbl.setObjectName('ms_label')
        tot_block.addWidget(self.tot_lbl)

        self.total_signer_input = QLineEdit()
        self.total_signer_input.setObjectName('ms_input')
        self.total_signer_input.setText('2')
        self.total_signer_input.setFixedWidth(700)
        self.total_signer_input.setFixedHeight(40)
        self.total_signer_input.setFrame(False)
        self.total_signer_input.setValidator(QIntValidator(2, 15, self))
        self.total_signer_input.setAccessibleName(MULTISIG_TOTAL_SIGNER_INPUT)
        tot_block.addWidget(self.total_signer_input)

        self.total_signer_help = QLabel()
        self.total_signer_help.setObjectName('ms_helper')
        tot_block.addWidget(self.total_signer_help)

        return tot_block

    def _build_required_signers_block(self) -> QVBoxLayout:
        """Build the required signers input block."""
        req_block = QVBoxLayout()
        req_block.setContentsMargins(0, 0, 0, 0)
        req_block.setSpacing(10)

        self.req_lbl = QLabel()
        self.req_lbl.setObjectName('ms_label')
        req_block.addWidget(self.req_lbl)

        self.required_signer_input = QLineEdit()
        self.required_signer_input.setObjectName('ms_input')
        self.required_signer_input.setText('2')
        self.required_signer_input.setFixedWidth(700)
        self.required_signer_input.setFixedHeight(40)
        self.required_signer_input.setFrame(False)
        self.required_signer_input.setValidator(QIntValidator(2, 15, self))
        self.required_signer_input.setAccessibleName(
            MULTISIG_REQUIRED_SIGNER_INPUT,
        )
        req_block.addWidget(self.required_signer_input)

        self.required_signer_help = QLabel()
        self.required_signer_help.setObjectName('ms_helper')
        req_block.addWidget(self.required_signer_help)

        return req_block

    def _build_summary_box(self) -> QFrame:
        """Build the summary display box."""
        summary_box = QFrame(self)
        summary_box.setFixedWidth(700)
        summary_box.setObjectName('ms_summary_box')
        sum_h = QHBoxLayout(summary_box)
        sum_h.setContentsMargins(14, 12, 14, 12)

        self.summary_text = QLabel()
        self.summary_text.setObjectName('ms_label')
        sum_h.addWidget(self.summary_text)
        sum_h.addStretch()

        return summary_box

    def get_total_signer(self) -> int:
        """Get the total number of signers."""
        try:
            return int(self.total_signer_input.text())
        except ValueError:
            return 0

    def get_required_signer(self) -> int:
        """Get the required number of signers."""
        try:
            return int(self.required_signer_input.text())
        except ValueError:
            return 0

    def set_inputs_enabled(self, enabled: bool):
        """Enable or disable the input fields."""
        self.required_signer_input.setEnabled(enabled)
        self.total_signer_input.setEnabled(enabled)

    def retranslate_ui(self, labels: MultisigThresholdLabels):
        """Update all translatable strings.

        Args:
            labels: Model containing all label strings.
        """
        self.info_title.setText(labels.info_title)
        self.info_sub.setText(labels.info_sub)
        self.tot_lbl.setText(labels.tot_lbl)
        self.total_signer_help.setText(labels.tot_help)
        self.req_lbl.setText(labels.req_lbl)
        self.required_signer_help.setText(labels.req_help)
