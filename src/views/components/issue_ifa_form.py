# pylint: disable=too-many-instance-attributes
"""
Issue IFA form component for IFA asset issuance page.
"""
from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from accessible_constant import IFA_ASSET_AMOUNT
from accessible_constant import IFA_ASSET_NAME
from accessible_constant import IFA_ASSET_TICKER
from accessible_constant import IFA_ASSET_TOTAL_SUPPLY
from src.utils.common_utils import set_number_validator


class IssueIFAForm(QWidget):
    """Form widget for IFA asset issuance with ticker, name, and supply fields."""

    def __init__(self, parent=None, default_fee_rate: int = 1):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._default_fee_rate = default_fee_rate
        self.inner_layout: QVBoxLayout = None
        self.footer_line: QFrame = None
        self.ticker_layout: QVBoxLayout = None
        self.ticker_label: QLabel = None
        self.ticker_input: QLineEdit = None
        self.name_layout: QVBoxLayout = None
        self.name_label: QLabel = None
        self.name_input: QLineEdit = None
        self.supply_layout: QVBoxLayout = None
        self.total_supply_title_widget: QWidget = None
        self.total_supply_title_layout: QHBoxLayout = None
        self.total_supply_label: QLabel = None
        self.total_supply_info_btn: QPushButton = None
        self.total_supply_input: QLineEdit = None
        self.issue_supply_label: QLabel = None
        self.issue_amount_input: QLineEdit = None
        self.error_label: QLabel = None
        self.fee_rate_label: QLabel = None
        self.fee_rate_input: QLineEdit = None

        self.setObjectName('issue_nia_widget')
        self.setMinimumSize(QSize(499, 608))
        self.setMaximumSize(QSize(466, 608))

        self.inner_layout = QVBoxLayout(self)
        self.inner_layout.setSpacing(6)
        self.inner_layout.setContentsMargins(1, 4, 1, 30)

        # Asset ticker field
        self._build_ticker_field()

        # Asset name field
        self._build_name_field()

        # Supply fields
        self._build_supply_fields()

        # Error label
        self._build_error_label()

        # Fee rate field
        self._build_fee_rate_field()

        # Spacer
        self.inner_layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding),
        )

        # Footer line
        self.footer_line = QFrame(self)
        self.footer_line.setObjectName('bottom_line_frame')
        self.footer_line.setFrameShape(QFrame.HLine)
        self.footer_line.setFrameShadow(QFrame.Sunken)
        self.inner_layout.addWidget(self.footer_line)

        # Button spacer
        self.inner_layout.addItem(
            QSpacerItem(20, 22, QSizePolicy.Preferred, QSizePolicy.Preferred),
        )

    def _build_ticker_field(self):
        """Build the asset ticker input field."""
        self.ticker_layout = QVBoxLayout()
        self.ticker_layout.setSpacing(0)
        self.ticker_layout.setContentsMargins(60, -1, 0, -1)

        self.ticker_label = QLabel(self)
        self.ticker_label.setObjectName('asset_ticker_label')
        self.ticker_label.setMinimumSize(QSize(0, 35))
        self.ticker_layout.addWidget(self.ticker_label)

        self.ticker_input = QLineEdit(self)
        self.ticker_input.setObjectName('issue_nia_input')
        self.ticker_input.setAccessibleName(IFA_ASSET_TICKER)
        self.ticker_input.setMinimumSize(QSize(0, 40))
        self.ticker_input.setMaximumSize(QSize(370, 40))
        self.ticker_input.setFrame(False)
        self.ticker_input.setClearButtonEnabled(False)
        self.ticker_layout.addWidget(self.ticker_input)

        self.inner_layout.addLayout(self.ticker_layout)

    def _build_name_field(self):
        """Build the asset name input field."""
        self.name_layout = QVBoxLayout()
        self.name_layout.setSpacing(0)
        self.name_layout.setContentsMargins(60, -1, 0, -1)

        self.name_label = QLabel(self)
        self.name_label.setObjectName('asset_name_label')
        self.name_label.setMinimumSize(QSize(0, 40))
        self.name_label.setMaximumSize(QSize(370, 40))
        self.name_layout.addWidget(self.name_label)

        self.name_input = QLineEdit(self)
        self.name_input.setObjectName('asset_name_input')
        self.name_input.setAccessibleName(IFA_ASSET_NAME)
        self.name_input.setMinimumSize(QSize(0, 40))
        self.name_input.setMaximumSize(QSize(370, 40))
        self.name_input.setFrame(False)
        self.name_input.setClearButtonEnabled(False)
        self.name_layout.addWidget(self.name_input)

        self.inner_layout.addLayout(self.name_layout)

    def _build_supply_fields(self):
        """Build the supply input fields."""
        self.supply_layout = QVBoxLayout()
        self.supply_layout.setSpacing(0)
        self.supply_layout.setContentsMargins(60, -1, 0, -1)

        # Total supply title with info button
        self.total_supply_title_widget = QWidget(self)
        self.total_supply_title_layout = QHBoxLayout(
            self.total_supply_title_widget,
        )
        self.total_supply_title_layout.setContentsMargins(0, 0, 0, 0)
        self.total_supply_title_layout.setSpacing(0)

        self.total_supply_label = QLabel(self)
        self.total_supply_label.setObjectName('total_supply_label')
        self.total_supply_label.setMinimumSize(QSize(0, 40))
        self.total_supply_label.setMaximumSize(QSize(100, 40))
        self.total_supply_title_layout.addWidget(self.total_supply_label)

        self.total_supply_info_btn = QPushButton(self)
        self.total_supply_info_btn.setObjectName('total_supply_info_btn')
        self.total_supply_info_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.total_supply_info_btn.setFlat(True)
        self.total_supply_info_btn.setIcon(QIcon(':/assets/info_circle.png'))
        self.total_supply_info_btn.setIconSize(QSize(50, 50))
        self.total_supply_info_btn.setFixedSize(QSize(50, 50))
        self.total_supply_title_layout.addWidget(self.total_supply_info_btn)

        self.supply_layout.addWidget(
            self.total_supply_title_widget, alignment=Qt.AlignLeft,
        )

        # Total supply input
        self.total_supply_input = QLineEdit(self)
        self.total_supply_input.setObjectName('amount_input')
        self.total_supply_input.setAccessibleName(IFA_ASSET_TOTAL_SUPPLY)
        self.total_supply_input.setMinimumSize(QSize(0, 40))
        self.total_supply_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.total_supply_input)
        self.total_supply_input.setFrame(False)
        self.total_supply_input.setClearButtonEnabled(False)
        self.supply_layout.addWidget(self.total_supply_input)

        # Issue supply label
        self.issue_supply_label = QLabel(self)
        self.issue_supply_label.setObjectName('total_supply_label')
        self.issue_supply_label.setMinimumSize(QSize(0, 40))
        self.issue_supply_label.setMaximumSize(QSize(370, 40))
        self.supply_layout.addWidget(self.issue_supply_label)

        # Issue amount input
        self.issue_amount_input = QLineEdit(self)
        self.issue_amount_input.setObjectName('amount_input')
        self.issue_amount_input.setAccessibleName(IFA_ASSET_AMOUNT)
        self.issue_amount_input.setMinimumSize(QSize(0, 40))
        self.issue_amount_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.issue_amount_input)
        self.issue_amount_input.setFrame(False)
        self.issue_amount_input.setClearButtonEnabled(False)
        self.supply_layout.addWidget(self.issue_amount_input)

        self.inner_layout.addLayout(self.supply_layout)

    def _build_error_label(self):
        """Build the error label."""
        self.error_label = QLabel(self)
        self.error_label.setObjectName('error_label')
        self.error_label.setMinimumSize(QSize(0, 40))
        self.error_label.setMaximumSize(QSize(370, 40))
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.error_label.setStyleSheet('color: #D32F2F;')
        self.error_label.hide()
        self.supply_layout.addWidget(self.error_label)

    def _build_fee_rate_field(self):
        """Build the fee rate input field."""
        self.fee_rate_label = QLabel(self)
        self.fee_rate_label.setObjectName('fee_rate_label')
        self.fee_rate_label.setMinimumSize(QSize(0, 40))
        self.fee_rate_label.setMaximumSize(QSize(370, 40))
        self.supply_layout.addWidget(self.fee_rate_label)

        self.fee_rate_input = QLineEdit(self)
        self.fee_rate_input.setObjectName('amount_input')
        self.fee_rate_input.setMinimumSize(QSize(0, 40))
        self.fee_rate_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.fee_rate_input)
        self.fee_rate_input.setFrame(False)
        self.fee_rate_input.setClearButtonEnabled(False)
        self.fee_rate_input.setText(str(self._default_fee_rate))
        self.fee_rate_input.setPlaceholderText(str(self._default_fee_rate))
        self.supply_layout.addWidget(self.fee_rate_input)

    def show_error(self, message: str):
        """Show an error message."""
        self.error_label.setText(message)
        self.error_label.show()

    def hide_error(self):
        """Hide the error message."""
        self.error_label.hide()

    def clear_error(self):
        """Clear the error message."""
        self.error_label.clear()
        self.error_label.hide()

    def configure_secondary_issuance(self, asset_name: str, asset_id: str):
        """Configure form for secondary issuance mode."""
        if asset_name:
            self.name_input.setText(asset_name)
        if asset_id:
            self.ticker_input.setText(asset_id)
            self.ticker_input.setCursorPosition(0)
            self.ticker_input.setReadOnly(True)

        # Hide total supply fields and lock name
        self.total_supply_title_widget.hide()
        self.total_supply_input.hide()
        self.name_input.setReadOnly(True)
        self.setFixedHeight(608)

    def configure_primary_issuance(self):
        """Configure form for primary issuance mode."""
        self.ticker_input.setText('')
        self.name_input.setText('')
        self.issue_amount_input.setText('')
        self.fee_rate_label.hide()
        self.fee_rate_input.hide()

    def get_ticker(self) -> str:
        """Get the ticker text."""
        return self.ticker_input.text().upper()

    def get_name(self) -> str:
        """Get the asset name text."""
        return self.name_input.text()

    def get_total_supply(self) -> str:
        """Get the total supply text."""
        return self.total_supply_input.text()

    def get_issue_amount(self) -> str:
        """Get the issue amount text."""
        return self.issue_amount_input.text()

    def get_fee_rate(self) -> str:
        """Get the fee rate text."""
        return self.fee_rate_input.text()
