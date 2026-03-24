# pylint: disable=too-many-instance-attributes, too-many-statements, too-few-public-methods
"""
Multisig setup page – full-page view.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import QStandardPaths
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFileDialog
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
from rgb_lib import Cosigner
from rgb_lib import CosignerData

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import InitRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.utils.build_app_path import app_paths
from src.utils.common_utils import copy_text
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import MASTER_XPUB
from src.utils.constant import MNEMONIC_KEY
from src.utils.constant import VANILLA_KEYCHAIN
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.helpers import load_stylesheet
from src.utils.keyring_storage import get_value
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.page_navigation_events import PageNavigationEventManager
from src.utils.wallet_credential_encryption import mnemonic_store
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton
from src.views.components.cosigner_detail_card import CosignerDetailCard
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame


class MultisigSetupPage(QWidget):
    """Multisig wallet setup page — handles threshold, key generation and cosigner collection."""

    def __init__(self, view_model):
        super().__init__()
        self._view_model = view_model

        network = SettingRepository.get_wallet_network()
        self._password = get_value(WALLET_PASSWORD_KEY, network.value)

        if not self._password:
            logger.error('Multisig setup accessed without password set!')
            PageNavigationEventManager.get_instance().selection_page_signal.emit(None)
            return

        self._setup_ui()

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

        self.required_signer_input.textChanged.connect(self._update_summary)
        self.total_signer_input.textChanged.connect(self._update_summary)
        self.required_signer_input.textChanged.connect(self._update_continue_enabled)
        self.total_signer_input.textChanged.connect(self._update_continue_enabled)

        saved_m, saved_n = SettingRepository.get_multisig_config()
        if saved_m and saved_n:
            self.required_signer_input.setText(str(saved_m))
            self.total_signer_input.setText(str(saved_n))

            is_hardware_wallet = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
            if is_hardware_wallet and not self._is_watch_only:
                master_fp = local_store.get_value(MASTER_FINGERPRINT)
                account_xpub_vanilla = local_store.get_value(ACCOUNT_XPUB_VANILLA)
                account_xpub_colored = local_store.get_value(ACCOUNT_XPUB_COLORED)

                if master_fp and account_xpub_vanilla and account_xpub_colored:
                    self._complete_threshold_confirmation_after_hw_connect(saved_m, saved_n)
                    return

            stored_cosigners = SettingRepository.get_cosigners()
            if stored_cosigners:
                self._restore_cosigner_inputs(stored_cosigners)
                self._update_continue_enabled()

    # ------------------------------------------------------------------ #
    #  UI Setup                                                            #
    # ------------------------------------------------------------------ #

    def _setup_ui(self):
        """Build and wire the widget tree."""
        self.setStyleSheet(load_stylesheet('views/qss/multisig_setup_page.qss'))

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)

        self.logo = WalletLogoFrame(self)
        self.grid.addWidget(self.logo, 0, 0, 1, 2)
        self.grid.addItem(QSpacerItem(268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 1, 0)

        self.card = QWidget(self)
        self.card.setObjectName('ms_page_card')
        self.card.setMinimumSize(QSize(770, 530))
        self.card.setMaximumSize(QSize(770, 530))
        self.v = QVBoxLayout(self.card)
        self.v.setContentsMargins(0, 12, 0, 20)
        self.v.setSpacing(10)
        self.vertical_layout = self.v
        self.breadcrumb_widget = None

        self.continue_button = PrimaryButton()
        self.continue_button.setFixedSize(QSize(100, 40))
        self.continue_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Title row
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(30, 9, 30, 0)
        self.title = QLabel()
        self.title.setObjectName('ms_title')
        self.title.setMinimumSize(QSize(415, 63))
        self.title.setMaximumSize(QSize(415, 63))
        title_layout.addWidget(self.title)
        title_layout.addStretch()
        self.close_btn = QPushButton()
        self.close_btn.setObjectName('close_button')
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setIcon(QIcon(':/assets/x_circle.png'))
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.clicked.connect(self._view_model.page_navigation.selection_page)
        title_layout.addWidget(self.close_btn)
        self.v.addLayout(title_layout)
        self.close_btn.show()

        above_line = QFrame(self.card)
        above_line.setObjectName('above_line_frame')
        above_line.setFrameShape(QFrame.HLine)
        above_line.setFrameShadow(QFrame.Sunken)
        self.v.addWidget(above_line)

        # Step 1: Threshold frame
        self.threshold_frame = self._build_threshold_frame()
        self.v.addWidget(self.threshold_frame)

        # Step 2: Review frame (hidden until step 2)
        self.review_frame = self._build_review_frame()
        self.v.addWidget(self.review_frame)

        # Creator frame (action row placeholder)
        self.creator_frame = QFrame(self.card)
        self.creator_frame.setObjectName('capabilities_frame')
        self.creator_frame.hide()
        self.creator_v = QVBoxLayout(self.creator_frame)
        self.creator_v.setContentsMargins(35, 0, 20, 0)
        self.creator_actions = QHBoxLayout()
        self.creator_actions.setContentsMargins(35, 0, 0, 0)
        self.creator_actions.setSpacing(12)
        self.creator_v.addLayout(self.creator_actions)
        self.v.addWidget(self.creator_frame)

        # Step 3: Cosigners frame (hidden until step 3)
        self.cos_frame = self._build_cosigner_frame()
        self.v.addWidget(self.cos_frame)

        # Footer
        self._build_footer()

        # Grid spacers
        self.grid.addItem(QSpacerItem(20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding), 0, 1)
        self.grid.addWidget(self.card, 1, 1)
        self.grid.addItem(QSpacerItem(20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding), 2, 1)
        self.grid.addItem(QSpacerItem(268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 1, 2)

    def _build_threshold_frame(self) -> QFrame:
        frame = QFrame(self.card)
        frame.setObjectName('capabilities_frame')
        t_v = QVBoxLayout(frame)
        t_v.setContentsMargins(34, 14, 34, 6)
        t_v.setSpacing(10)

        # Info box
        info_box = QFrame(frame)
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
        t_v.addWidget(info_box)

        # Total signers
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
        tot_block.addWidget(self.total_signer_input)
        self.total_signer_help = QLabel()
        self.total_signer_help.setObjectName('ms_helper')
        tot_block.addWidget(self.total_signer_help)
        t_v.addLayout(tot_block)

        # Required signers
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
        req_block.addWidget(self.required_signer_input)
        self.required_signer_help = QLabel()
        self.required_signer_help.setObjectName('ms_helper')
        req_block.addWidget(self.required_signer_help)
        t_v.addLayout(req_block)

        # Summary box
        summary_box = QFrame(frame)
        summary_box.setFixedWidth(700)
        summary_box.setObjectName('ms_summary_box')
        sum_h = QHBoxLayout(summary_box)
        sum_h.setContentsMargins(14, 12, 14, 12)
        self.summary_text = QLabel()
        self.summary_text.setObjectName('ms_label')
        sum_h.addWidget(self.summary_text)
        sum_h.addStretch()
        t_v.addWidget(summary_box)

        return frame

    def _build_review_frame(self) -> QFrame:
        frame = QFrame(self.card)
        frame.setObjectName('capabilities_frame')
        frame.hide()
        self.r_v = QVBoxLayout(frame)
        self.r_v.setContentsMargins(34, 0, 34, 6)
        self.r_v.setSpacing(14)

        title_lbl = QLabel('Review your wallet info and copy fields as needed.')
        title_lbl.setObjectName('ms_label')
        title_lbl.setContentsMargins(0, 4, 0, 10)
        self.r_v.addWidget(title_lbl)

        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(12)
        self.row2 = QHBoxLayout()
        self.row2.setContentsMargins(0, 0, 0, 0)
        self.row2.setSpacing(12)

        self.fp_display, self.fp_value_widget, _ = self._make_detail_field(
            QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint'), '',
        )
        self.keychain_display, self.keychain_value_widget, _ = self._make_detail_field(
            QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keychain'), '',
        )
        self.row1.addLayout(self.fp_display)
        self.row1.addLayout(self.keychain_display)
        self.r_v.addLayout(self.row1)

        self.path_display, self.path_value_widget, _ = self._make_detail_field(
            QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'derivation_path'), '',
        )
        self.xpub_vanilla_display, self.xpub_vanilla_value_widget, _ = self._make_detail_field(
            QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_vanilla'), '',
        )
        self.row2.addLayout(self.xpub_vanilla_display)
        self.r_v.addLayout(self.row2)

        self.row3 = QHBoxLayout()
        self.row3.setContentsMargins(0, 0, 0, 0)
        self.row3.setSpacing(12)
        self.xpub_colored_display, self.xpub_colored_value_widget, self.xpub_colored_copy_btn = self._make_detail_field(
            QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'account_xpub_colored'), '',
            show_copy_btn=True,
            info_text=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'colored_xpub_info_text',
                'Share this with the bridge operator to sync with the multisig bridge',
            ),
        )
        self.row3.addLayout(self.xpub_colored_display)
        self.r_v.addLayout(self.row3)

        self.row5 = QHBoxLayout()
        self.row5.setContentsMargins(0, 0, 0, 0)
        self.row5.setSpacing(12)
        self.cosigner_string_display, self.cosigner_string_value_widget, self.cosigner_string_copy_btn = self._make_detail_field(
            QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'signer_details'), '',
            show_copy_btn=True,
            info_text=QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'signer_details_explanation'),
        )
        self.row5.addLayout(self.cosigner_string_display)
        self.r_v.addLayout(self.row5)
        self.r_v.addStretch()

        return frame

    def _build_cosigner_frame(self) -> QFrame:
        frame = QFrame(self.card)
        frame.setObjectName('capabilities_frame')
        frame.hide()
        frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        c_v = QVBoxLayout(frame)
        c_v.setContentsMargins(34, 14, 34, 16)
        c_v.setSpacing(16)

        scroll = QScrollArea()
        scroll.setObjectName('ms_scroll')
        self.cos_scroll = scroll
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

        self.cosigner_rows = []
        return frame

    def _build_footer(self):
        self.footer = QHBoxLayout()
        self.footer.setContentsMargins(0, 4, 35, 12)

        self.export_button = PrimaryButton()
        self.export_button.setIcon(QIcon(':/assets/export.png'))
        self.export_button.setIconSize(QSize(18, 18))
        self.export_button.setLayoutDirection(Qt.RightToLeft)
        self.export_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_button.setFixedSize(QSize(100, 40))
        self.export_button.hide()
        self.export_button.clicked.connect(self._export_cosigner_to_file)
        self.footer.addSpacing(35)
        self.footer.addWidget(self.export_button)

        self.back_button = PrimaryButton()
        self.back_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_button.setFixedSize(QSize(100, 40))
        self.back_button.clicked.connect(self._go_back)
        self.footer.addStretch()
        self.footer.addSpacing(12)
        self.footer.addWidget(self.back_button)
        self.footer.addSpacing(12)
        self.continue_button.clicked.connect(self._go_next)
        self.footer.addWidget(self.continue_button)
        self.v.addLayout(self.footer)

    def _make_detail_field(
        self, title: str, placeholder: str,
        show_copy_btn: bool = False, info_text: str = None,
    ) -> tuple[QGridLayout, QLineEdit, QPushButton]:
        """Create a labelled read-only field with an optional copy button."""
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        copy_btn = None

        label_container = QWidget()
        lbl_layout = QHBoxLayout(label_container)
        lbl_layout.setContentsMargins(0, 0, 0, 0)
        lbl_layout.setSpacing(8)
        lbl = QLabel(title[:-1] if title.endswith(':') else title)
        lbl.setObjectName('ms_label')
        lbl_layout.addWidget(lbl)
        if info_text:
            info_btn = QPushButton()
            info_btn.setObjectName('ms_info_button')
            info_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            info_btn.setFlat(True)
            info_btn.setIcon(QIcon(':/assets/info_circle.png'))
            info_btn.setIconSize(QSize(20, 20))
            info_btn.setFixedSize(QSize(20, 20))
            info_btn.setToolTip(info_text)
            lbl_layout.addWidget(info_btn)
        lbl_layout.addStretch()
        grid.addWidget(label_container, 0, 0)

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        inp = QLineEdit()
        inp.setObjectName('wallet_detail_input')
        inp.setFixedHeight(40)
        inp.setReadOnly(True)
        inp.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))
        inp.setFrame(False)
        inp.setClearButtonEnabled(False)
        inp.setPlaceholderText(placeholder)
        h.addWidget(inp)
        if show_copy_btn:
            inp.setStyleSheet('border-top-right-radius: 0px; border-bottom-right-radius: 0px;')
            copy_btn = QPushButton()
            copy_btn.setObjectName('copy_button')
            copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            copy_btn.setMinimumSize(QSize(50, 0))
            copy_btn.setMaximumSize(QSize(50, 40))
            ic = QIcon()
            ic.addFile(':/assets/copy.png', QSize(), QIcon.Normal, QIcon.Off)
            copy_btn.setIcon(ic)
            h.addWidget(copy_btn)
        grid.addLayout(h, 1, 0)
        return grid, inp, copy_btn

    # ------------------------------------------------------------------ #
    #  Translations                                                        #
    # ------------------------------------------------------------------ #

    def retranslate_ui(self):
        """Set or refresh all translatable UI strings."""
        self.title.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'multisig_setup_title'))
        self.back_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'back'))
        self.export_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'export') + ' ')
        self.total_signer_help.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_cosigners_help'))
        self.req_lbl.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'required_signatures_label'))
        self.info_title.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'configure_signature_requirements'))
        self.info_sub.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'choose_number_of_signatures'))
        self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next'))
        self.tot_lbl.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_cosigners_label'))

    # ------------------------------------------------------------------ #
    #  Hardware-wallet post-connect hook                                   #
    # ------------------------------------------------------------------ #

    def _complete_threshold_confirmation_after_hw_connect(self, m: int, n: int):
        """Complete threshold confirmation after returning from hardware wallet setup."""
        self.required_signer_input.setEnabled(False)
        self.total_signer_input.setEnabled(False)
        self._threshold_locked = True

        for card in self.cosigner_rows:
            self.cosigners_v.removeWidget(card)
            card.deleteLater()
        self.cosigner_rows.clear()

        for i in range(2, n + 1):
            self._add_cosigner_row(i)

        self.threshold_frame.hide()
        self.creator_frame.hide()
        self.back_button.show()
        self.close_btn.hide()

        if self._is_watch_only:
            self.cos_frame.show()
            self._current_step = 2
            self.card.setMinimumSize(QSize(770, 640))
            self.card.setMaximumSize(QSize(770, 640))
            self._update_continue_enabled()
            self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue'))
        else:
            self._populate_wallet_review_fields()
            self.review_frame.show()
            self.cos_frame.hide()
            self._current_step = 2
            self.export_button.show()
            self.card.setMinimumSize(QSize(770, 570))
            self.card.setMaximumSize(QSize(770, 570))
            self._update_continue_enabled()
            self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next'))

    # ------------------------------------------------------------------ #
    #  Threshold & Key Generation                                          #
    # ------------------------------------------------------------------ #

    def _on_confirm_threshold(self) -> bool:
        """Lock threshold and create exact N cosigner rows."""
        n = self._get_total_signer()
        m = self._get_required_signer()
        if m > n or m < 1 or n < 2:
            return False

        self.required_signer_input.setEnabled(False)
        self.total_signer_input.setEnabled(False)
        self._threshold_locked = True
        SettingRepository.set_multisig_config(m, n)

        is_hardware_wallet = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET

        if not self._is_watch_only:
            try:
                if is_hardware_wallet:
                    SettingRepository.set_multisig_config(m, n)
                    self._view_model.page_navigation.hardware_wallet_connect_page(is_multisig=True)
                    return True
                elif os.path.exists(app_paths.mnemonic_file_path):
                    print('Keys already exist - skipping generation to preserve mnemonic.')
                else:
                    network = get_bitcoin_network_from_enum(SettingRepository.get_wallet_network())
                    keys = CommonOperationRepository.init(InitRequestModel(password='', network=network))
                    local_store.set_value(MASTER_FINGERPRINT, keys.master_fingerprint)
                    local_store.set_value(MASTER_XPUB, keys.xpub)
                    local_store.set_value(ACCOUNT_XPUB_VANILLA, keys.account_xpub_vanilla)
                    local_store.set_value(ACCOUNT_XPUB_COLORED, keys.account_xpub_colored)
                    encrypted = mnemonic_store.encrypt(self._password, keys.mnemonic)
                    local_store.write_to_file(
                        file_name=MNEMONIC_KEY, file_path=app_paths.mnemonic_file_path, value=encrypted,
                    )
                    print('Fresh setup - encrypted and saved mnemonic.')
            except Exception as e:
                print(f'Error generating/loading wallet keys: {e}')
                self.required_signer_input.setEnabled(True)
                self.total_signer_input.setEnabled(True)
                self._threshold_locked = False
                SettingRepository.set_multisig_config(None, None)
                return False

        for card in self.cosigner_rows:
            self.cosigners_v.removeWidget(card)
            card.deleteLater()
        self.cosigner_rows.clear()

        for i in range(2, n + 1):
            self._add_cosigner_row(i)

        self.continue_button.setEnabled(False)
        self._threshold_locked = True
        self.required_signer_input.setEnabled(False)
        self.total_signer_input.setEnabled(False)
        self._update_summary()
        self._update_continue_enabled()
        return True

    # ------------------------------------------------------------------ #
    #  Step navigation                                                     #
    # ------------------------------------------------------------------ #

    def _go_next(self):
        self.continue_button.setEnabled(False)
        if self._current_step == 1:
            if not self._on_confirm_threshold():
                self._update_continue_enabled()
                return

            self.threshold_frame.hide()
            self.creator_frame.hide()
            self.back_button.show()
            self.close_btn.hide()

            if self._is_watch_only:
                self._configure_watch_only_review_fields()
                self.review_frame.show()
                self.cos_frame.hide()
                self._current_step = 2
                self.card.setMinimumSize(QSize(770, 570))
                self.card.setMaximumSize(QSize(770, 570))
                self._update_continue_enabled()
                self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next'))
            else:
                self._populate_wallet_review_fields()
                self.review_frame.show()
                self.cos_frame.hide()
                self._current_step = 2
                self.export_button.show()
                self.card.setMinimumSize(QSize(770, 570))
                self.card.setMaximumSize(QSize(770, 570))
                self._update_continue_enabled()
                self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next'))

        elif self._current_step == 2:
            if self._is_watch_only:
                if not self._save_watch_only_review_fields():
                    self._update_continue_enabled()
                    return
                self.review_frame.hide()
                self.cos_frame.show()
                if hasattr(self, 'reset_button'):
                    self.footer.replaceWidget(self.reset_button, self.export_button)
                    self.reset_button.deleteLater()
                    del self.reset_button
                self.export_button.hide()
                self._current_step = 3
            else:
                self.review_frame.hide()
                self.cos_frame.show()
                self.export_button.hide()
                self._current_step = 3

            total_signer = self._get_total_signer()
            if total_signer > 2:
                self.card.setMinimumSize(QSize(770, 640))
                self.card.setMaximumSize(QSize(770, 640))
            else:
                self.card.setMinimumSize(QSize(770, 520))
                self.card.setMaximumSize(QSize(770, 520))
            self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue'))
            self._update_continue_enabled()

        elif self._current_step == 3:
            if not self._save_cosigners_data():
                self._update_continue_enabled()
                return
            self._view_model.page_navigation.welcome_page()

    def _go_back(self):
        if self._current_step == 2:
            self.required_signer_input.setEnabled(True)
            self.total_signer_input.setEnabled(True)
            self.cos_frame.hide()
            self.review_frame.hide()
            self.threshold_frame.show()
            self.creator_frame.hide()
            self.back_button.hide()
            self.export_button.hide()
            self._current_step = 1
            self.card.setMinimumSize(QSize(770, 530))
            self.card.setMaximumSize(QSize(770, 530))
            self._update_summary()
            self._update_continue_enabled()
            self.close_btn.show()
            SettingRepository.set_multisig_config(None, None)
            self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next'))
        elif self._current_step == 3:
            self.cos_frame.hide()
            self.review_frame.show()
            self.export_button.show()
            self._current_step = 2
            self.card.setMinimumSize(QSize(770, 570))
            self.card.setMaximumSize(QSize(770, 570))
            self._update_continue_enabled()
            self.continue_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next'))

    # ------------------------------------------------------------------ #
    #  Watch-only helpers                                                  #
    # ------------------------------------------------------------------ #

    def _configure_watch_only_review_fields(self):
        self._populate_wallet_review_fields()
        self.export_button.hide()
        self.fp_value_widget.clear()
        self.keychain_value_widget.clear()
        self.xpub_vanilla_value_widget.clear()
        self.xpub_colored_value_widget.clear()
        self.cosigner_string_value_widget.clear()
        self.r_v.removeItem(self.row1)
        self.r_v.removeItem(self.row2)
        self.r_v.removeItem(self.row3)
        self.r_v.removeItem(self.row5)
        self.r_v.addLayout(self.row5)
        self.r_v.addLayout(self.row1)
        self.r_v.addLayout(self.row2)
        self.r_v.addLayout(self.row3)
        self.cosigner_string_value_widget.setReadOnly(False)
        if hasattr(self, 'cosigner_string_copy_btn'):
            self.cosigner_string_copy_btn.hide()
        self.reset_button = SecondaryButton()
        self.reset_button.setIcon(QIcon(':/assets/x_cross.png'))
        self.reset_button.setIconSize(QSize(18, 18))
        self.reset_button.setLayoutDirection(Qt.RightToLeft)
        self.reset_button.setFixedSize(QSize(100, 36))
        self.reset_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reset_button.setText(QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'reset') + ' ')
        self.reset_button.clicked.connect(self._on_watch_only_reset_clicked)
        self.footer.replaceWidget(self.export_button, self.reset_button)
        self.export_button.hide()
        self.cosigner_string_value_widget.textChanged.connect(self._on_watch_only_cosigner_string_changed)

    def _on_watch_only_reset_clicked(self):
        self.fp_value_widget.clear()
        self.keychain_value_widget.clear()
        self.xpub_vanilla_value_widget.clear()
        self.xpub_colored_value_widget.clear()
        self.cosigner_string_value_widget.clear()
        self._update_continue_enabled()

    def _on_watch_only_cosigner_string_changed(self, text):
        text = text.strip()
        if not text:
            self.fp_value_widget.clear()
            self.keychain_value_widget.clear()
            self.xpub_vanilla_value_widget.clear()
            self.xpub_colored_value_widget.clear()
            self._update_continue_enabled()
            return
        try:
            data = Cosigner(text).cosigner_data()
            self.fp_value_widget.setText(data.master_fingerprint)
            val = data.vanilla_keychain
            self.keychain_value_widget.setText(str(val) if val is not None else '')
            self.xpub_vanilla_value_widget.setText(data.account_xpub_vanilla)
            self.xpub_colored_value_widget.setText(data.account_xpub_colored)
            self._update_continue_enabled()
        except Exception:
            self.fp_value_widget.clear()
            self.keychain_value_widget.clear()
            self.xpub_vanilla_value_widget.clear()
            self.xpub_colored_value_widget.clear()
            self._update_continue_enabled()

    def _save_watch_only_review_fields(self) -> bool:
        fp = self.fp_value_widget.text().strip()
        keychain = self.keychain_value_widget.text().strip()
        vanilla = self.xpub_vanilla_value_widget.text().strip()
        colored = self.xpub_colored_value_widget.text().strip()
        if not fp or not vanilla or not colored:
            return False
        local_store.set_value(MASTER_FINGERPRINT, fp)
        local_store.set_value(VANILLA_KEYCHAIN, int(keychain) if keychain.isdigit() else 0)
        local_store.set_value(ACCOUNT_XPUB_VANILLA, vanilla)
        local_store.set_value(ACCOUNT_XPUB_COLORED, colored)
        return True

    # ------------------------------------------------------------------ #
    #  Review-frame population                                             #
    # ------------------------------------------------------------------ #

    def _populate_wallet_review_fields(self):
        master_fp = local_store.get_value(MASTER_FINGERPRINT)
        account_xpub_vanilla = local_store.get_value(ACCOUNT_XPUB_VANILLA)
        account_xpub_colored = local_store.get_value(ACCOUNT_XPUB_COLORED)
        derivation_path = "m/48'/0'/0'/2'"
        keychain = local_store.get_value(VANILLA_KEYCHAIN)
        keychain_str = str(keychain) if keychain is not None else '0'

        self.fp_value_widget.setText(master_fp)
        self.keychain_value_widget.setText(keychain_str)
        self.path_value_widget.setText(derivation_path)
        self.xpub_vanilla_value_widget.setText(self._truncate_text(account_xpub_vanilla))
        self.xpub_colored_value_widget.setText(self._truncate_text(account_xpub_colored))

        if not self._is_watch_only:
            if master_fp and account_xpub_vanilla and account_xpub_colored:
                try:
                    keychain_val = int(keychain) if keychain is not None else 0
                    data = CosignerData(
                        master_fingerprint=master_fp,
                        account_xpub_vanilla=account_xpub_vanilla,
                        account_xpub_colored=account_xpub_colored,
                        vanilla_keychain=keychain_val,
                    )
                    cosigner_str = Cosigner.from_data(data).cosigner_string()
                    self.cosigner_string_value_widget.setText(cosigner_str)
                    self.cosigner_string_value_widget.setCursorPosition(0)
                    self.cosigner_string_copy_btn.clicked.connect(lambda: copy_text(cosigner_str))
                    self.xpub_colored_copy_btn.clicked.connect(lambda: copy_text(account_xpub_colored))
                except Exception as e:
                    logger.error('Failed to generate cosigner string: %s', e)
                    self.cosigner_string_value_widget.setText('Error generating string')
            else:
                self.cosigner_string_value_widget.setText('Incomplete signer data')

    # ------------------------------------------------------------------ #
    #  Cosigner helpers                                                    #
    # ------------------------------------------------------------------ #

    def _add_cosigner_row(self, index: int):
        card = CosignerDetailCard(index, self)
        if self._get_total_signer() == 2:
            card.set_collapsible(False)
        if card.import_btn:
            card.import_btn.clicked.connect(lambda: self._import_cosigner_from_file(card))
        if card.reset_btn:
            card.reset_btn.clicked.connect(card.string_input.clear)
        if card.string_input:
            card.string_input.textChanged.connect(lambda text, c=card: self._on_cosigner_string_changed(text, c))
        self.cosigner_rows.append(card)
        self.cosigners_v.insertWidget(self.cosigners_v.count() - 1, card)
        if index == 2 and card.string_input:
            card.string_input.setFocus()

    def _on_cosigner_string_changed(self, text, row_w):
        row_w.string_input.setCursorPosition(0)
        text = text.strip()
        if not text:
            row_w.fp_input.clear()
            row_w.vanilla_xpub_input.clear()
            row_w.colored_xpub_input.clear()
            row_w.keychain_input.clear()
            row_w.string_input.setReadOnly(False)
            row_w.import_btn.setVisible(True)
            row_w.reset_btn.setVisible(False)
            self._update_continue_enabled()
            return
        try:
            data = Cosigner(text).cosigner_data()
            row_w.fp_input.setText(data.master_fingerprint)
            row_w.vanilla_xpub_input.setText(self._truncate_text(data.account_xpub_vanilla))
            row_w.vanilla_xpub_str = data.account_xpub_vanilla
            row_w.colored_xpub_input.setText(self._truncate_text(data.account_xpub_colored))
            row_w.colored_xpub_str = data.account_xpub_colored
            val = data.vanilla_keychain
            row_w.keychain_input.setText(str(val) if val is not None else '0')
            self._update_continue_enabled()
            row_w.string_input.setReadOnly(True)
            row_w.import_btn.setVisible(False)
            row_w.reset_btn.setVisible(True)
        except Exception:
            row_w.fp_input.clear()
            row_w.vanilla_xpub_input.clear()
            row_w.colored_xpub_input.clear()
            row_w.keychain_input.clear()
            row_w.string_input.setReadOnly(False)
            row_w.import_btn.setVisible(True)
            row_w.reset_btn.setVisible(False)
            self._update_continue_enabled()

    def _restore_cosigner_inputs(self, cosigners_data: list[dict]):
        if not self._threshold_locked:
            self._on_confirm_threshold()
        for data in cosigners_data:
            idx = data.get('index')
            if not idx:
                continue
            target_card = next((c for c in self.cosigner_rows if c.index == idx), None)
            if target_card:
                if MASTER_FINGERPRINT in data:
                    target_card.fp_input.setText(data[MASTER_FINGERPRINT])
                if VANILLA_KEYCHAIN in data:
                    val = data[VANILLA_KEYCHAIN]
                    target_card.keychain_input.setText(str(val) if val is not None else '0')
                if ACCOUNT_XPUB_VANILLA in data:
                    target_card.vanilla_xpub_input.setText(self._truncate_text(data[ACCOUNT_XPUB_VANILLA]))
                    target_card.vanilla_xpub_str = data[ACCOUNT_XPUB_VANILLA]
                if ACCOUNT_XPUB_COLORED in data:
                    target_card.colored_xpub_input.setText(self._truncate_text(data[ACCOUNT_XPUB_COLORED]))
                    target_card.colored_xpub_str = data[ACCOUNT_XPUB_COLORED]
        self.required_signer_input.setEnabled(False)
        self.total_signer_input.setEnabled(False)

    def _save_cosigners_data(self) -> bool:
        cosigners_data = []
        for card in self.cosigner_rows:
            card.clear_error()
            cosigner_string = card.string_input.text().strip()
            if not cosigner_string:
                card.show_error('Cosigner details required')
                return False
            try:
                data = Cosigner(cosigner_string).cosigner_data()
            except Exception:
                card.show_error('Invalid cosigner details')
                return False
            keychain = None
            if data.vanilla_keychain and data.vanilla_keychain.isdigit():
                keychain = int(data.vanilla_keychain)
            cosigners_data.append({
                'index': card.index,
                MASTER_FINGERPRINT: data.master_fingerprint,
                ACCOUNT_XPUB_VANILLA: data.account_xpub_vanilla,
                ACCOUNT_XPUB_COLORED: data.account_xpub_colored,
                VANILLA_KEYCHAIN: keychain,
            })
        SettingRepository.set_cosigners(cosigners_data)
        return True

    # ------------------------------------------------------------------ #
    #  Validation helpers                                                  #
    # ------------------------------------------------------------------ #

    def _get_required_signer(self) -> int:
        try:
            return int(self.required_signer_input.text())
        except Exception:
            return 0

    def _get_total_signer(self) -> int:
        try:
            return int(self.total_signer_input.text())
        except Exception:
            return 0

    def _update_continue_enabled(self):
        if self._current_step == 1:
            n = self._get_total_signer()
            m = self._get_required_signer()
            self.continue_button.setEnabled((2 <= n <= 15) and (2 <= m <= n))
            return

        if self.cos_frame.isVisible():
            n = self._get_total_signer()
            n_rows = len(self.cosigner_rows)
            all_filled = all_valid = True
            any_duplicates = False
            seen = set()
            for card in self.cosigner_rows:
                card.clear_error()
                xpub_str = card.vanilla_xpub_str
                if xpub_str:
                    if xpub_str in seen:
                        card.show_error('Duplicate Cosigner')
                        any_duplicates = True
                        all_valid = False
                    else:
                        seen.add(xpub_str)
                else:
                    all_filled = False
                    if card.string_input.text().strip():
                        card.show_error('Invalid cosigner details')
                        all_valid = False
            self.continue_button.setEnabled(
                all_filled and all_valid and not any_duplicates and n_rows == n - 1,
            )
        else:
            self.continue_button.setEnabled(True)

    def _update_summary(self):
        n = self._get_total_signer()
        m = self._get_required_signer()
        self.total_signer_input.setValidator(QIntValidator(2, 15, self))
        max_m = max(2, min(n, 15))
        self.required_signer_input.setValidator(QIntValidator(2, max_m, self))
        self.required_signer_help.setText(
            QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'minimum_signatures_needed').format(max_m),
        )
        m_disp = m if m >= 1 else 0
        n_disp = n if n >= 1 else 0
        if self.summary_text is not None:
            self.summary_text.setText(
                QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'configuration_note').format(m_disp, n_disp),
            )

    def _truncate_text(self, text: str) -> str:
        if text and len(text) > 40:
            return text[:25] + '...' + text[-25:]
        return text

    # ------------------------------------------------------------------ #
    #  File I/O                                                            #
    # ------------------------------------------------------------------ #

    def _export_cosigner_to_file(self):
        download_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Cosigner Data',
            os.path.join(download_dir, 'cosigner.txt'),
            'Text Files (*.txt);;All Files (*)',
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.cosigner_string_value_widget.text())
                ToastManager.success(description='Cosigner data exported successfully!', parent=self)
            except Exception as e:
                logger.error('Failed to export cosigner data: %s', e)
                ToastManager.error(description=f'Failed to export cosigner data: {e}', parent=self)

    def _import_cosigner_from_file(self, target_card):
        downloads_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import Cosigner Data', downloads_dir,
            'Text Files (*.txt);;All Files (*)',
        )
        if file_path:
            try:
                with open(file_path, encoding='utf-8') as f:
                    cosigner_string = f.read().strip()
                target_card.string_input.setText(cosigner_string)
                if not target_card.is_expanded:
                    target_card.toggle_content()
                ToastManager.success(description='Cosigner data imported successfully!', parent=self)
            except Exception as e:
                logger.error('Failed to import cosigner data: %s', e)
                ToastManager.error(description=f'Failed to import cosigner data: {e}', parent=self)
