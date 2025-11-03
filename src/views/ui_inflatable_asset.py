# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the InflatableAssetWidget class,
which represents the UI for inflatable assets.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QRect
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QImage
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QScrollArea
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget
from rgb_lib import AssetSchema

import src.resources_rc
from accessible_constant import FUNGIBLES_SCROLL_WIDGETS
from accessible_constant import ISSUE_NIA_ASSET
from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import DraftAsset
from src.model.rgb_model import RgbAssetPageLoadModel
from src.utils.clickable_frame import ClickableFrame
from src.utils.common_utils import format_epoch_time
from src.utils.common_utils import generate_identicon
from src.utils.common_utils import get_current_wallet_mode_config
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.utils.render_timer import RenderTimer
from src.utils.worker import ThreadManager
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.header_frame import HeaderFrame
from src.views.components.loading_screen import LoadingTranslucentScreen
from src.views.components.toast import ToastManager


class InflatableAssetWidget(QWidget, ThreadManager):
    """This class represents all the UI elements of the inflatable page."""
    _native_auth_finished: bool = False

    def __init__(self, view_model):
        self.render_timer = RenderTimer(
            task_name='InflatableAssetWidget Rendering',
        )
        self.render_timer.start()
        super().__init__()
        self._view_model: MainViewModel = view_model
        self._view_model.main_asset_view_model.asset_loaded.connect(
            self.show_inflatables_assets,
        )
        self.network: NetworkEnumModel = SettingRepository.get_wallet_network()
        self.__loading_translucent_screen = None
        self.sidebar = None
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/fungible_asset_style.qss',
            ),
        )
        self.setObjectName('my_assets_page')
        self.vertical_layout_inflatable_1 = QVBoxLayout(self)
        self.vertical_layout_inflatable_1.setObjectName(
            'vertical_layout_fungible_1',
        )
        self.vertical_layout_inflatable_1.setContentsMargins(0, 0, 0, 0)
        self.inflatable_widget = QWidget(self)
        self.inflatable_widget.setObjectName('widget_2')
        self.vertical_layout_inflatable_2 = QVBoxLayout(self.inflatable_widget)
        self.vertical_layout_inflatable_2.setObjectName('vertical_layout_2')
        self.vertical_layout_inflatable_2.setContentsMargins(25, 12, 25, 0)
        self.inflatables_header_title_frame = HeaderFrame(
            title_logo_path=':/assets/my_asset.png', title_name='inflatables',
        )
        self.inflatables_header_title_frame.action_button.setAccessibleName(
            ISSUE_NIA_ASSET,
        )
        config = get_current_wallet_mode_config()
        self.is_watch_only = SettingRepository.get_wallet_access_type(
        ) == WalletAccessType.WATCH_ONLY
        self.is_offline_wallet = SettingRepository.get_wallet_type(
        ) == WalletType.OFFLINE_TYPE_WALLET
        self.priv = config.privileges
        self.vertical_layout_inflatable_frame = None
        self.grid_layout_inflatable_frame = None
        self.inflatables_asset_logo = None
        self.inflatables_asset_name = None
        self.inflatables_address = None
        self.inflatables_amount = None
        self.inflatables_token_symbol = None
        self.inflatables_vertical_layout_4 = None
        self.inflatables_image_label = None
        self.inflatables_horizontal_spacer = None
        self.inflatables_vertical_spacer_scroll_area = None
        self.inflatables_header_frame = None
        self.inflatables_header_layout = None
        self.inflatables_logo_header = None
        self.inflatables_name_header = None
        self.inflatables_address_header = None
        self.inflatables_amount_header = None
        self.inflatables_symbol_header = None
        self.inflatables_outbound_balance = None

        self.vertical_layout_inflatable_2.addWidget(
            self.inflatables_header_title_frame,
        )

        self.inflatable_label = QLabel(self.inflatable_widget)
        self.inflatable_label.setObjectName('fungibles_label')
        self.inflatable_label.setMinimumSize(QSize(1016, 57))

        self.usb_last_sync_horizontal_layout = QHBoxLayout()
        self.usb_last_sync_horizontal_layout.setContentsMargins(0, 0, 12, 0)

        self.usb_last_sync_inflatable_info_label = QLabel()
        self.usb_last_sync_inflatable_info_label.setObjectName(
            'usb_last_sync_info_label',
        )
        self.outdated_inflatable_balance_label = QLabel()
        self.outdated_inflatable_balance_label.setObjectName(
            'outdated_balance_label',
        )

        self.usb_last_sync_horizontal_layout.addWidget(
            self.usb_last_sync_inflatable_info_label,
        )
        if self.is_offline_wallet:
            self.usb_last_sync_horizontal_layout.addWidget(
                self.outdated_inflatable_balance_label,
            )

        self.inflatables_horizontal_spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.addWidget(self.inflatable_label)
        self.horizontal_layout.addSpacerItem(
            self.inflatables_horizontal_spacer,
        )
        if self.is_offline_wallet or self.is_watch_only:
            self.horizontal_layout.addLayout(
                self.usb_last_sync_horizontal_layout,
            )

        self.vertical_layout_inflatable_2.addLayout(self.horizontal_layout)

        self.scroll_area_inflatable = QScrollArea(self.inflatable_widget)
        self.scroll_area_inflatable.setObjectName('scroll_area_1')
        self.scroll_area_inflatable.setWidgetResizable(True)
        self.scroll_area_inflatable.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        self.scroll_area_inflatable.setStyleSheet(
            load_stylesheet('views/qss/scrollbar.qss'),
        )
        self.scroll_area_inflatable.setMinimumHeight(320)
        self.scroll_area_widget_inflatable = QWidget()
        self.scroll_area_widget_inflatable.setObjectName(
            'scrollAreaWidgetContents_2',
        )
        self.scroll_area_widget_inflatable.setAccessibleName(
            FUNGIBLES_SCROLL_WIDGETS,
        )
        self.scroll_area_widget_inflatable.setGeometry(QRect(0, 0, 1182, 2000))
        self.scroll_area_widget_inflatable.setContentsMargins(0, -1, 10, -1)

        self.scroll_area_widget_inflatable.setMaximumSize(
            QSize(16777215, 2000),
        )
        self.inflatables_vertical_layout_scroll_content = QVBoxLayout(
            self.scroll_area_widget_inflatable,
        )
        self.inflatables_vertical_layout_scroll_content.setObjectName(
            'verticalLayout_2',
        )
        self.inflatables_vertical_layout_scroll_content.setContentsMargins(
            0, -1, 0, -1,
        )
        self.inflatables_vertical_layout_3 = QVBoxLayout()
        self.inflatables_vertical_layout_3.setSpacing(10)
        self.inflatables_vertical_layout_3.setObjectName('verticalLayout_3')

        self.inflatable_frame = QFrame(self.scroll_area_widget_inflatable)

        self.inflatables_vertical_layout_scroll_content.addLayout(
            self.inflatables_vertical_layout_3,
        )

        self.scroll_area_inflatable.setWidget(
            self.scroll_area_widget_inflatable,
        )

        self.vertical_layout_inflatable_2.addWidget(
            self.scroll_area_inflatable,
        )
        self.inflatables_horizontal_layout_2 = QHBoxLayout()
        self.inflatables_horizontal_layout_2.setSpacing(6)

        self.inflatables_horizontal_layout_2.setObjectName(
            'horizontalLayout_2',
        )
        self.inflatables_horizontal_layout_2.setContentsMargins(1, -1, 1, -1)

        self.vertical_layout_inflatable_1.addWidget(self.inflatable_widget)
        self.inflatable_frame_card = QFrame(self.inflatable_widget)
        self.inflatable_frame_card.setObjectName('fungibles_frame_card')

        self.inflatable_frame_card.setFrameShape(QFrame.StyledPanel)
        self.inflatable_frame_card.setFrameShadow(QFrame.Raised)

        self.inflatables_horizontal_layout_2.addWidget(
            self.inflatable_frame_card,
        )

        self.vertical_layout_inflatable_2.addLayout(
            self.inflatables_horizontal_layout_2,
        )
        self.retranslate_ui()
        self.setup_ui_connection()

    def show_inflatables_assets(self):
        """This method creates all the inflatable assets elements of the main asset page."""
        for i in reversed(range(self.inflatables_vertical_layout_3.count())):
            widget = self.inflatables_vertical_layout_3.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.inflatables_header_frame = QFrame(
            self.scroll_area_widget_inflatable,
        )
        self.inflatables_header_frame.setObjectName('header_frame')
        self.inflatables_header_frame.setMinimumSize(QSize(900, 70))
        self.inflatables_header_frame.setMaximumSize(QSize(16777215, 70))
        self.inflatables_header_layout = QGridLayout(
            self.inflatables_header_frame,
        )
        self.inflatables_header_layout.setContentsMargins(20, 6, 20, 6)

        self.inflatables_logo_header = QLabel(self.inflatables_header_frame)
        self.inflatables_logo_header.setObjectName('logo_header')
        self.inflatables_logo_header.setMinimumSize(QSize(40, 40))
        self.inflatables_logo_header.setMaximumSize(QSize(40, 40))
        self.inflatables_header_layout.addWidget(
            self.inflatables_logo_header, 0, 1,
        )

        self.inflatables_name_header = QLabel(self.inflatables_header_frame)
        self.inflatables_name_header.setObjectName('name_header')
        self.inflatables_name_header.setMinimumSize(QSize(130, 40))
        self.inflatables_header_layout.addWidget(
            self.inflatables_name_header, 0, 0, Qt.AlignLeft,
        )

        self.inflatables_address_header = QLabel(self.inflatables_header_frame)
        self.inflatables_address_header.setObjectName('address_header')
        self.inflatables_address_header.setMinimumSize(QSize(600, 0))
        self.inflatables_address_header.setMaximumSize(
            QSize(16777215, 16777215),
        )
        self.inflatables_header_layout.addWidget(
            self.inflatables_address_header, 0, 2, Qt.AlignLeft,
        )
        self.inflatables_address_header.setStyleSheet(
            'padding-left: 10px;',
        )

        self.inflatables_amount_header = QLabel(self.inflatables_header_frame)
        self.inflatables_amount_header.setObjectName('amount_header')
        self.inflatables_amount_header.setWordWrap(True)
        self.inflatables_amount_header.setMinimumSize(QSize(98, 40))
        self.inflatables_header_layout.addWidget(
            self.inflatables_amount_header, 0, 3, Qt.AlignLeft,
        )

        self.inflatables_symbol_header = QLabel(self.inflatables_header_frame)
        self.inflatables_symbol_header.setObjectName('symbol_header')
        self.inflatables_header_layout.addWidget(
            self.inflatables_symbol_header, 0, 5, Qt.AlignLeft,
        )

        self.inflatables_vertical_layout_3.addWidget(
            self.inflatables_header_frame,
        )

        inflatables_wallet_service = WalletDataService.get_session()
        inflatables_draft_assets = (
            inflatables_wallet_service.list_draft_issue_assets(
            ) if inflatables_wallet_service is not None else []
        )
        for d in inflatables_draft_assets:
            if d.get('file_path'):
                continue
            inflatables_draft_asset = DraftAsset(
                draft_id=d.get('id'),
                asset_id='draft_asset',
                name=f"{d.get('name')} (Draft)",
                ticker=d.get('ticker'),
            )
            if self.is_watch_only:
                self.create_inflatable_card(inflatables_draft_asset)

        for asset in self._view_model.main_asset_view_model.assets.ifa:
            self.create_inflatable_card(asset)
        self.inflatables_vertical_spacer_scroll_area = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )
        self.inflatables_vertical_layout_scroll_content.addItem(
            self.inflatables_vertical_spacer_scroll_area,
        )
        self.inflatables_name_header.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_name', None,
            ),
        )
        self.inflatables_address_header.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_id', None,
            ),
        )
        self.inflatables_amount_header.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'on_chain_balance', None,
            ),
        )
        self.inflatables_symbol_header.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'symbol_header', None,
            ),
        )

    def create_inflatable_card(self, asset, img_path=None):
        """This method creates all the inflatable assets elements of the main asset page."""
        self.inflatable_frame = ClickableFrame(
            asset.asset_id, asset.name, self.inflatable_widget, asset_type=AssetSchema.IFA,
        )
        self.inflatable_frame.setStyleSheet(
            load_stylesheet('views/qss/fungible_asset_style.qss'),
        )

        self.inflatable_frame.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.inflatable_frame.setObjectName('frame_4')
        self.inflatable_frame.setMinimumSize(QSize(900, 70))
        self.inflatable_frame.setMaximumSize(QSize(16777215, 70))

        self.inflatable_frame.setFrameShape(QFrame.StyledPanel)
        self.inflatable_frame.setFrameShadow(QFrame.Raised)
        self.vertical_layout_inflatable_frame = QVBoxLayout(
            self.inflatable_frame,
        )
        self.vertical_layout_inflatable_frame.setObjectName(
            'vertical_layout_16',
        )
        self.grid_layout_inflatable_frame = QGridLayout()
        self.grid_layout_inflatable_frame.setObjectName(
            'horizontal_layout_7',
        )
        self.grid_layout_inflatable_frame.setContentsMargins(6, 0, 6, 0)
        self.inflatables_asset_logo = QLabel(self.inflatable_frame)
        self.inflatables_asset_logo.setObjectName('asset_logo')

        self.inflatables_asset_logo.setMinimumSize(QSize(40, 40))
        self.inflatables_asset_logo.setMaximumSize(QSize(40, 40))

        if img_path:
            self.inflatables_asset_logo.setPixmap(QPixmap(img_path))

        else:
            img_str = generate_identicon(asset.asset_id)
            image = QImage.fromData(QByteArray.fromBase64(img_str.encode()))
            pixmap = QPixmap.fromImage(image)
            self.inflatables_asset_logo.setPixmap(pixmap)

        self.grid_layout_inflatable_frame.addWidget(
            self.inflatables_asset_logo, 0, 0,
        )

        self.inflatables_asset_name = QLabel(self.inflatable_frame)
        self.inflatables_asset_name.setObjectName('asset_name')
        self.inflatables_asset_name.setMinimumSize(QSize(135, 40))
        self.inflatables_asset_name.setStyleSheet(
            load_stylesheet(
                'views/qss/fungible_asset_style.qss',
            ),
        )
        self.inflatables_asset_name.setText(asset.name)
        self.grid_layout_inflatable_frame.addWidget(
            self.inflatables_asset_name, 0, 1,
        )

        self.inflatables_address = QLabel(self.inflatable_frame)
        self.inflatables_address.setObjectName('address')
        self.inflatables_address.setMinimumSize(QSize(600, 0))
        self.inflatables_address.setMaximumSize(QSize(16777215, 16777215))
        self.inflatables_address.setStyleSheet(
            'padding-left:10px;',
        )

        if asset.asset_id == 'draft_asset':
            self.inflatables_address.setText('Click to continue issuance')
        else:
            self.inflatables_address.setText(asset.asset_id)

        self.grid_layout_inflatable_frame.addWidget(
            self.inflatables_address, 0, 2, Qt.AlignLeft,
        )

        self.inflatables_amount = QLabel(self.inflatable_frame)
        self.inflatables_amount.setObjectName('amount')
        self.inflatables_amount.setMinimumSize(QSize(100, 40))

        if asset.asset_id == 'draft_asset':
            self.inflatables_amount.setText('-')
        else:
            self.inflatables_amount.setText(str(asset.balance.future))
        self.grid_layout_inflatable_frame.addWidget(
            self.inflatables_amount, 0, 3, Qt.AlignLeft,
        )

        self.inflatables_token_symbol = QLabel(self.inflatable_frame)
        self.inflatables_token_symbol.setObjectName('token_symbol')

        self.inflatables_token_symbol.setText(asset.ticker)
        self.grid_layout_inflatable_frame.addWidget(
            self.inflatables_token_symbol, 0, 5, Qt.AlignLeft,
        )

        self.vertical_layout_inflatable_frame.addLayout(
            self.grid_layout_inflatable_frame,
        )

        self.inflatables_vertical_layout_3.addWidget(self.inflatable_frame)
        if asset.asset_id == 'draft_asset':
            draft_id = asset.draft_id
            self.inflatable_frame.clicked.connect(
                lambda: self._view_model.page_navigation.issue_ifa_page(
                    draft_id, from_draft=True,
                ),
            )
        else:
            self.inflatable_frame.clicked.connect(
                self.handle_asset_frame_click,
            )

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self._view_model.main_asset_view_model.get_assets()
        self.inflatables_header_title_frame.refresh_page_button.clicked.connect(
            self.refresh_inflatables_asset,
        )
        self.inflatables_header_title_frame.action_button.clicked.connect(
            lambda: self._view_model.main_asset_view_model.navigate_issue_asset(
                self._view_model.page_navigation.issue_ifa_page,
            ),
        )
        self._view_model.main_asset_view_model.loading_started.connect(
            self.show_inflatable_loading_screen,
        )
        self._view_model.main_asset_view_model.loading_finished.connect(
            self.stop_inflatable_loading_screen,
        )
        self._view_model.main_asset_view_model.message.connect(
            self.show_message,
        )

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.show_inflatable_loading_screen()
        self.inflatable_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'inflatables', None,
            ),
        )

        epoch_time = format_epoch_time()
        if epoch_time is not None:
            self.usb_last_sync_inflatable_info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_info_label',
                ).format(epoch_time),
            )
            self.outdated_inflatable_balance_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'outdated_balance_label',
                ),
            )

    def refresh_inflatables_asset(self):
        """This method start the render timer and perform the inflatable asset list refresh"""
        self.render_timer.start()
        self._view_model.main_asset_view_model.get_assets(
            rgb_asset_hard_refresh=True,
        )
        inflatables_epoch_time = format_epoch_time()
        if inflatables_epoch_time is not None:
            self.usb_last_sync_inflatable_info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_info_label', None,
                ).format(inflatables_epoch_time),
            )
            self.outdated_inflatable_balance_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'outdated_balance_label', None,
                ),
            )

    def handle_asset_frame_click(self, asset_id, asset_name, image_path, asset_type):
        """This method handles inflatable asset click of the main asset page."""
        self._view_model.cfa_view_model.asset_info.emit(
            asset_id, asset_name, image_path, asset_type,
        )
        self._view_model.page_navigation.cfa_detail_page(
            RgbAssetPageLoadModel(
                asset_type=asset_type,
                is_secondary_issuance=True,
            ),
        )

    def show_inflatable_loading_screen(self):
        """This method handled show loading screen on main asset page"""
        self.__loading_translucent_screen = LoadingTranslucentScreen(
            parent=self, description_text='Loading', dot_animation=True,
        )
        self.__loading_translucent_screen.start()
        self.inflatables_header_title_frame.refresh_page_button.setDisabled(
            True,
        )

    def stop_inflatable_loading_screen(self):
        """This method handled stop loading screen on main asset page"""
        self.render_timer.stop()
        self.__loading_translucent_screen.stop()
        self.inflatables_header_title_frame.refresh_page_button.setDisabled(
            False,
        )

    def show_message(self, inflatable_asset_toast_preset, message):
        """This method handled showing message main asset page"""
        if inflatable_asset_toast_preset == ToastPreset.SUCCESS:
            ToastManager.success(description=message)
        if inflatable_asset_toast_preset == ToastPreset.ERROR:
            ToastManager.error(description=message)
        if inflatable_asset_toast_preset == ToastPreset.INFORMATION:
            ToastManager.info(description=message)
        if inflatable_asset_toast_preset == ToastPreset.WARNING:
            ToastManager.warning(description=message)
