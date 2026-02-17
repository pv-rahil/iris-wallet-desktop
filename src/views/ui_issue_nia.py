# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the IssueNIAWidget class,
 which represents the UI for issuing NIA assets.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
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
from src.model.common_operation_model import IssueAssetDraftModel
from src.model.common_operation_model import ReceiveAssetModel
from src.model.success_model import SuccessPageModel
from src.utils.common_utils import enforce_u64_max_input
from src.utils.helpers import register_multisig_button
from src.utils.common_utils import set_number_validator
from src.utils.common_utils import set_placeholder_value
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.decorators.check_colorable_available import get_unspent_utxo_count
from src.utils.helpers import load_stylesheet
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType

class IssueNIAWidget(QWidget):
    """This class represents the UI for issuing NIA assets."""

    def __init__(self, view_model, draft_id=None, from_draft=False):
        super().__init__()
        self.render_timer = RenderTimer(task_name='IssueNIAAsset Rendering')
        self._view_model: MainViewModel = view_model
        self.setStyleSheet(load_stylesheet('views/qss/issue_nia_style.qss'))
        self.setObjectName('issue_nia_page')
        self.issue_nia_grid_layout = QGridLayout(self)
        self.issue_nia_grid_layout.setObjectName('issue_nia_grid_layout')
        self.issue_nia_wallet_logo = WalletLogoFrame(self)
        self.issue_nia_grid_layout.addWidget(
            self.issue_nia_wallet_logo, 0, 0, 1, 2,
        )
        self.draft_id = draft_id
        self.from_draft = from_draft
        self.is_multisig_wallet = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        self.is_offline_wallet = SettingRepository.get_wallet_type(
        ) == WalletType.OFFLINE_TYPE_WALLET

        self.horizontal_spacer_nia_widget = QSpacerItem(
            265,
            20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.issue_nia_grid_layout.addItem(
            self.horizontal_spacer_nia_widget, 1, 3, 1, 1,
        )

        self.vertical_spacer_nia_widget = QSpacerItem(
            20,
            190,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.issue_nia_grid_layout.addItem(
            self.vertical_spacer_nia_widget, 3, 1, 1, 1,
        )

        self.horizontal_spacer_2 = QSpacerItem(
            266,
            20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.issue_nia_grid_layout.addItem(
            self.horizontal_spacer_2, 2, 0, 1, 1,
        )

        self.issue_nia_vertical_spacer_1 = QSpacerItem(
            20,
            190,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.issue_nia_grid_layout.addItem(
            self.issue_nia_vertical_spacer_1, 0, 2, 1, 1,
        )

        self.issue_nia_widget = QWidget(self)
        self.issue_nia_widget.setObjectName(
            'issue_nia_widget',
        )
        self.issue_nia_widget.setMinimumSize(QSize(499, 608))
        self.issue_nia_widget.setMaximumSize(QSize(466, 608))

        self.inner_grid_layout = QGridLayout(self.issue_nia_widget)
        self.inner_grid_layout.setSpacing(6)
        self.inner_grid_layout.setObjectName('inner_grid_layout')
        self.inner_grid_layout.setContentsMargins(1, 4, 1, 30)
        self.vertical_layout_issue_nia = QVBoxLayout()
        self.vertical_layout_issue_nia.setSpacing(6)
        self.vertical_layout_issue_nia.setObjectName(
            'vertical_layout_setup_wallet_password',
        )
        self.issue_nia_title_layout = QHBoxLayout()
        self.issue_nia_title_layout.setObjectName('horizontal_layout_1')
        self.issue_nia_title_layout.setContentsMargins(35, 9, 40, 0)
        self.issue_nia_title = QLabel(
            self.issue_nia_widget,
        )
        self.issue_nia_title.setObjectName(
            'set_wallet_password_label',
        )
        self.issue_nia_title.setMinimumSize(QSize(415, 63))

        self.issue_nia_title_layout.addWidget(self.issue_nia_title)

        self.nia_close_btn = QPushButton(self.issue_nia_widget)
        self.nia_close_btn.setAccessibleName(ISSUE_NIA_ASSET_CLOSE_BUTTON)
        self.nia_close_btn.setObjectName('close_btn')
        self.nia_close_btn.setMinimumSize(QSize(24, 24))
        self.nia_close_btn.setMaximumSize(QSize(50, 65))
        self.nia_close_btn.setAutoFillBackground(False)
        self.nia_close_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        issue_nia_close_icon = QIcon()
        issue_nia_close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(),
            QIcon.Normal,
            QIcon.Off,
        )
        self.nia_close_btn.setIcon(issue_nia_close_icon)
        self.nia_close_btn.setIconSize(QSize(24, 24))
        self.nia_close_btn.setCheckable(False)
        self.nia_close_btn.setChecked(False)

        self.issue_nia_title_layout.addWidget(
            self.nia_close_btn, 0, Qt.AlignHCenter,
        )

        self.vertical_layout_issue_nia.addLayout(
            self.issue_nia_title_layout,
        )

        self.header_line = QFrame(self.issue_nia_widget)
        self.header_line.setObjectName('line_3')

        self.header_line.setFrameShape(QFrame.HLine)
        self.header_line.setFrameShadow(QFrame.Sunken)

        self.vertical_layout_issue_nia.addWidget(self.header_line)

        self.asset_ticker_layout = QVBoxLayout()
        self.asset_ticker_layout.setSpacing(0)
        self.asset_ticker_layout.setObjectName('vertical_layout_1')
        self.asset_ticker_layout.setContentsMargins(60, -1, 0, -1)

        self.asset_ticker_label = QLabel(self.issue_nia_widget)
        self.asset_ticker_label.setObjectName('asset_ticker_label')
        self.asset_ticker_label.setMinimumSize(QSize(0, 35))
        self.asset_ticker_label.setBaseSize(QSize(0, 0))
        self.asset_ticker_label.setAutoFillBackground(False)
        self.asset_ticker_label.setFrameShadow(QFrame.Plain)
        self.asset_ticker_label.setLineWidth(1)

        self.asset_ticker_layout.addWidget(self.asset_ticker_label)

        self.short_identifier_input = QLineEdit(
            self.issue_nia_widget,
        )
        self.short_identifier_input.setObjectName('issue_nia_input')
        self.short_identifier_input.setAccessibleName(NIA_ASSET_TICKER)
        self.short_identifier_input.setMinimumSize(QSize(0, 40))
        self.short_identifier_input.setMaximumSize(QSize(370, 40))

        self.short_identifier_input.setFrame(False)
        self.short_identifier_input.setClearButtonEnabled(False)

        self.asset_ticker_layout.addWidget(self.short_identifier_input)

        self.vertical_layout_issue_nia.addLayout(
            self.asset_ticker_layout,
        )

        self.asset_name_layout = QVBoxLayout()
        self.asset_name_layout.setSpacing(0)
        self.asset_name_layout.setObjectName('vertical_layout_2')
        self.asset_name_layout.setContentsMargins(60, -1, 0, -1)

        self.asset_name_label = QLabel(self.issue_nia_widget)
        self.asset_name_label.setObjectName('asset_name_label')
        self.asset_name_label.setMinimumSize(QSize(0, 40))
        self.asset_name_label.setMaximumSize(QSize(370, 40))
        self.asset_name_layout.addWidget(self.asset_name_label)

        self.asset_name_input = QLineEdit(
            self.issue_nia_widget,
        )
        self.asset_name_input.setObjectName('asset_name_input')
        self.asset_name_input.setAccessibleName(NIA_ASSET_NAME)
        self.asset_name_input.setMinimumSize(QSize(0, 40))
        self.asset_name_input.setMaximumSize(QSize(370, 40))

        self.asset_name_input.setFrame(False)
        self.asset_name_input.setClearButtonEnabled(False)

        self.asset_name_layout.addWidget(self.asset_name_input)

        self.vertical_layout_issue_nia.addLayout(
            self.asset_name_layout,
        )
        self.asset_supply_layout = QVBoxLayout()
        self.asset_supply_layout.setSpacing(0)
        self.asset_supply_layout.setObjectName('vertical_layout_3')
        self.asset_supply_layout.setContentsMargins(60, -1, 0, -1)

        self.total_supply_label = QLabel(self.issue_nia_widget)
        self.total_supply_label.setObjectName('total_supply_label')
        self.total_supply_label.setMinimumSize(QSize(0, 40))
        self.total_supply_label.setMaximumSize(QSize(370, 40))
        self.asset_supply_layout.addWidget(self.total_supply_label)

        self.amount_input = QLineEdit(
            self.issue_nia_widget,
        )
        self.amount_input.setObjectName('amount_input')
        self.amount_input.setAccessibleName(NIA_ASSET_AMOUNT)
        self.amount_input.setMinimumSize(QSize(0, 40))
        self.amount_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.amount_input)
        self.amount_input.setFrame(False)
        self.amount_input.setClearButtonEnabled(False)

        self.asset_supply_layout.addWidget(self.amount_input)

        self.vertical_layout_issue_nia.addLayout(
            self.asset_supply_layout,
        )

        self.vertical_spacer_issue_nia = QSpacerItem(
            20,
            40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.vertical_layout_issue_nia.addItem(
            self.vertical_spacer_issue_nia,
        )

        self.footer_line = QFrame(self.issue_nia_widget)
        self.footer_line.setObjectName('bottom_line_frame')

        self.footer_line.setFrameShape(QFrame.HLine)
        self.footer_line.setFrameShadow(QFrame.Sunken)

        self.vertical_layout_issue_nia.addWidget(self.footer_line)

        self.issue_button_spacer = QSpacerItem(
            20, 22, QSizePolicy.Preferred, QSizePolicy.Preferred,
        )
        self.vertical_layout_issue_nia.addItem(self.issue_button_spacer)
        self.issue_nia_btn = PrimaryButton()
        self.issue_nia_btn.setAccessibleName(ISSUE_NIA_BUTTON)
        self.issue_nia_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.issue_nia_btn.setMinimumSize(QSize(402, 40))
        self.issue_nia_btn.setMaximumSize(QSize(402, 40))

        self.issue_nia_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.vertical_layout_issue_nia.addWidget(
            self.issue_nia_btn, 0, Qt.AlignCenter,
        )

        self.inner_grid_layout.addLayout(
            self.vertical_layout_issue_nia,
            0,
            0,
            1,
            1,
        )

        self.issue_nia_grid_layout.addWidget(
            self.issue_nia_widget,
            1,
            1,
            2,
            2,
        )
        self.setup_ui_connection()
        self.retranslate_ui()
        if self.from_draft and self.draft_id:
            self._load_draft_data()
        else:
            self.short_identifier_input.setText('')
            self.asset_name_input.setText('')
            self.amount_input.setText('')

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.asset_name_input.textChanged.connect(self.handle_button_enabled)
        self.short_identifier_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.amount_input.textChanged.connect(self.handle_button_enabled)
        self.nia_close_btn.clicked.connect(
            self._view_model.issue_nia_asset_view_model.on_close_click,
        )
        self._view_model.issue_nia_asset_view_model.issue_button_clicked.connect(
            self.update_loading_state,
        )
        if not self.is_multisig_wallet:
            self.issue_nia_btn.clicked.connect(
                self.on_issue_nia_click,
            )
        else:
            register_multisig_button(
                self._view_model,
                self.issue_nia_btn,
                self.on_issue_nia_click
            )
        self._view_model.issue_nia_asset_view_model.is_issued.connect(
            self.asset_issued,
        )
        self.amount_input.textChanged.connect(
            lambda: set_placeholder_value(self.amount_input),
        )
        self.amount_input.textChanged.connect(
            lambda text: enforce_u64_max_input(self.amount_input, text),
        )
        self._view_model.utxo_creation_view_model.hw_dialog_update.connect(
            self.handle_nia_hw_dialog,
        )
        self._view_model.utxo_creation_view_model.utxo_created.connect(
            self.handle_nia_utxo_created,
        )
        self._view_model.utxo_creation_view_model.psbt_posted_to_bridge.connect(
            self.handle_psbt_posted_to_bridge,
        )

        self._view_model.utxo_creation_view_model.unsigned_psbt.connect(
            self.show_nia_psbt_page,
        )
        self._view_model.issue_nia_asset_view_model.utxo_creation_started.connect(
            self.handle_nia_issue,
        )

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.issue_nia_btn.setDisabled(True)
        self.issue_nia_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'issue_new_nia_asset',
                None,
            ),
        )
        self.asset_ticker_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'asset_ticker',
                None,
            ),
        )
        self.short_identifier_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'short_identifier',
                None,
            ),
        )
        self.asset_name_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'asset_name',
                None,
            ),
        )
        self.asset_name_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'name_of_the_asset',
                None,
            ),
        )
        self.total_supply_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'total_supply',
                None,
            ),
        )
        self.amount_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'amount_to_issue',
                None,
            ),
        )
        self.issue_nia_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_asset', None,
            ),
        )

    def update_loading_state(self, is_loading: bool):
        """
            Updates the loading state of the issue_nia_btn.
            This method prints the loading state and starts or stops the loading animation
            of the proceed_wallet_password object based on the value of is_loading.
        """
        if is_loading:
            self.render_timer.start()
            self.issue_nia_btn.start_loading()
            self.nia_close_btn.setDisabled(True)
        else:
            self.render_timer.stop()
            self.issue_nia_btn.stop_loading()
            self.nia_close_btn.setDisabled(False)

    def on_issue_nia_click(self):
        """Handle the click event for issuing a new NIA asset."""
        # Retrieve text values from input fields
        short_identifier = self.short_identifier_input.text().upper()
        asset_name = self.asset_name_input.text()
        amount_to_issue = self.amount_input.text()
        if not self.from_draft:
            self.create_issue_asset_draft(
                short_identifier, asset_name, amount_to_issue,
            )

        # Call the view model method and pass the text values as arguments
        self._view_model.issue_nia_asset_view_model.on_issue_click(
            short_identifier,
            asset_name,
            amount_to_issue,
        )

    def handle_button_enabled(self):
        """Updates the enabled state of the send button."""
        if (self.short_identifier_input.text() and self.amount_input.text() and self.asset_name_input.text() and self.amount_input.text() != '0'):
            self.issue_nia_btn.setDisabled(False)
        else:
            self.issue_nia_btn.setDisabled(True)

    def asset_issued(self, asset_name):
        """This method handled after asset issued"""
        # Clean up draft if issuance was started from a draft
        if self.from_draft and self.draft_id:
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.delete_draft_issue_asset(self.draft_id)
        nia_header = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_new_ticker',
        )
        nia_title = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'you_are_all_set',
        )
        nia_description = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_issued',
        ).format(asset_name)
        nia_button_text = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'home',
        )
        params = SuccessPageModel(
            header=nia_header,
            title=nia_title,
            description=nia_description,
            button_text=nia_button_text,
            callback=self._view_model.page_navigation.fungibles_asset_page,
        )
        self.render_timer.stop()
        self._view_model.page_navigation.show_success_page(params)

    def handle_nia_hw_dialog(self, message: str, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler."""
        nia_hw_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        nia_hw_dialog.update_dialog(message, dialog_type)
        self.issue_nia_btn.stop_loading()
        if not nia_hw_dialog.isVisible():
            nia_hw_dialog.show()

    def handle_psbt_posted_to_bridge(self):
        """Handle PSBT posted to bridge (multisig initiator)."""
        # Only handle if the current purpose matches NIA issuing
        if self._view_model.utxo_creation_view_model.current_purpose != 'issue_asset_nia':
            return
        # Close dialog
        self._view_model.utxo_creation_view_model.psbt_posted_to_bridge.disconnect()
        nia_hw_dialog = HardwareWalletOperationDialog.get_instance(parent=self)
        if nia_hw_dialog.isVisible():
            nia_hw_dialog.accept()

        # Notify and navigate
        ToastManager.success(INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE)
        self._view_model.page_navigation.fungibles_asset_page()

    def handle_nia_utxo_created(self, status: bool):
        """Close the hardware wallet dialog after UTXO creation and resume asset issuance if pending."""
        # Only handle if the current purpose matches NIA issuing
        if self._view_model.utxo_creation_view_model.current_purpose != 'issue_asset_nia':
            return
        if status:
            self._view_model.utxo_creation_view_model.utxo_created.disconnect()

            nia_hw_dialog = HardwareWalletOperationDialog.get_instance(
                parent=self,
            )
            if nia_hw_dialog.isVisible():
                nia_hw_dialog.accept()

            self.on_issue_nia_click()

    def handle_nia_issue(self):
        """handle nia issue"""
        self._view_model.issue_nia_asset_view_model.utxo_creation_started.disconnect()
        wallet_service = WalletDataService.get_session()
        if wallet_service:
            unsigned_psbts = wallet_service.list_psbt(
                signed=False,
            )
            existing_psbt = next(
                (
                    p for p in unsigned_psbts if p.get('purpose') == 'issue_asset_nia'
                ), None,
            )
            if existing_psbt and existing_psbt.get('psbt'):
                self._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_nia'
                self.show_nia_psbt_page(existing_psbt.get('psbt'))
                return
        # Compute missing UTXOs (required = 3) and create only those
        current = get_unspent_utxo_count()
        needed = 1 - current
        needed = needed if needed > 0 else 1
        self._view_model.utxo_creation_view_model.create_utxos_begin(
            'issue_asset_nia', needed,
        )

    def show_nia_psbt_page(self, psbt):
        """Navigate to the receive asset page and display the PSBT as a QR code."""
        # Only respond if PSBT relates to NIA issuing purpose
        if self._view_model.utxo_creation_view_model.current_purpose != 'issue_asset_nia':
            return
        if psbt:
            self._view_model.page_navigation.receive_asset_page(
                ReceiveAssetModel(
                    page_name='NIA page',
                    address_info='psbt_info', psbt=psbt, is_signed=False,
                ),
            )

    def create_issue_asset_draft(self, ticker, name, amount):
        """Create and save an Issue Asset draft when UTXOs are not available.
        It stores minimal metadata so the draft can be shown on the fungible page.
        """
        wallet_service = WalletDataService.get_session()
        if wallet_service is not None:
            wallet_service.upsert_draft_issue_asset(
                IssueAssetDraftModel(
                    name=name,
                    ticker=ticker,
                    issued_amount=int(amount),
                ),
            )

    def _load_draft_data(self):
        """Load draft data using the draft ID"""
        wallet_service = WalletDataService.get_session()

        drafts = wallet_service.list_draft_issue_assets()
        draft = next((d for d in drafts if d.get('id') == self.draft_id), None)
        if draft:
            if 'name' in draft:
                self.asset_name_input.setText(draft['name'])
            if 'ticker' in draft:
                self.short_identifier_input.setText(draft['ticker'])
            if 'issued_amount' in draft:
                self.amount_input.setText(str(draft['issued_amount']))
            self.handle_button_enabled()
