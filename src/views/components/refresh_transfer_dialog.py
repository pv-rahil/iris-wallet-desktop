# pylint: disable=too-many-instance-attributes,too-many-statements,too-few-public-methods
"""
Dialog that shows refreshed transfer results in card-like clickable frames.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLayout
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QScrollArea
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout
from rgb_lib import RgbLibError

from src.model.rgb_model import RefreshFailureItem
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.error_mapping import ERROR_MAPPING
from src.utils.helpers import load_stylesheet


class RefreshTransferDialog(QDialog):
    """Dialog to present refreshed transfer results with a card-like behavior."""

    def __init__(self, parent=None, payload: list[RefreshFailureItem] | None = None):
        """Initialize the dialog with optional payload."""
        super().__init__(parent)
        self.setObjectName('refresh_transfer_dialog')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        # Make the window background transparent; we will draw rounded bg on a container
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(
            load_stylesheet('views/qss/refresh_transfer_dialog_style.qss'),
        )

        # Root layout holds the rounded container
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame(self)
        self.container.setObjectName('container_frame')
        self.root_layout.addWidget(self.container)

        # Layout skeleton inside the rounded container
        self.dialog_box_vertical_layout = QVBoxLayout(self.container)
        self.dialog_box_vertical_layout.setSpacing(6)
        self.dialog_box_vertical_layout.setContentsMargins(16, 14, 16, 14)
        self.dialog_box_horizontal_layout = QHBoxLayout()
        self.dialog_box_horizontal_layout.setContentsMargins(0, 14, 0, 0)

        # Title
        self.title_label = QLabel(self)
        self.title_label.setObjectName('title_label')
        self.title_label.setContentsMargins(5, 0, 0, 0)
        self.dialog_box_horizontal_layout.addWidget(
            self.title_label, alignment=Qt.AlignLeft,
        )

        self.close_btn = QPushButton(self)
        self.close_btn.setObjectName('close_btn')
        self.close_btn.setMinimumSize(QSize(24, 24))
        self.close_btn.setMaximumSize(QSize(24, 24))
        self.close_btn.setAutoFillBackground(False)
        close_icon = QIcon()
        close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(), QIcon.Normal, QIcon.Off,
        )
        self.close_btn.setIcon(close_icon)
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.setCheckable(False)
        self.close_btn.setChecked(False)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)

        self.dialog_box_horizontal_layout.addWidget(
            self.close_btn,
        )
        self.dialog_box_horizontal_layout.addStretch()
        self.dialog_box_vertical_layout.addLayout(
            self.dialog_box_horizontal_layout,
        )

        # Scroll area for cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName('scroll_area_1')
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self.scroll_area.setMinimumHeight(220)
        self.scroll_area.setStyleSheet(
            load_stylesheet('views/qss/scrollbar.qss'),
        )
        self.scroll_area_widget = QFrame()
        self.scroll_area_widget.setObjectName('scroll_area_widget_1')
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.cards_layout = QVBoxLayout(self.scroll_area_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)

        self.dialog_box_vertical_layout.addWidget(self.scroll_area)

        self.title_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'refresh_transfer_title', None,
            ),
        )
        if payload is not None:
            self.populate(payload)

    def populate(self, items: list[RefreshFailureItem]):
        """Populate the dialog with refreshed transfer results.

        items: list of entries with keys: asset_id, failure
        """
        # Clear existing
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

        # Add cards
        for entry in items:
            card = self._create_card(entry.asset_id, entry.failure)
            self.cards_layout.addWidget(card)

        # Add stretch at end
        self.cards_layout.addStretch(1)

        # Resize behavior based on number of cards
        if len(items) == 1:
            # Let the dialog shrink to content height for a single item
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll_area.setMinimumHeight(0)
            self.dialog_box_vertical_layout.setSizeConstraint(
                QLayout.SetFixedSize,
            )
            self.adjustSize()
            self.title_label.setFixedWidth(525)
        else:
            # Restore default behavior for multiple items
            self.dialog_box_vertical_layout.setSizeConstraint(
                QLayout.SetDefaultConstraint,
            )
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scroll_area.setMinimumHeight(220)
            self.setMaximumWidth(540)
            self.setMaximumHeight(100)
            self.title_label.setFixedWidth(510)

    def _create_card(self, asset_id: str, failure: RgbLibError | None) -> QFrame:
        """Create a card for a single failure entry."""
        frame = QFrame(self.scroll_area_widget)
        frame.setObjectName('transfer_frame')
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        # Expand to available width for consistent left/right alignment regardless of caller
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        grid = QGridLayout(frame)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        # Make caption narrow and value expand
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 0)

        # Asset ID (caption + value)
        asset_id_caption = QLabel(frame)
        asset_id_caption.setObjectName('asset_id_label')
        grid.addWidget(asset_id_caption, 0, 0, 1, 1, Qt.AlignLeft)

        # Asset ID row container (to match Reason row exactly)
        asset_id_row_container = QFrame(frame)
        asset_id_row_container.setObjectName('asset_id_row_container')
        # Fill the grid's content width so right edge matches frame content right
        asset_id_row_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )
        asset_id_hbox = QHBoxLayout(asset_id_row_container)
        asset_id_hbox.setContentsMargins(0, 0, 0, 0)
        asset_id_hbox.setSpacing(0)

        asset_id_value = QLabel(asset_id_row_container)
        asset_id_value.setObjectName('asset_id_value_label')
        asset_id_value.setWordWrap(False)
        asset_id_value.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )
        asset_id_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        asset_id_hbox.addWidget(asset_id_value, 1)

        grid.addWidget(asset_id_row_container, 0, 1, 1, 2)

        # Reason (caption + value)
        reason_caption = QLabel(frame)
        reason_caption.setObjectName('reason_label')
        grid.addWidget(reason_caption, 1, 0, 1, 1, Qt.AlignLeft)

        # Reason row container that spans columns 1-2 like the Asset ID row
        reason_value_container = QFrame(frame)
        reason_value_container.setObjectName('reason_value_container')
        # Same behavior as Asset ID row: fill width
        reason_value_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )
        reason_hbox = QHBoxLayout(reason_value_container)
        reason_hbox.setContentsMargins(0, 0, 0, 0)
        reason_hbox.setSpacing(0)

        reason_value = QLabel(reason_value_container)
        reason_value.setObjectName('failure_value_label')
        reason_value.setWordWrap(True)
        # Let reason text take remaining space; no fixed width
        reason_value.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )
        reason_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        reason_value.setContentsMargins(0, 0, 0, 0)
        reason_hbox.addWidget(reason_value)

        status_chip = QLabel(reason_value_container)
        status_chip.setObjectName('status_chip')
        status_chip.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'failure', None,
            ),
        )
        status_chip.setAlignment(Qt.AlignCenter)
        reason_hbox.addWidget(status_chip)

        reason_hbox.addStretch()

        grid.addWidget(reason_value_container, 1, 1, 1, 2)

        asset_id_caption.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'error_asset_id_invalid_tx', None,
            ),
        )
        asset_id_value.setText(asset_id)

        failure_message = ERROR_MAPPING.get(type(failure).__name__)
        reason_caption.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'reason', None,
            ),
        )
        reason_value.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, failure_message, None,
            ),
        )

        return frame

    def _clear_layout(self, layout):
        """Clear a layout and delete all its widgets."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
