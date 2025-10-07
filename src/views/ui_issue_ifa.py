# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the IssueIFAWidget class,
 which represents the UI for issuing IFA assets.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import QTranslator
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

import src.resources_rc
from accessible_constant import ISSUE_NIA_ASSET_CLOSE_BUTTON
from accessible_constant import ISSUE_NIA_BUTTON
from accessible_constant import NIA_ASSET_AMOUNT
from accessible_constant import NIA_ASSET_NAME
from accessible_constant import NIA_ASSET_TICKER
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import ReceiveAssetModel
from src.model.rgb_model import RgbAssetPageLoadModel
from src.model.success_model import SuccessPageModel
from src.utils.common_utils import enforce_u64_max_input
from src.utils.common_utils import set_number_validator
from src.utils.common_utils import set_placeholder_value
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.wallet_logo_frame import WalletLogoFrame


class IssueIFAWidget(QWidget):
    """This class represents the UI for issuing IFA assets."""

    def __init__(self, view_model, draft_id=None, from_draft=False, params: RgbAssetPageLoadModel | None = None):
        super().__init__()
        self.render_timer = RenderTimer(task_name='IssueIFAAsset Rendering')
        self._view_model: MainViewModel = view_model
        self.setStyleSheet(load_stylesheet('views/qss/issue_nia_style.qss'))
        self.setObjectName('issue_ifa_page')

        self.params: RgbAssetPageLoadModel | None = params
        self.secondary_issuance: bool = bool(
            self.params and self.params.is_secondary_issuance,
        )
        self.issue_ifa_grid_layout = QGridLayout(self)
        self.issue_ifa_grid_layout.setObjectName('issue_nia_grid_layout')
        self.issue_ifa_wallet_logo = WalletLogoFrame(self)
        self.issue_ifa_grid_layout.addWidget(
            self.issue_ifa_wallet_logo, 0, 0, 1, 2,
        )
        self.draft_id = draft_id
        self.from_draft = from_draft

        self.horizontal_spacer_ifa_widget = QSpacerItem(
            265,
            20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.issue_ifa_grid_layout.addItem(
            self.horizontal_spacer_ifa_widget, 1, 3, 1, 1,
        )

        self.vertical_spacer_ifa_widget = QSpacerItem(
            20,
            190,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.issue_ifa_grid_layout.addItem(
            self.vertical_spacer_ifa_widget, 3, 1, 1, 1,
        )

        self.inflatables_horizontal_spacer_2 = QSpacerItem(
            266,
            20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.issue_ifa_grid_layout.addItem(
            self.inflatables_horizontal_spacer_2, 2, 0, 1, 1,
        )

        self.issue_ifa_vertical_spacer_1 = QSpacerItem(
            20,
            190,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.issue_ifa_grid_layout.addItem(
            self.issue_ifa_vertical_spacer_1, 0, 2, 1, 1,
        )

        self.issue_ifa_widget = QWidget(self)
        self.issue_ifa_widget.setObjectName(
            'issue_nia_widget',
        )
        self.issue_ifa_widget.setMinimumSize(QSize(499, 608))
        self.issue_ifa_widget.setMaximumSize(QSize(466, 608))

        self.inner_grid_layout = QGridLayout(self.issue_ifa_widget)
        self.inner_grid_layout.setSpacing(6)
        self.inner_grid_layout.setObjectName('inner_grid_layout')
        self.inner_grid_layout.setContentsMargins(1, 4, 1, 30)
        self.vertical_layout_issue_ifa = QVBoxLayout()
        self.vertical_layout_issue_ifa.setSpacing(6)
        self.vertical_layout_issue_ifa.setObjectName(
            'vertical_layout_setup_wallet_password',
        )
        self.issue_ifa_title_layout = QHBoxLayout()
        self.issue_ifa_title_layout.setObjectName('horizontal_layout_1')
        self.issue_ifa_title_layout.setContentsMargins(35, 9, 40, 0)
        self.issue_ifa_title = QLabel(
            self.issue_ifa_widget,
        )
        self.issue_ifa_title.setObjectName(
            'set_wallet_password_label',
        )
        self.issue_ifa_title.setMinimumSize(QSize(415, 63))

        self.issue_ifa_title_layout.addWidget(self.issue_ifa_title)

        self.ifa_close_btn = QPushButton(self.issue_ifa_widget)
        self.ifa_close_btn.setAccessibleName(ISSUE_NIA_ASSET_CLOSE_BUTTON)
        self.ifa_close_btn.setObjectName('nia_close_btn')
        self.ifa_close_btn.setMinimumSize(QSize(24, 24))
        self.ifa_close_btn.setMaximumSize(QSize(50, 65))
        self.ifa_close_btn.setAutoFillBackground(False)
        self.ifa_close_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        issue_ifa_close_icon = QIcon()
        issue_ifa_close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(),
            QIcon.Normal,
            QIcon.Off,
        )
        self.ifa_close_btn.setIcon(issue_ifa_close_icon)
        self.ifa_close_btn.setIconSize(QSize(24, 24))
        self.ifa_close_btn.setCheckable(False)
        self.ifa_close_btn.setChecked(False)

        self.issue_ifa_title_layout.addWidget(
            self.ifa_close_btn, 0, Qt.AlignHCenter,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.issue_ifa_title_layout,
        )

        self.header_line = QFrame(self.issue_ifa_widget)
        self.header_line.setObjectName('line_3')

        self.header_line.setFrameShape(QFrame.HLine)
        self.header_line.setFrameShadow(QFrame.Sunken)

        self.vertical_layout_issue_ifa.addWidget(self.header_line)

        self.inflatables_asset_ticker_layout = QVBoxLayout()
        self.inflatables_asset_ticker_layout.setSpacing(0)
        self.inflatables_asset_ticker_layout.setObjectName('vertical_layout_1')
        self.inflatables_asset_ticker_layout.setContentsMargins(60, -1, 0, -1)

        self.inflatables_asset_ticker_label = QLabel(self.issue_ifa_widget)
        self.inflatables_asset_ticker_label.setObjectName('asset_ticker_label')
        self.inflatables_asset_ticker_label.setMinimumSize(QSize(0, 35))
        self.inflatables_asset_ticker_label.setBaseSize(QSize(0, 0))
        self.inflatables_asset_ticker_label.setAutoFillBackground(False)
        self.inflatables_asset_ticker_label.setFrameShadow(QFrame.Plain)
        self.inflatables_asset_ticker_label.setLineWidth(1)

        self.inflatables_asset_ticker_layout.addWidget(
            self.inflatables_asset_ticker_label,
        )

        self.inflatables_short_identifier_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_short_identifier_input.setObjectName(
            'issue_nia_input',
        )
        self.inflatables_short_identifier_input.setAccessibleName(
            NIA_ASSET_TICKER,
        )
        self.inflatables_short_identifier_input.setMinimumSize(QSize(0, 40))
        self.inflatables_short_identifier_input.setMaximumSize(QSize(370, 40))

        self.inflatables_short_identifier_input.setFrame(False)
        self.inflatables_short_identifier_input.setClearButtonEnabled(False)

        self.inflatables_asset_ticker_layout.addWidget(
            self.inflatables_short_identifier_input,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.inflatables_asset_ticker_layout,
        )

        self.inflatables_asset_name_layout = QVBoxLayout()
        self.inflatables_asset_name_layout.setSpacing(0)
        self.inflatables_asset_name_layout.setObjectName('vertical_layout_2')
        self.inflatables_asset_name_layout.setContentsMargins(60, -1, 0, -1)

        self.inflatables_asset_name_label = QLabel(self.issue_ifa_widget)
        self.inflatables_asset_name_label.setObjectName('asset_name_label')
        self.inflatables_asset_name_label.setMinimumSize(QSize(0, 40))
        self.inflatables_asset_name_label.setMaximumSize(QSize(370, 40))
        self.inflatables_asset_name_layout.addWidget(
            self.inflatables_asset_name_label,
        )

        self.inflatables_asset_name_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_asset_name_input.setObjectName('asset_name_input')
        self.inflatables_asset_name_input.setAccessibleName(NIA_ASSET_NAME)
        self.inflatables_asset_name_input.setMinimumSize(QSize(0, 40))
        self.inflatables_asset_name_input.setMaximumSize(QSize(370, 40))

        self.inflatables_asset_name_input.setFrame(False)
        self.inflatables_asset_name_input.setClearButtonEnabled(False)

        self.inflatables_asset_name_layout.addWidget(
            self.inflatables_asset_name_input,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.inflatables_asset_name_layout,
        )
        self.inflatables_asset_supply_layout = QVBoxLayout()
        self.inflatables_asset_supply_layout.setSpacing(0)
        self.inflatables_asset_supply_layout.setObjectName('vertical_layout_3')
        self.inflatables_asset_supply_layout.setContentsMargins(60, -1, 0, -1)

        self.inflatables_issue_supply_label = QLabel(self.issue_ifa_widget)
        self.inflatables_issue_supply_label.setObjectName('total_supply_label')
        self.inflatables_issue_supply_label.setMinimumSize(QSize(0, 40))
        self.inflatables_issue_supply_label.setMaximumSize(QSize(370, 40))
        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_issue_supply_label,
        )

        self.inflatables_issue_amount_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_issue_amount_input.setObjectName('amount_input')
        self.inflatables_issue_amount_input.setAccessibleName(NIA_ASSET_AMOUNT)
        self.inflatables_issue_amount_input.setMinimumSize(QSize(0, 40))
        self.inflatables_issue_amount_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.inflatables_issue_amount_input)
        self.inflatables_issue_amount_input.setFrame(False)
        self.inflatables_issue_amount_input.setClearButtonEnabled(False)

        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_issue_amount_input,
        )

        self.inflatables_total_supply_label = QLabel(self.issue_ifa_widget)
        self.inflatables_total_supply_label.setObjectName('total_supply_label')
        self.inflatables_total_supply_label.setMinimumSize(QSize(0, 40))
        self.inflatables_total_supply_label.setMaximumSize(QSize(370, 40))
        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_total_supply_label,
        )

        self.inflatables_total_supply_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_total_supply_input.setObjectName('amount_input')
        self.inflatables_total_supply_input.setAccessibleName(NIA_ASSET_AMOUNT)
        self.inflatables_total_supply_input.setMinimumSize(QSize(0, 40))
        self.inflatables_total_supply_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.inflatables_total_supply_input)
        self.inflatables_total_supply_input.setFrame(False)
        self.inflatables_total_supply_input.setClearButtonEnabled(False)

        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_total_supply_input,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.inflatables_asset_supply_layout,
        )

        # Secondary issuance-only: option to replace label (shown only in secondary mode)
        self.replace_label_checkbox = QCheckBox(self.issue_ifa_widget)
        self.replace_label_checkbox.setObjectName('replace_label_checkbox')
        self.replace_label_checkbox.hide()  # shown only in secondary mode
        self.replace_checkbox_horizontal_layout = QHBoxLayout()
        self.replace_checkbox_horizontal_layout.setContentsMargins(0, 20, 0, 0)
        # self.replace_checkbox_horizontal_layout.addWidget(
        #     self.replace_label_checkbox,
        # )
        self.inflatables_asset_supply_layout.addLayout(
            self.replace_checkbox_horizontal_layout,
        )

        self.vertical_spacer_issue_ifa = QSpacerItem(
            20,
            40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.vertical_layout_issue_ifa.addItem(
            self.vertical_spacer_issue_ifa,
        )

        self.inflatables_footer_line = QFrame(self.issue_ifa_widget)
        self.inflatables_footer_line.setObjectName('bottom_line_frame')

        self.inflatables_footer_line.setFrameShape(QFrame.HLine)
        self.inflatables_footer_line.setFrameShadow(QFrame.Sunken)

        self.vertical_layout_issue_ifa.addWidget(self.inflatables_footer_line)

        self.inflatables_issue_button_spacer = QSpacerItem(
            20, 22, QSizePolicy.Preferred, QSizePolicy.Preferred,
        )
        self.vertical_layout_issue_ifa.addItem(
            self.inflatables_issue_button_spacer,
        )
        self.issue_ifa_btn = PrimaryButton()
        self.issue_ifa_btn.setAccessibleName(ISSUE_NIA_BUTTON)
        self.issue_ifa_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.issue_ifa_btn.setMinimumSize(QSize(402, 40))
        self.issue_ifa_btn.setMaximumSize(QSize(402, 40))

        self.issue_ifa_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.vertical_layout_issue_ifa.addWidget(
            self.issue_ifa_btn, 0, Qt.AlignCenter,
        )

        self.inner_grid_layout.addLayout(
            self.vertical_layout_issue_ifa,
            0,
            0,
            1,
            1,
        )

        self.issue_ifa_grid_layout.addWidget(
            self.issue_ifa_widget,
            1, 1, 2, 2,
        )
        self.setup_ui_connection()
        self.retranslate_ui()
        # Apply prefill rules for secondary issuance
        if self.params is not None and self.secondary_issuance:
            self.issue_ifa_title.setText('Secondary Issuance')
            if self.params.asset_name:
                self.inflatables_asset_name_input.setText(
                    self.params.asset_name,
                )
            if self.params.asset_id:
                self.inflatables_short_identifier_input.setText(
                    self.params.asset_id,
                )
                self.inflatables_short_identifier_input.setCursorPosition(0)
                self.inflatables_short_identifier_input.setReadOnly(True)
            # Hide total supply fields and lock name in secondary issuance
            self.inflatables_total_supply_label.hide()
            self.inflatables_total_supply_input.hide()
            self.inflatables_asset_name_input.setReadOnly(True)
            self.replace_label_checkbox.show()
            self.issue_ifa_widget.setFixedHeight(500)

        if self.from_draft and self.draft_id:
            self._load_inflatables_draft_data()
        else:
            if not self.secondary_issuance:
                self.inflatables_short_identifier_input.setText('')
                self.inflatables_asset_name_input.setText('')
                self.inflatables_issue_amount_input.setText('')

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.inflatables_asset_name_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.inflatables_short_identifier_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.inflatables_issue_amount_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.ifa_close_btn.clicked.connect(
            self._view_model.page_navigation.inflatable_asset_page,
        )
        self._view_model.issue_nia_asset_view_model.issue_button_clicked.connect(
            self.update_loading_state,
        )
        self.issue_ifa_btn.clicked.connect(self.on_issue_ifa_click)
        self._view_model.issue_nia_asset_view_model.is_issued.connect(
            self.inflatables_asset_issued,
        )
        self.inflatables_issue_amount_input.textChanged.connect(
            lambda: set_placeholder_value(self.inflatables_issue_amount_input),
        )
        self.inflatables_issue_amount_input.textChanged.connect(
            lambda text: enforce_u64_max_input(
                self.inflatables_issue_amount_input, text,
            ),
        )
        self._view_model.utxo_creation_view_model.hw_dialog_update.connect(
            self.handle_ifa_hw_dialog,
        )
        self._view_model.utxo_creation_view_model.utxo_created.connect(
            self.handle_ifa_utxo_created,
        )
        self._view_model.utxo_creation_view_model.unsigned_psbt.connect(
            self.show_ifa_psbt_page,
        )
        self._view_model.issue_nia_asset_view_model.utxo_creation_started.connect(
            self.handle_ifa_issue,
        )

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.issue_ifa_btn.setDisabled(True)
        self.issue_ifa_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'issue_new_ifa_asset',
                None,
            ),
        )
        if self.secondary_issuance:
            self.inflatables_asset_ticker_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'asset_id',
                    None,
                ),
            )
        else:
            self.inflatables_asset_ticker_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'asset_ticker',
                    None,
                ),
            )
        self.inflatables_short_identifier_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'short_identifier',
                None,
            ),
        )
        self.inflatables_asset_name_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'asset_name',
                None,
            ),
        )
        self.inflatables_asset_name_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'name_of_the_asset',
                None,
            ),
        )
        self.inflatables_issue_supply_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'issue_supply',
                None,
            ),
        )
        self.inflatables_issue_amount_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'amount_to_issue',
                None,
            ),
        )
        self.inflatables_total_supply_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'total_supply',
                None,
            ),
        )
        self.inflatables_total_supply_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'total_supply',
                None,
            ),
        )
        self.issue_ifa_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_asset', None,
            ),
        )
        # Checkbox label for secondary issue (fallback to raw if missing in translations)
        self.replace_label_checkbox.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'replace_label', None,
            ),
        )

    def update_loading_state(self, is_loading: bool):
        """
            Updates the loading state of the issue_ifa_btn.
            This method prints the loading state and starts or stops the loading animation
            of the proceed_wallet_password object based on the value of is_loading.
        """
        if is_loading:
            self.render_timer.start()
            self.issue_ifa_btn.start_loading()
            self.ifa_close_btn.setDisabled(True)
        else:
            self.render_timer.stop()
            self.issue_ifa_btn.stop_loading()
            self.ifa_close_btn.setDisabled(False)

    def on_issue_ifa_click(self):
        """Handle the click event for issuing a new IFA asset."""
        # Retrieve text values from input fields
        short_identifier = self.inflatables_short_identifier_input.text().upper()
        asset_name = self.inflatables_asset_name_input.text()
        amount_to_issue = self.inflatables_issue_amount_input.text()
        if not self.from_draft:
            self.create_issue_inflatables_asset_draft(
                short_identifier, asset_name, amount_to_issue,
            )

        # Call the view model method and pass the text values as arguments
        self._view_model.issue_nia_asset_view_model.on_issue_click(
            short_identifier, asset_name,
            amount_to_issue,
        )

    def handle_button_enabled(self):
        """Updates the enabled state of the send button."""
        if (
            self.inflatables_short_identifier_input.text() and
            self.inflatables_issue_amount_input.text(
            ) and self.inflatables_asset_name_input.text()
            and self.inflatables_issue_amount_input.text() != '0'
        ):
            self.issue_ifa_btn.setDisabled(False)
        else:
            self.issue_ifa_btn.setDisabled(True)

    def inflatables_asset_issued(self, asset_name):
        """This method handled after asset issued"""
        # Clean up draft if issuance was started from a draft
        if self.from_draft and self.draft_id:
            inflatables_wallet_service = WalletDataService.get_session()
            if inflatables_wallet_service is not None:
                inflatables_wallet_service.delete_draft_issue_asset(
                    self.draft_id,
                )
        inflatables_header = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_new_ticker',
        )
        inflatables_title = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'you_are_all_set',
        )
        inflatables_description = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_issued',
        ).format(asset_name)
        inflatables_button_text = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'home',
        )
        params = SuccessPageModel(
            header=inflatables_header,
            title=inflatables_title,
            description=inflatables_description,
            button_text=inflatables_button_text,
            callback=self._view_model.page_navigation.inflatable_asset_page,
        )
        self.render_timer.stop()
        self._view_model.page_navigation.show_success_page(params)

    def handle_ifa_hw_dialog(self, message: str, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler."""
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        ifa_hw_dialog.update_dialog(message, dialog_type)
        self.issue_ifa_btn.stop_loading()
        if not ifa_hw_dialog.isVisible():
            ifa_hw_dialog.show()

    def handle_ifa_utxo_created(self, status: bool):
        """Close the hardware wallet dialog after UTXO creation and resume asset issuance if pending."""
        if status:
            self._view_model.utxo_creation_view_model.utxo_created.disconnect()

            ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(
                parent=self,
            )
            if ifa_hw_dialog.isVisible():
                ifa_hw_dialog.accept()

            self.on_issue_ifa_click()

    def handle_ifa_issue(self):
        """handle ifa issue"""
        self._view_model.issue_nia_asset_view_model.utxo_creation_started.disconnect()
        inflatables_wallet_service = WalletDataService.get_session()
        if inflatables_wallet_service:
            unsigned_psbts = inflatables_wallet_service.list_psbt(
                signed=False,
            )
            existing_inflatables_psbt = next(
                (
                    p for p in unsigned_psbts if p.get('purpose') == 'issue_asset'
                ), None,
            )
            if existing_inflatables_psbt and existing_inflatables_psbt.get('psbt'):
                self.show_ifa_psbt_page(existing_inflatables_psbt.get('psbt'))
                return
        self._view_model.utxo_creation_view_model.create_utxos_begin(
            'issue_asset',
        )

    def show_ifa_psbt_page(self, inflatables_psbt):
        """Navigate to the receive asset page and display the PSBT as a QR code."""
        if inflatables_psbt:
            self._view_model.utxo_creation_view_model.unsigned_psbt.disconnect()
            self._view_model.page_navigation.receive_asset_page(
                ReceiveAssetModel(
                    page_name='IFA page',
                    address_info='psbt_info', psbt=inflatables_psbt, is_signed=False,
                ),
            )

    def create_issue_inflatables_asset_draft(self, ticker, name, amount):
        """Create and save an Issue Asset draft when UTXOs are not available.
        It stores minimal metadata so the draft can be shown on the fungible page.
        """
        inflatables_wallet_service = WalletDataService.get_session()
        if inflatables_wallet_service is not None:
            inflatables_wallet_service.upsert_draft_issue_asset(
                name=name,
                ticker=ticker,
                issued_amount=int(amount),
            )

    def _load_inflatables_draft_data(self):
        """Load draft data using the draft ID"""
        inflatables_wallet_service = WalletDataService.get_session()

        inflatables_drafts = inflatables_wallet_service.list_draft_issue_assets()
        draft = next(
            (
                d for d in inflatables_drafts if d.get(
                    'id',
                ) == self.draft_id
            ), None,
        )
        if draft:
            if 'name' in draft:
                self.inflatables_asset_name_input.setText(draft['name'])
            if 'ticker' in draft:
                self.inflatables_short_identifier_input.setText(
                    draft['ticker'],
                )
            if 'issued_amount' in draft:
                self.inflatables_issue_amount_input.setText(
                    str(draft['issued_amount']),
                )
            self.handle_button_enabled()
