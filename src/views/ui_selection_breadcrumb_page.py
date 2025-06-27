# pylint: disable=too-many-instance-attributes,too-many-statements
"""
Selection breadcrumb page for wallet creation flow.
Provides a multi-step UI for selecting wallet mode, security type, entry type, and key storage, with breadcrumb navigation and dialog integration.
"""
from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QStackedWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletSecurityType
from src.model.enums.enums_model import WalletType
from src.model.selection_page_model import SelectionPageModel
from src.views.components.selection_breadcrumb_widget import BreadcrumbBar
from src.views.components.selection_page import SelectionPage
from src.views.components.wallet_logo_frame import WalletLogoFrame
from src.views.components.wallet_mode_summary_dialog import WalletModeSummaryDialog
from src.views.components.watch_only_dialog import WatchOnlyDialog
from src.views.ui_restore_mnemonic import RestoreMnemonicWidget


class SelectionBreadcrumbWidget(QWidget):
    """
    Widget for the selection breadcrumb navigation flow in the wallet creation process.
    Guides the user through wallet mode, security type, entry type, and key storage selection steps.
    """

    def __init__(self, view_model):
        """
        Initialize the SelectionBreadcrumbWidget and set up the multi-step UI.
        """
        super().__init__()
        self._view_model = view_model
        # Restore state from view model if present
        self.selected_logos = getattr(self._view_model, 'selected_logos', [])
        self.selected_titles = getattr(self._view_model, 'selected_titles', [])
        self.selected_step_indices = getattr(
            self._view_model, 'selected_step_indices', [],
        )
        self.current_index = getattr(self._view_model, 'current_index', 0)
        self.steps = [
            {
                'logo': ':/assets/online.png',
                'title': 'online',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='select_wallet_mode',
                        logo_1_path=':/assets/online.png',
                        logo_1_title=WalletType.ONLINE_TYPE_WALLET.value,
                        logo_1_info='online_wallet_info',
                        logo_2_path=':/assets/offline.png',
                        logo_2_title=WalletType.OFFLINE_TYPE_WALLET.value,
                        logo_2_info='offline_wallet_info',
                    ),
                ),
            },
            {
                'logo': ':/assets/private_key.png',
                'title': 'with_private_key',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='select_security_type',
                        logo_1_path=':/assets/private_key.png',
                        logo_1_title=WalletSecurityType.WITH_PRIVATE_KEY.value,
                        logo_1_info='with_private_key_info',
                        logo_2_path=':/assets/eye_icon.png',
                        logo_2_title=WalletSecurityType.WATCH_ONLY.value,
                        logo_2_info='watch_only_info',
                    ),
                ),
            },
            {
                'logo': ':/assets/create_new.png',
                'title': 'create_new',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='select_entry_type',
                        logo_1_path=':/assets/create_new.png',
                        logo_1_title=WalletEntryType.CREATE.value,
                        logo_1_info='create_new_wallet_info',
                        logo_2_path=':/assets/load_wallet.png',
                        logo_2_title=WalletEntryType.LOAD.value,
                        logo_2_info='load_existing_wallet_info',
                    ),
                ),
            },
            {
                'logo': ':/assets/desktop.png',
                'title': 'on_device',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='select_key_storage',
                        logo_1_path=':/assets/desktop.png',
                        logo_1_title=KeyStorageType.ON_DEVICE.value,
                        logo_1_info='on_device_info',
                        logo_2_path=':/assets/hw.png',
                        logo_2_title=KeyStorageType.HARDWARE_WALLET.value,
                        logo_2_info='hardware_wallet_info',
                    ),
                ),
            },
        ]
        self.previous_selections = []

        # Create main grid layout
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        # Add wallet logo at the top
        self.wallet_logo = WalletLogoFrame()
        self.grid_layout.addWidget(self.wallet_logo, 0, 0, 1, 2)

        # Add vertical spacer after logo (top spacer)
        self.vertical_spacer_1 = QSpacerItem(
            20, 208, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed,
        )
        self.grid_layout.addItem(self.vertical_spacer_1, 0, 3, 1, 1)

        # Add horizontal spacer for left margin
        self.horizontal_spacer_1 = QSpacerItem(
            268, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )
        self.grid_layout.addItem(self.horizontal_spacer_1, 1, 0, 1, 1)

        # Create main content widget
        self.widget_page = QWidget()
        self.widget_page.setObjectName('widget_page')
        self.widget_page.setStyleSheet("""
            QWidget#widget_page {
                background: transparent
            }
        """)
        self.widget_page.setMinimumSize(QSize(720, 480))

        # Create vertical layout for the content
        self.vertical_layout = QVBoxLayout(self.widget_page)
        self.vertical_layout.setSpacing(6)
        self.vertical_layout.setContentsMargins(1, 11, 1, 10)

        # Add stack widget to vertical layout
        self.stack = QStackedWidget()
        for step in self.steps:
            self.stack.addWidget(step['widget'])
        self.vertical_layout.addWidget(self.stack)

        # Add the widget page to grid layout (main content area)
        self.grid_layout.addWidget(self.widget_page, 1, 1, 1, 1)

        # Add bottom spacers
        self.vertical_spacer_5 = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )
        self.grid_layout.addItem(self.vertical_spacer_5, 3, 1, 1, 1)

        self.horizontal_spacer_2 = QSpacerItem(
            268, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )
        self.grid_layout.addItem(self.horizontal_spacer_2, 2, 4, 1, 1)

        self.vertical_spacer_4 = QSpacerItem(
            20, 208, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )
        self.grid_layout.addItem(self.vertical_spacer_4, 5, 2, 1, 1)

        # Connect continue buttons
        self.steps[0]['widget'].continue_button.clicked.connect(
            lambda: self.handle_continue(0),
        )
        self.steps[1]['widget'].continue_button.clicked.connect(
            lambda: self.handle_continue(1),
        )
        self.steps[2]['widget'].continue_button.clicked.connect(
            lambda: self.handle_continue(2),
        )
        self.steps[3]['widget'].continue_button.clicked.connect(
            lambda: self.handle_continue(3),
        )

        self.update_breadcrumbs()

    def get_flow_step_indices(self):
        """
        Returns the list of step indices for the current flow (offline or online).
        """
        if self.selected_titles and self.selected_titles[0] == WalletType.OFFLINE_TYPE_WALLET.value:
            return [0, 2, 3]
        return [0, 1, 2, 3]

    def update_breadcrumbs(self):
        """
        Update the breadcrumbs for the current step and manage the breadcrumb bar UI.
        """
        flow_indices = self.get_flow_step_indices()
        crumbs = []
        for i, logo in enumerate(self.selected_logos):
            crumbs.append(
                {
                    'logo': logo,
                    'title': self.selected_titles[i],
                    'step_index': flow_indices[i],
                    'pending': False,
                },
            )
        # If on a new step, add the default selection as a pending breadcrumb
        if (
            len(self.selected_logos) < len(flow_indices)
            and self.current_index == flow_indices[len(self.selected_logos)]
        ):
            step = self.steps[self.current_index]
            default_logo = step['widget'].params.logo_1_path
            default_title = step['widget'].params.logo_1_title
            crumbs.append({
                'logo': default_logo,
                'title': default_title,
                'step_index': self.current_index,
                'pending': True,
            })
        self._crumbs = crumbs  # Store for click handler
        # Remove any previous breadcrumb bar from all pages
        for step_data in self.steps:
            if hasattr(step_data['widget'], 'breadcrumb_widget') and step_data['widget'].breadcrumb_widget:
                if step_data['widget'].vertical_layout.indexOf(step_data['widget'].breadcrumb_widget) != -1:
                    step_data['widget'].vertical_layout.removeWidget(
                        step_data['widget'].breadcrumb_widget,
                    )
                    step_data['widget'].breadcrumb_widget.deleteLater()
                step_data['widget'].breadcrumb_widget = None
        # Add the new breadcrumb bar to the current step
        if crumbs:
            breadcrumb_bar_for_current_page = BreadcrumbBar(
                self.steps[self.current_index]['widget'],
            )
            breadcrumb_bar_for_current_page.crumb_clicked.connect(
                self.on_breadcrumb_clicked,
            )
            # Connect close button
            breadcrumb_bar_for_current_page.cls_button.clicked.connect(
                self._view_model.page_navigation.term_and_condition_page,
            )
            # Find the active breadcrumb index that matches the current_index
            active_index = next(
                (
                    i for i, crumb in enumerate(
                        crumbs,
                    ) if crumb['step_index'] == self.current_index
                ), len(crumbs) - 1,
            )
            breadcrumb_bar_for_current_page.set_breadcrumbs(
                crumbs, active_index=active_index,
            )
            current_page = self.steps[self.current_index]['widget']
            current_page.breadcrumb_widget = breadcrumb_bar_for_current_page
            current_page.vertical_layout.insertWidget(
                0, breadcrumb_bar_for_current_page,
            )
            # Hide the original close button in the page
            if hasattr(current_page, 'close_button'):
                current_page.close_button.hide()
        self.stack.setCurrentIndex(self.current_index)

    def on_breadcrumb_clicked(self, idx):
        """
        Handle the breadcrumb click event and navigate to the selected step if allowed.
        """
        # Only allow navigation to committed breadcrumbs (not pending)
        if idx >= len(self._crumbs) or self._crumbs[idx].get('pending', False):
            return
        self.current_index = self._crumbs[idx]['step_index']
        self.update_breadcrumbs()

    def get_breadcrumb_idx(self, step_idx):
        """
        Get the breadcrumb index for the given step index, accounting for offline mode mapping.
        """
        if self.selected_titles and self.selected_titles[0] == WalletType.OFFLINE_TYPE_WALLET.value:
            if step_idx == 0:
                return 0
            if step_idx == 2:
                return 1
            if step_idx == 3:
                return 2
        return step_idx

    def handle_continue(self, idx):
        """
        Handle the continue button click event for a given step index.
        Updates state, manages navigation, and shows dialogs as needed.
        """
        page = self.steps[idx]['widget']
        selected = page.selected_frame
        if selected == page.params.logo_1_title:
            logo = page.params.logo_1_path
            title = page.params.logo_1_title
        else:
            logo = page.params.logo_2_path
            title = page.params.logo_2_title
        self._reset_state_after_selection_change(idx, title, logo)
        if idx == 0:
            if title == WalletType.OFFLINE_TYPE_WALLET.value:
                self.current_index = 2
                SettingRepository.set_wallet_security_type(None)
                SettingRepository.remove_setting('wallet_security_type')
            else:
                self.current_index = idx + 1
            self.steps[self.current_index]['widget'].reset_selection()
            self.update_breadcrumbs()
        elif idx == 1:
            if title == WalletSecurityType.WATCH_ONLY.value:
                self._show_watch_only_flow()
            else:
                self.current_index = idx + 1
                self.steps[self.current_index]['widget'].reset_selection()
                self.update_breadcrumbs()
        else:
            if idx + 1 < len(self.steps):
                self.current_index = 3 if self.selected_titles[
                    0
                ] == WalletType.OFFLINE_TYPE_WALLET.value and idx == 2 else idx + 1
                self.steps[self.current_index]['widget'].reset_selection()
                self.update_breadcrumbs()
            else:
                self._show_final_summary_flow()
        if (idx != 1 or title != WalletSecurityType.WATCH_ONLY.value) and idx != len(self.steps) - 1:
            self.update_breadcrumbs()
        self._view_model.selected_logos = self.selected_logos
        self._view_model.selected_titles = self.selected_titles
        self._view_model.selected_step_indices = self.selected_step_indices
        self._view_model.current_index = self.current_index

    def _show_final_summary_flow(self):
        """
        Show the final wallet mode summary dialog and handle navigation after summary.
        Handles blur effect and navigation to hardware wallet or mnemonic restore if needed.
        """
        self.update_breadcrumbs()
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        dialog = WalletModeSummaryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.setGraphicsEffect(None)
            key_storage = SettingRepository.get_key_storage_type()
            if key_storage == KeyStorageType.HARDWARE_WALLET:
                self._view_model.page_navigation.hardware_wallet_connect_page()
            elif SettingRepository.get_wallet_entry_type() == WalletEntryType.LOAD:
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(10)
                restore_dialog = RestoreMnemonicWidget(
                    view_model=self._view_model, parent=self,
                )
                if restore_dialog.exec() == QDialog.Accepted:
                    self._view_model.page_navigation.welcome_page()
            else:
                self._view_model.page_navigation.welcome_page()
        else:
            self.setGraphicsEffect(None)

    def _show_watch_only_flow(self):
        """
        Show the watch-only wallet dialog flow, including xpub/fingerprint input and summary.
        Handles blur effect and navigation to welcome page if completed.
        """
        self.update_breadcrumbs()
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        dialog = WalletModeSummaryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            watch_only_dialog = WatchOnlyDialog(parent=self)
            if watch_only_dialog.exec() == QDialog.Accepted:
                self.setGraphicsEffect(None)
                self._view_model.page_navigation.welcome_page()
        else:
            self.setGraphicsEffect(None)

    def _reset_state_after_selection_change(self, idx, title, logo):
        """
        Reset the selection state and clear subsequent steps if the selection has changed.
        Updates selected_logos, selected_titles, and selected_step_indices accordingly.
        """
        breadcrumb_idx = self.get_breadcrumb_idx(idx)
        should_reset = (
            len(self.selected_titles) <= breadcrumb_idx or
            self.selected_titles[breadcrumb_idx] != title
        )
        if not should_reset:
            return
        self.selected_logos = self.selected_logos[:breadcrumb_idx]
        self.selected_titles = self.selected_titles[:breadcrumb_idx]
        flow_indices = self.get_flow_step_indices()
        self.selected_step_indices = flow_indices[:breadcrumb_idx]
        if len(self.selected_logos) > breadcrumb_idx:
            self.selected_logos[breadcrumb_idx] = logo
            self.selected_titles[breadcrumb_idx] = title
            self.selected_step_indices[breadcrumb_idx] = idx
        else:
            self.selected_logos.append(logo)
            self.selected_titles.append(title)
            self.selected_step_indices.append(idx)
        for i in range(idx + 1, len(self.steps)):
            widget = self.steps[i]['widget']
            widget.reset_selection()
            widget.info_frame.hide()
            widget.selected_frame = None
            widget.on_click_frame(widget.params.logo_1_title, False)
            widget.on_click_frame(widget.params.logo_2_title, False)
            if i == 1:
                SettingRepository.set_wallet_security_type(None)
                SettingRepository.remove_setting('wallet_security_type')
            elif i == 2:
                SettingRepository.set_wallet_entry_type(None)
                SettingRepository.remove_setting('wallet_entry_type')
            elif i == 3:
                SettingRepository.set_key_storage_type(None)
                SettingRepository.remove_setting('key_storage_type')
