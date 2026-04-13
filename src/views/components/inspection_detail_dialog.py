# pylint: disable=too-few-public-methods, too-many-locals
"""
Dialog for displaying detailed PSBT and RGB inspection information.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QScrollArea
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton


class InspectionDetailDialog(QDialog):
    """
    Detailed inspection dialog for BTC and RGB transactions.
    """

    def __init__(self, psbt_details, rgb_details=None, parent=None):
        super().__init__(parent)
        self.psbt_details = psbt_details
        self.rgb_details = rgb_details
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName('inspection_detail_dialog')
        self.setMinimumSize(QSize(800, 650))
        self.setMaximumHeight(750)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint,
        )
        self.setModal(True)
        self.setStyleSheet(
            load_stylesheet('views/qss/inspection_detail_dialog.qss'),
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header with Title
        header_frame = QFrame()
        header_frame.setObjectName('dialog_header')
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)

        title = QLabel(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'detailed_transaction_view', 'Detailed Transaction View',
            ),
        )
        title.setObjectName('dialog_title')
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        main_layout.addWidget(header_frame)

        # Scroll Area for Content
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_content.setObjectName('scroll_content')
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 5, 0)
        self.scroll_layout.setSpacing(12)

        # 1. Transaction Overview Card
        self._add_overview_card()

        # 2. Bitcoin Details Sections
        self._add_bitcoin_io_sections()

        # 3. RGB Asset Section (if available)
        if self.rgb_details is not None:
            self._add_rgb_section()

        self.scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)  # Give it stretch factor 1

        # Bottom Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        close_btn = PrimaryButton(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'close', 'Close',
            ), parent=self,
        )
        close_btn.setObjectName('close_btn')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch(1)
        main_layout.addLayout(btn_layout)

    def _add_overview_card(self):
        title = QLabel(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_summary', 'Transaction Summary',
            ),
        )
        title.setObjectName('section_title')
        self.scroll_layout.addWidget(title)

        card = QFrame()
        card.setObjectName('info_card')
        grid = QGridLayout(card)
        grid.setSpacing(12)

        self._add_grid_row(
            grid, 0, QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_id', 'Transaction Identification',
            ), self.psbt_details.txid,
        )
        self._add_grid_row(
            grid, 1, QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_input', 'Total Network Input',
            ), f"{self.psbt_details.total_input_sat:,} sats",
        )
        self._add_grid_row(
            grid, 2, QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_output', 'Total Network Output',
            ), f"{self.psbt_details.total_output_sat:,} sats",
        )
        if hasattr(self.psbt_details, 'fee_sat'):
            self._add_grid_row(
                grid, 3, QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'network_fee', 'Network Fee',
                ), f"{self.psbt_details.fee_sat:,} sats",
            )

        self.scroll_layout.addWidget(card)

    def _create_io_card(self, index: int, amount_sat: int, label_key: str, body_text: str) -> QFrame:
        """Create an input/output card."""
        card = QFrame()
        card.setObjectName('item_card')
        l = QVBoxLayout(card)
        l.setContentsMargins(16, 14, 16, 14)
        l.setSpacing(6)

        header_layout = QHBoxLayout()
        text_label = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, label_key,
        )
        header = QLabel(f"{text_label} #{index}")
        header.setObjectName('card_header')
        header_layout.addWidget(header)
        header_layout.addStretch()

        amount_lbl = QLabel(f"{amount_sat:,} sats")
        amount_lbl.setObjectName('value_text')
        header_layout.addWidget(amount_lbl)
        l.addLayout(header_layout)

        body = QLabel(body_text)
        body.setObjectName('card_body')
        body.setWordWrap(True)
        l.addWidget(body)
        return card

    def _add_bitcoin_io_sections(self):
        # Inputs
        if self.psbt_details.inputs:
            h_inputs = QLabel(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'inputs', 'Inputs',
                ),
            )
            h_inputs.setObjectName('section_title')
            self.scroll_layout.addWidget(h_inputs)

            for i, inp in enumerate(self.psbt_details.inputs):
                txid = self._extract_txid(inp)
                card = self._create_io_card(i, inp.amount_sat, 'input', txid)
                self.scroll_layout.addWidget(card)

        # Outputs
        if self.psbt_details.outputs:
            h_outputs = QLabel(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'outputs', 'Outputs',
                ),
            )
            h_outputs.setObjectName('section_title')
            self.scroll_layout.addWidget(h_outputs)

            for i, out in enumerate(self.psbt_details.outputs):
                if out.amount_sat == 0:
                    continue
                card = self._create_io_card(
                    i, out.amount_sat, 'output', out.address,
                )
                self.scroll_layout.addWidget(card)

    def _extract_txid(self, inp) -> str:
        """Extract clean TxID from input."""
        txid = str(inp.outpoint.txid) if hasattr(inp.outpoint, 'txid') else str(
            inp.outpoint,
        ).split(':', maxsplit=1)[0]

        if txid.startswith('Outpoint(txid='):
            txid = txid.replace('Outpoint(txid=', '').split(',')[0].strip()
        return txid

    def _create_rgb_io_card(self, index: int, label_key: str, assignment, is_concealed: bool = False) -> QFrame:
        """Create an RGB input/output card."""
        card = QFrame()
        card.setObjectName('item_card')
        l = QVBoxLayout(card)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(4)

        h = QHBoxLayout()
        hdr_text = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, label_key,
        )
        hdr = QLabel(f"{hdr_text} #{index}")
        hdr.setObjectName('card_header')
        h.addWidget(hdr)
        h.addStretch()

        val = str(assignment)
        if hasattr(assignment, 'is_FUNGIBLE') and assignment.is_FUNGIBLE():
            val = f"{assignment.amount:,}"
        elif hasattr(assignment, 'is_INFLATION_RIGHT') and assignment.is_INFLATION_RIGHT():
            val = f"{assignment.amount:,}"

        amt = QLabel(val)
        amt.setObjectName('value_text')
        h.addWidget(amt)
        l.addLayout(h)

        if is_concealed:
            meta = QLabel('??')
            meta.setObjectName('card_meta')
            l.addWidget(meta)

        return card

    def _add_rgb_section(self):
        title = QLabel(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_info',
            ),
        )
        title.setObjectName('section_title')
        self.scroll_layout.addWidget(title)

        transition_type_map = {
            'TYPEOFTRANSITION.INFLATE': 'Inflation',
            'TYPEOFTRANSITION.SEND': 'Asset Transfer',
            'TypeOfTransition.INFLATE': 'Inflation',
            'TypeOfTransition.SEND': 'Asset Transfer',
        }

        for _op_idx, op in enumerate(self.rgb_details.operations):
            for _t_idx, trans in enumerate(op.transitions):
                raw_type = str(trans.type)
                clean_type = transition_type_map.get(raw_type, raw_type)

                asset_label_text = QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_id_label', 'Asset id',
                )
                type_text = QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transition_type', 'Transition type',
                )

                title_container = QWidget()
                title_layout = QVBoxLayout(title_container)
                title_layout.setContentsMargins(0, 6, 0, 0)
                title_layout.setSpacing(2)

                # Asset id row
                asset_id_row = QHBoxLayout()
                asset_id_row.setSpacing(4)
                asset_id_label = QLabel()
                asset_id_label.setObjectName('label_text')
                asset_id_label.setText(asset_label_text)
                asset_id_row.addWidget(asset_id_label)

                asset_id_value = QLabel()
                asset_id_value.setObjectName('value_text')
                asset_id_value.setText(op.asset_id)
                asset_id_row.addWidget(asset_id_value)
                asset_id_row.addStretch()
                title_layout.addLayout(asset_id_row)

                # Transition type row
                type_row = QHBoxLayout()
                type_row.setSpacing(4)
                type_label = QLabel()
                type_label.setObjectName('label_text')
                type_label.setText(type_text)
                type_row.addWidget(type_label)

                type_value = QLabel()
                type_value.setObjectName('value_text')
                type_value.setText(clean_type)
                type_row.addWidget(type_value)
                type_row.addStretch()
                title_layout.addLayout(type_row)

                self.scroll_layout.addWidget(title_container)

                if trans.inputs:
                    for j, ri in enumerate(trans.inputs):
                        card = self._create_rgb_io_card(
                            j, 'input', ri.assignment,
                        )
                        self.scroll_layout.addWidget(card)

                if trans.outputs:
                    for j, ro in enumerate(trans.outputs):
                        card = self._create_rgb_io_card(
                            j, 'output', ro.assignment, is_concealed=ro.is_concealed,
                        )
                        self.scroll_layout.addWidget(card)

    def _add_grid_row(self, grid, row, label, value):
        lbl = QLabel(label)
        lbl.setObjectName('label_text')
        val = QLabel(str(value))
        val.setObjectName('value_text')
        val.setWordWrap(True)
        grid.addWidget(lbl, row, 0)
        grid.addWidget(val, row, 1)
