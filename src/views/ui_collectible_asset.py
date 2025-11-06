# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the CollectiblesAssetWidget class,
which represents the UI for collectibles assets.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFormLayout
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
from accessible_constant import ISSUE_CFA_ASSET
from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import RgbAssetPageLoadModel
from src.utils.clickable_frame import ClickableFrame
from src.utils.common_utils import format_epoch_time
from src.utils.common_utils import resize_image
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.header_frame import HeaderFrame
from src.views.components.loading_screen import LoadingTranslucentScreen
from src.views.components.toast import ToastManager


class CollectiblesAssetWidget(QWidget):
    """This class represents all the UI elements of the collectibles asset page."""

    def __init__(self, view_model):
        self.render_timer = RenderTimer(
            task_name='CollectiblesAssetWidget Rendering',
        )
        self.render_timer.start()
        super().__init__()
        self._view_model: MainViewModel = view_model
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/collectible_asset_style.qss',
            ),
        )
        self.num_columns = None
        self._view_model.main_asset_view_model.asset_loaded.connect(
            self.create_collectibles_frames,
        )

        self.setObjectName('collectibles_page')
        self.loading_screen = None
        self.grid_layout_widget = None
        self.frames = None
        self.total_items = None
        self.vertical_layout_collectibles = QVBoxLayout(self)
        self.vertical_layout_collectibles.setObjectName(
            'vertical_layout_collectibles',
        )
        self.vertical_layout_collectibles.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self)
        self.widget.setObjectName('collectibles_widget')

        self.vertical_layout_2 = QVBoxLayout(self.widget)
        self.vertical_layout_2.setObjectName('vertical_layout_2')
        self.vertical_layout_2.setContentsMargins(25, 12, 25, 0)
        self.asset_name = None
        self.collectibles_frame = None
        self.collectible_frame_grid_layout = None
        self.collectible_asset_name = None
        self.image_label = None
        self.horizontal_spacer = None
        self.vertical_spacer_scroll_area = None

        self.collectible_header_frame = HeaderFrame(
            title_name='collectibles', title_logo_path=':/assets/my_asset.png',
        )
        self.collectible_header_frame.action_button.setAccessibleName(
            ISSUE_CFA_ASSET,
        )
        # Start hidden until we confirm issued assets exist (use header API to lock)
        self.issue_button_in_header = False
        self.collectible_header_frame.set_action_button_visible(
            False, override=True,
        )
        self.vertical_layout_2.addWidget(self.collectible_header_frame)

        self.collectibles_label = QLabel(self.widget)
        self.collectibles_label.setObjectName('collectibles_label')
        self.collectibles_label.setMinimumSize(QSize(1016, 50))
        self.collectibles_label.setMaximumSize(QSize(1016, 50))

        self.usb_last_sync_collectible_horizontal_layout = QHBoxLayout()
        self.usb_last_sync_collectible_horizontal_layout.setContentsMargins(
            0, 0, 12, 0,
        )

        self.usb_last_sync_collectible_info_label = QLabel()
        self.usb_last_sync_collectible_info_label.setObjectName(
            'usb_last_sync_collectible_info_label',
        )
        self.outdated_collectible_balance_label = QLabel()
        self.outdated_collectible_balance_label.setObjectName(
            'outdated_balance_label',
        )

        self.usb_last_sync_collectible_horizontal_layout.addWidget(
            self.usb_last_sync_collectible_info_label,
        )

        self.is_watch_only = SettingRepository.get_wallet_access_type(
        ) == WalletAccessType.WATCH_ONLY
        self.is_offline_wallet = SettingRepository.get_wallet_type(
        ) == WalletType.OFFLINE_TYPE_WALLET

        self.horizontal_spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self._top_row_layout = QHBoxLayout()
        self._top_row_layout.addWidget(self.collectibles_label)
        self._top_row_layout.addSpacerItem(self.horizontal_spacer)
        if self.is_offline_wallet:
            self.usb_last_sync_collectible_horizontal_layout.addWidget(
                self.outdated_collectible_balance_label,
            )
        if self.is_offline_wallet or self.is_watch_only:
            self._top_row_layout.addLayout(
                self.usb_last_sync_collectible_horizontal_layout,
            )

        self.vertical_layout_2.addLayout(self._top_row_layout)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)

        self.grid_layout.setObjectName('grid_layout')
        self.grid_layout.setContentsMargins(1, -1, 1, -1)

        self.vertical_layout_collectibles.addWidget(self.widget)
        self.collectibles_frame_card = QFrame(self.widget)
        self.collectibles_frame_card.setObjectName('collectibles_frame_card')

        self.collectibles_frame_card.setFrameShape(QFrame.StyledPanel)
        self.collectibles_frame_card.setFrameShadow(QFrame.Raised)
        self.collectible_frame_grid_layout = QFormLayout(
            self.collectibles_frame_card,
        )
        self.collectible_frame_grid_layout.setObjectName(
            'collectible_frame_grid_layout',
        )
        self.collectible_frame_grid_layout.setHorizontalSpacing(0)
        self.collectible_frame_grid_layout.setVerticalSpacing(0)
        self.collectible_frame_grid_layout.setContentsMargins(3, -1, 3, -1)

        self.grid_layout.addWidget(self.collectibles_frame_card)

        self.vertical_layout_2.addLayout(self.grid_layout)

        self.retranslate_ui()
        self.setup_ui_connection()
        self.resizeEvent = self.resize_event_called  # pylint: disable=invalid-name
        # Empty state management
        self._empty_state_widget = None
        self.issue_button_in_header = True

    def calculate_columns(self):
        """Calculate the number of columns based on the available width"""
        available_width = self.width()
        item_width = 290
        num_columns = max(1, available_width // item_width)
        return num_columns

    def resize_event_called(self, event):
        """It updates the layout of collectibles when window is resized"""
        super().resizeEvent(event)
        self._view_model.main_asset_view_model.asset_loaded.connect(
            self.update_grid_layout,
        )

    def update_grid_layout(self):
        """Update the grid layout with new number of columns"""
        num_columns = self.calculate_columns()
        # Build frames list including CFA drafts (identified by file_path in shared drafts table)
        self.frames = []
        wallet_service = WalletDataService.get_session()
        if wallet_service is not None:
            drafts = wallet_service.list_draft_issue_assets()
            for d in drafts:
                fp = d.get('file_path')
                if not fp:
                    continue
                if d.get('inflation_amounts') or d.get('replace_rights_num'):
                    continue
                self.frames.append(self.create_collectible_frame(draft=d))
        # Then append actual issued CFA assets
        for coll_asset in self._view_model.main_asset_view_model.assets.cfa:
            self.frames.append(
                self.create_collectible_frame(coll_asset=coll_asset),
            )
        self.total_items = len(self.frames)

        # Show empty state if there are no issued assets (drafts don't count)
        issued_count = len(self._view_model.main_asset_view_model.assets.cfa)
        if issued_count == 0:
            self._show_empty_collectibles_state()
            return
        self._hide_empty_collectibles_state()

        if hasattr(self, 'scroll_area'):
            grid_widget = self.scroll_area.widget()
            grid_layout = grid_widget.layout()
            grid_layout.setSpacing(40)

            # Clear the existing layout
            for i in reversed(range(grid_layout.count())):
                item = grid_layout.itemAt(i)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    grid_layout.removeItem(item)

            # Add widgets to the grid layout
            for index, frame in enumerate(self.frames):
                row = index // num_columns
                col = index % num_columns
                grid_layout.addWidget(frame, row, col)
            # Add spacers if the last row is not full
            if self.total_items < 5:
                remaining_columns = num_columns - \
                    (self.total_items % num_columns)
                row = self.total_items // num_columns
                for col in range(num_columns - remaining_columns, num_columns):
                    horizontal_spacer = QSpacerItem(
                        242, 242, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
                    )
                    grid_layout.addItem(horizontal_spacer, row, col)

            self.grid_layout = grid_layout
            self.resizeEvent = self.resize_event_called

    def create_collectibles_frames(self):
        """Initial setup for the grid layout and scroll area"""
        if not hasattr(self, 'scroll_area'):
            grid_widget = QWidget()
            self.grid_layout_widget = QGridLayout(grid_widget)
            grid_widget.setStyleSheet("""
                border:none;
                background: transparent;
            """)

            self.scroll_area = QScrollArea()  # pylint: disable=W0201
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setWidget(grid_widget)
            self.scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            )
            self.scroll_area.setStyleSheet(
                load_stylesheet('views/qss/scrollbar.qss'),
            )

            self.grid_layout.addWidget(self.scroll_area)

        self.grid_layout.setSpacing(10)
        self.grid_layout.setVerticalSpacing(20)
        self.update_grid_layout()
        self.resizeEvent = self.resize_event_called

    def create_collectible_frame(self, coll_asset=None, draft=None):
        """Create a single collectible or draft frame (reused for drafts)."""
        if draft is not None:
            image_path = draft.get('file_path')
            asset_name = f"{draft.get('name', 'Draft')} (Draft)"
            asset_id = 'draft_asset'
        else:
            image_path = coll_asset.media.file_path
            asset_name = coll_asset.name
            asset_id = coll_asset.asset_id
        collectibles_frame = ClickableFrame(
            asset_id,
            asset_name,
            image_path=image_path,
            asset_type=AssetSchema.CFA,
        )
        collectibles_frame.setObjectName('collectibles_frame')
        collectibles_frame.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        collectibles_frame.setStyleSheet(
            'background: transparent;\n'
            'border: none;\n'
            'border-top-left-radius: 8px;\n'
            'border-top-right-radius: 8px;\n',
        )
        collectibles_frame.setFrameShape(QFrame.StyledPanel)
        collectibles_frame.setFrameShadow(QFrame.Raised)

        form_layout = QFormLayout(collectibles_frame)
        form_layout.setObjectName('formLayout')
        form_layout.setHorizontalSpacing(0)
        form_layout.setVerticalSpacing(0)
        form_layout.setContentsMargins(0, 0, 0, 0)

        collectible_asset_name = QLabel(collectibles_frame)
        collectible_asset_name.setObjectName('collectible_asset_name')
        collectible_asset_name.setMinimumSize(242, 42)
        collectible_asset_name.setMaximumSize(242, 42)

        image_label = QLabel()
        image_label.setObjectName('collectible_image')
        image_label.setMinimumSize(242, 242)
        image_label.setMaximumSize(242, 242)
        image_label.setStyleSheet(
            'border-radius: 8px; border: none; background: transparent;',
        )
        image_label.setStyleSheet(
            'QLabel{\n'
            'border-top-left-radius: 8px;\n'
            'border-top-right-radius: 8px;\n'
            'border-bottom-left-radius: 0px;\n'
            'border-bottom-right-radius: 0px;\n'
            'background: transparent;\n'
            'background-color: rgb(27, 35, 59);\n'
            '}\n',
        )

        if image_path:
            resized_image = resize_image(image_path, 242, 242)
            image_label.setPixmap(resized_image)

        form_layout.addRow(image_label)

        collectible_asset_name.setStyleSheet(
            'QLabel{\n'
            'font: 15px "Inter";\n'
            'color: #FFFFFF;\n'
            'font-weight:600;\n'
            'border-top-left-radius: 0px;\n'
            'border-top-right-radius: 0px;\n'
            'border-bottom-left-radius: 8px;\n'
            'border-bottom-right-radius: 8px;\n'
            'background: transparent;\n'
            'background-color: rgb(27, 35, 59);\n'
            'padding: 10.5px, 10px, 10.5px, 10px;\n'
            'padding-left: 11px\n'
            '}\n'
            '',
        )
        collectible_asset_name.setText(asset_name)

        form_layout.addRow(collectible_asset_name)

        if draft is not None:
            draft_id = draft.get('id')
            if draft_id is not None:
                collectibles_frame.clicked.connect(
                    lambda _a=None, _b=None, _c=None, _d=None: self._view_model.page_navigation.issue_cfa_asset_page(
                        draft_id, from_draft=True,
                    ),
                )
        else:
            collectibles_frame.clicked.connect(
                self.handle_collectible_frame_click,
            )
        self.resizeEvent = self.resize_event_called
        return collectibles_frame

    def _show_empty_collectibles_state(self):
        """Display an empty-state card with action button centered."""
        # Hide header issue button
        self.collectible_header_frame.set_action_button_visible(
            False, override=True,
        )
        self.issue_button_in_header = False
        if self._empty_state_widget is not None:
            return
        # Hide scroll area so we can truly center the card
        if hasattr(self, 'scroll_area'):
            self.scroll_area.hide()
        wrapper = QFrame(self.widget)
        # remove card visuals per request (transparent)
        wrapper.setStyleSheet(
            'QFrame{border:none; background: transparent;} QLabel{background:transparent;}',
        )
        wrapper.setFixedWidth(680)
        wrapper.setFixedHeight(200)
        v = QVBoxLayout(wrapper)
        # reduce internal spacing so content sits tighter
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(2)
        # Title
        title = QLabel('No Assets Issued')
        title.setStyleSheet('color:#fff; font: 600 20px "Inter"; border:None;')
        v.addWidget(title, 0, Qt.AlignHCenter)
        # Subtext
        sub = QLabel(
            "You haven't issued any assets yet. Create your first collectible asset to get started.",
        )
        sub.setStyleSheet(
            'color: rgba(255,255,255,0.75); font: 14px "Inter"; border:None;',
        )
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignHCenter)
        sub.setFixedWidth(560)
        v.addWidget(sub, 0, Qt.AlignHCenter)
        # Action button
        btn = PrimaryButton('Issue New Collectibles')
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setFixedWidth(200)
        btn.clicked.connect(
            lambda: self._view_model.main_asset_view_model.navigate_issue_asset(
                self._view_model.page_navigation.issue_cfa_asset_page,
            ),
        )
        v.addWidget(btn, 0, Qt.AlignHCenter)
        # Add to grid area centered with stretches
        # Clear previous temp items if any
        self.grid_layout.addItem(
            QSpacerItem(
                0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
            ), 0, 0,
        )
        self.grid_layout.addWidget(wrapper, 1, 1, Qt.AlignCenter)
        self.grid_layout.setRowStretch(0, 1)
        self.grid_layout.setRowStretch(2, 3)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(2, 1)
        self._empty_state_widget = wrapper

    def _hide_empty_collectibles_state(self):
        """Remove empty-state card and show header action button."""
        if self._empty_state_widget is not None:
            self.grid_layout.removeWidget(self._empty_state_widget)
            self._empty_state_widget.deleteLater()
            self._empty_state_widget = None
        # Show scroll area again
        if hasattr(self, 'scroll_area'):
            self.scroll_area.show()
        # Show header button only if there are issued assets; release override accordingly
        issued_count = len(self._view_model.main_asset_view_model.assets.cfa)
        if issued_count > 0:
            # make it visible and keep override so network changes won't flip it
            self.collectible_header_frame.set_action_button_visible(
                True, override=True,
            )
            self.issue_button_in_header = True
        else:
            # keep hidden
            self.collectible_header_frame.set_action_button_visible(
                False, override=True,
            )
            self.issue_button_in_header = False

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self._view_model.main_asset_view_model.get_assets()
        self.collectible_header_frame.refresh_page_button.clicked.connect(
            self.trigger_render_and_refresh,
        )
        self.collectible_header_frame.action_button.clicked.connect(
            lambda: self._view_model.main_asset_view_model.navigate_issue_asset(
                self._view_model.page_navigation.issue_cfa_asset_page,
            ),
        )
        self._view_model.main_asset_view_model.loading_started.connect(
            self.show_collectible_asset_loading,
        )
        self._view_model.main_asset_view_model.loading_finished.connect(
            self.stop_loading_screen,
        )
        self._view_model.main_asset_view_model.message.connect(
            self.show_message,
        )

    def trigger_render_and_refresh(self):
        """This method start the render timer and perform the collectible asset list refresh"""
        self.render_timer.start()
        self._view_model.main_asset_view_model.get_assets(
            rgb_asset_hard_refresh=True,
        )
        formated_epoch_time = format_epoch_time()
        if formated_epoch_time is not None:
            self.usb_last_sync_collectible_info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_info_label', None,
                ).format(formated_epoch_time),
            )
            if self.is_offline_wallet:
                self.outdated_collectible_balance_label.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'outdated_balance_label', None,
                    ),
                )

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.show_collectible_asset_loading()
        self.collectible_header_frame.action_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_new_collectibles', None,
            ),
        )
        self.collectibles_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'collectibles', None,
            ),
        )
        formated_epoch_time = format_epoch_time()
        if formated_epoch_time is not None:
            self.usb_last_sync_collectible_info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_info_label', None,
                ).format(formated_epoch_time),
            )
            if self.is_offline_wallet:
                self.outdated_collectible_balance_label.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'outdated_balance_label', None,
                    ),
                )

    def handle_collectible_frame_click(self, asset_id, asset_name, image_path, asset_type):
        """This method handles collectibles asset click of the main asset page."""
        if asset_id is None or asset_name is None or image_path is None or asset_type is None:
            return
        self._view_model.cfa_view_model.asset_info.emit(
            asset_id, asset_name, image_path, asset_type,
        )
        self._view_model.page_navigation.cfa_detail_page(
            RgbAssetPageLoadModel(asset_type=asset_type),
        )

    def show_collectible_asset_loading(self):
        """This method handled show loading screen on main asset page"""
        self.loading_screen = LoadingTranslucentScreen(
            parent=self, description_text='Loading', dot_animation=True,
        )
        self.loading_screen.start()
        self.collectible_header_frame.refresh_page_button.setDisabled(True)

    def stop_loading_screen(self):
        """This method handled stop loading screen on main asset page"""
        self.loading_screen.stop()
        self.collectible_header_frame.refresh_page_button.setDisabled(False)
        self.render_timer.stop()

    def show_message(self, collectibles_asset_toast_preset, message):
        """This method handled showing message main asset page"""
        if collectibles_asset_toast_preset == ToastPreset.SUCCESS:
            ToastManager.success(description=message)
        if collectibles_asset_toast_preset == ToastPreset.ERROR:
            ToastManager.error(description=message)
        if collectibles_asset_toast_preset == ToastPreset.INFORMATION:
            ToastManager.info(description=message)
        if collectibles_asset_toast_preset == ToastPreset.WARNING:
            ToastManager.warning(description=message)
