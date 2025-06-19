from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtCore import QEvent
from PySide6.QtCore import QObject
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QStackedWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget
import functools

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletSecurityType
from src.model.enums.enums_model import WalletType
from src.model.selection_page_model import SelectionPageModel
from src.views.components.selection_page import SelectionPage
from src.views.components.wallet_logo_frame import WalletLogoFrame
from src.views.components.wallet_mode_summary_dialog import WalletModeSummaryDialog


class BreadcrumbBar(QWidget):
    """
    This class represents the breadcrumb bar widget.
    It is used to display the navigation path in the application.
    """
    crumb_clicked = Signal(int)

    class CrumbHoverHelper(QObject):
        def __init__(self, frame, title_label, logo_label, logo_path, logo_white_path):
            super().__init__(frame)
            self.frame = frame
            self.title_label = title_label
            self.logo_label = logo_label
            self.logo_path = logo_path
            self.logo_white_path = logo_white_path

        def eventFilter(self, obj, event):
            if event.type() == QEvent.Enter:
                self.title_label.setStyleSheet("color: white; font-weight: 700; font-size: 17px;background: transparent;border: none")
                if self.logo_white_path:
                    self.logo_label.setPixmap(QPixmap(self.logo_white_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            elif event.type() == QEvent.Leave:
                self.title_label.setStyleSheet("color: rgb(102, 108, 129); font-weight: 600; font-size: 17px;background: transparent;border: none")
                if self.logo_path:
                    self.logo_label.setPixmap(QPixmap(self.logo_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            return False

    def __init__(self, parent=None):
        """
        Initialize the BreadcrumbBar widget.
        """
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(38, 15, 15, 15)
        self.layout.setSpacing(4)
        self.crumbs = []
        self.active_index = 0  # Track which breadcrumb is active

        self.cls_button = QPushButton(self)
        self.cls_button.setObjectName('close_button')
        self.cls_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cls_button.setMinimumSize(QSize(24, 24))
        self.cls_button.setMaximumSize(QSize(50, 65))
        self.cls_button.setAutoFillBackground(False)
        # Create close button
        close_icon = QIcon()
        close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(), QIcon.Normal, QIcon.Off,
        )
        self.cls_button.setIcon(close_icon)
        self.cls_button.setIconSize(QSize(24, 24))
        self.cls_button.setCheckable(False)
        self.cls_button.setChecked(False)

        self.setStyleSheet("""
            QFrame#breadcrumb_frame {
                background: transparent;
                border: none;
            }
            QLabel {
                color: #2c3e50;
                font-size: 14px;
            }
        """)

    def set_breadcrumbs(self, crumbs, active_index=0):
        """
        Set the breadcrumbs for the breadcrumb bar.
        """
        self.active_index = active_index
        # Clear existing crumbs
        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        self.crumbs = []

        for i, crumb in enumerate(crumbs):
            frame = QFrame()
            frame.setObjectName('breadcrumb_frame')
            frame.setFixedHeight(48)
            frame.setCursor(Qt.PointingHandCursor)
            # Mark pending state on the frame
            frame.is_pending = crumb.get('pending', False)

            h = QHBoxLayout(frame)
            h.setContentsMargins(5, 8, 0, 8)
            h.setSpacing(0)

            # Inner frame for hover effect
            crumb_content_frame = QFrame()
            crumb_content_frame.setObjectName('crumb_content_frame')
            crumb_content_frame.setStyleSheet("""
                QFrame {
                    background: transparent;
                    border: none
                }
            """)
            crumb_content_layout = QHBoxLayout(crumb_content_frame)
            crumb_content_layout.setContentsMargins(4, 0, 4, 0)
            crumb_content_layout.setSpacing(2)

            logo_container = QFrame()
            logo_container.setFixedSize(26, 26)
            logo_container.setStyleSheet("""
                QFrame {
                    background: transparent;
                    border: none           
                }
            """)
            logo_layout = QHBoxLayout(logo_container)
            logo_layout.setContentsMargins(0, 0, 0, 0)

            logo = QLabel()
            logo.setObjectName('breadcrumb_logo')
            logo_path = crumb.get('logo', '')
            # Auto-map to white logo if not provided
            logo_white_path = crumb.get('logo_white', '')
            if not logo_white_path and logo_path:
                import re
                m = re.match(r'^(.*/)?([^/]+)\.png$', logo_path)
                if m:
                    base = m.group(1) or ''
                    name = m.group(2)
                    logo_white_path = f"{base}white_{name}.png"

            logo.setPixmap(
                QPixmap(logo_path).scaled(
                    24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation,
                ),
            )
            logo_layout.addWidget(logo)
            crumb_content_layout.addWidget(logo_container)

            title = QLabel(crumb['title'])
            # Highlight if active
            if i == self.active_index:
                title.setStyleSheet("color: white; font-weight: 700; font-size: 17px;background: transparent;border: none")
                if logo_white_path:
                    logo.setPixmap(QPixmap(logo_white_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                title.setStyleSheet("color: rgb(102, 108, 129); font-weight: 600; font-size: 17px;background: transparent;border: none")
            crumb_content_layout.addWidget(title)

            h.addWidget(crumb_content_frame)

            # Install event filter for hover effect (only if not active)
            if i != self.active_index:
                hover_helper = self.CrumbHoverHelper(crumb_content_frame, title, logo, logo_path, logo_white_path)
                crumb_content_frame.installEventFilter(hover_helper)
                crumb_content_frame._hover_helper = hover_helper

            # Only allow click if not pending
            if not frame.is_pending:
                frame.mousePressEvent = functools.partial(lambda self, e, idx: self.crumb_clicked.emit(idx), self, idx=i)
            else:
                frame.mousePressEvent = lambda e: None

            self.layout.addWidget(frame)
            self.crumbs.append(frame)

            if i < len(crumbs) - 1:
                # Add two '>' symbols with reduced spacing
                separator = QLabel('>')
                separator.setStyleSheet("""
                    QLabel {
                        color: #95a5a6;
                        font-size: 20px;
                        font-weight: bold;
                    }
                """)
                self.layout.addWidget(separator)

        # Add stretch to push close button to the right
        self.layout.addStretch()
        # Add close button at the end
        self.layout.addWidget(self.cls_button)


class SelectionBreadcrumbWidget(QWidget):
    """
    This class represents the selection breadcrumb widget.
    It is used to display the selection path in the application.
    """

    def __init__(self, view_model):
        """
        Initialize the SelectionBreadcrumbWidget.
        """
        super().__init__()
        self._view_model = view_model
        self.steps = [
            {
                'logo': ':/assets/online.png',
                'title': 'Online',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='Select Wallet Mode',
                        logo_1_path=':/assets/online.png',
                        logo_1_title=WalletType.ONLINE_TYPE_WALLET.value,
                        logo_1_info='Online wallet allows you to connect to the network and perform transactions.',
                        logo_2_path=':/assets/offline.png',
                        logo_2_title=WalletType.OFFLINE_TYPE_WALLET.value,
                        logo_2_info='Offline wallet allows you to manage your assets without connecting to the network.',
                    ),
                ),
            },
            {
                'logo': ':/assets/private_key.png',
                'title': 'With Private Key',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='Select Security Type',
                        logo_1_path=':/assets/private_key.png',
                        logo_1_title=WalletSecurityType.WITH_PRIVATE_KEY.value,
                        logo_1_info='This wallet has a private key that allows you to sign transactions.',
                        logo_2_path=':/assets/eye_icon.png',
                        logo_2_title=WalletSecurityType.WATCH_ONLY.value,
                        logo_2_info='This wallet is watch-only. You can view your assets but cannot sign transactions.',
                    ),
                ),
            },
            {
                'logo': ':/assets/create_new.png',
                'title': 'Create New',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='Select Entry Type',
                        logo_1_path=':/assets/create_new.png',
                        logo_1_title=WalletEntryType.CREATE.value,
                        logo_1_info='Create a new wallet with a new seed phrase.',
                        logo_2_path=':/assets/load_wallet.png',
                        logo_2_title=WalletEntryType.LOAD.value,
                        logo_2_info='Load an existing wallet using a seed phrase or private key.',
                    ),
                ),
            },
            {
                'logo': ':/assets/desktop.png',
                'title': 'On Device',
                'widget': SelectionPage(
                    view_model=self._view_model,
                    params=SelectionPageModel(
                        title='Select Key Storage',
                        logo_1_path=':/assets/desktop.png',
                        logo_1_title=KeyStorageType.ON_DEVICE.value,
                        logo_1_info='Store your private key on your device securely.',
                        logo_2_path=':/assets/hw.png',
                        logo_2_title=KeyStorageType.HARDWARE_WALLET.value,
                        logo_2_info='Use a hardware wallet to store your private key securely.',
                    ),
                ),
            },
        ]
        self.selected_logos = []
        self.selected_titles = []
        self.selected_step_indices = []  # Track the actual step index for each breadcrumb
        self.current_index = 0
        # Add a new variable to track previous selections
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
        Update the breadcrumbs for the current step.
        """
        flow_indices = self.get_flow_step_indices()
        crumbs = []
        for i in range(len(self.selected_logos)):
            crumbs.append(
                {
                    'logo': self.selected_logos[i],
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
            default_logo = step['widget']._params.logo_1_path
            default_title = step['widget']._params.logo_1_title
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
            active_index = next((i for i, crumb in enumerate(crumbs) if crumb['step_index'] == self.current_index), len(crumbs) - 1)
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
        Handle the breadcrumb click event.
        """
        # Only allow navigation to committed breadcrumbs (not pending)
        if idx >= len(self._crumbs) or self._crumbs[idx].get('pending', False):
            return
        self.current_index = self._crumbs[idx]['step_index']
        self.update_breadcrumbs()

    def get_breadcrumb_idx(self, step_idx):
        """
        Get the breadcrumb index for the given step index.
        """
        # For offline mode, map step indices to breadcrumb indices
        if self.selected_titles and self.selected_titles[0] == WalletType.OFFLINE_TYPE_WALLET.value:
            if step_idx == 0:
                return 0
            elif step_idx == 2:
                return 1
            elif step_idx == 3:
                return 2
        return step_idx

    def handle_continue(self, idx):
        """
        Handle the continue button click event.
        """
        # Get selected option for breadcrumb
        page = self.steps[idx]['widget']
        selected = page.selected_frame

        if selected == page._params.logo_1_title:
            logo = page._params.logo_1_path
            title = page._params.logo_1_title
        else:
            logo = page._params.logo_2_path
            title = page._params.logo_2_title

        breadcrumb_idx = self.get_breadcrumb_idx(idx)
        # Only reset and update breadcrumbs if the selection has changed
        should_reset = (
            len(self.selected_titles) <= breadcrumb_idx or
            self.selected_titles[breadcrumb_idx] != title
        )

        if should_reset:
            self.selected_logos = self.selected_logos[:breadcrumb_idx]
            self.selected_titles = self.selected_titles[:breadcrumb_idx]
            # Always keep committed step indices in sync
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

            # Reset all subsequent pages to their initial state
            for i in range(idx + 1, len(self.steps)):
                self.steps[i]['widget'].reset_selection()
                self.steps[i]['widget'].info_frame.hide()
                self.steps[i]['widget'].selected_frame = None
                self.steps[i]['widget'].on_click_frame(
                    self.steps[i]['widget']._params.logo_1_title, False,
                )
                self.steps[i]['widget'].on_click_frame(
                    self.steps[i]['widget']._params.logo_2_title, False,
                )
                # Clear the stored types for subsequent steps
                if i == 1:  # Security type
                    SettingRepository.set_wallet_security_type(None)
                    SettingRepository.remove_setting('wallet_security_type')
                elif i == 2:  # Entry type
                    SettingRepository.set_wallet_entry_type(None)
                    SettingRepository.remove_setting('wallet_entry_type')
                elif i == 3:  # Key storage type
                    SettingRepository.set_key_storage_type(None)
                    SettingRepository.remove_setting('key_storage_type')

        # Special navigation logic
        if idx == 0:  # First selection (Online/Offline)
            if title == WalletType.OFFLINE_TYPE_WALLET.value:
                # If offline selected, go to entry type selection (Create New/Load)
                self.current_index = 2  # Skip security type
                # Clear security type since we're skipping it
                SettingRepository.set_wallet_security_type(None)
                SettingRepository.remove_setting('wallet_security_type')
                # Reset the next page to default selection
                self.steps[self.current_index]['widget'].reset_selection()
                # Update breadcrumbs to show correct path
                self.update_breadcrumbs()
            else:
                # If online selected, go to next step
                self.current_index = idx + 1
                # Reset the next page to default selection
                self.steps[self.current_index]['widget'].reset_selection()
                self.update_breadcrumbs()
        elif idx == 1:  # Second selection (With Private Key/Watch Only)
            if title == WalletSecurityType.WATCH_ONLY.value:
                # Update breadcrumbs once before showing dialog
                self.update_breadcrumbs()
                # Then show summary dialog
                dialog = WalletModeSummaryDialog(self._view_model)
                # Add blur effect to parent widget
                blur = QGraphicsBlurEffect()
                blur.setBlurRadius(10)
                self.setGraphicsEffect(blur)
                if dialog.exec() == QDialog.Accepted:
                    # Remove blur effect
                    self.setGraphicsEffect(None)
                    # Clear all selections before going to welcome page
                    self.selected_logos = []
                    self.selected_titles = []
                    self.selected_step_indices = []
                    # Clear all settings from local storage
                    SettingRepository.remove_setting('wallet_type')
                    SettingRepository.remove_setting('wallet_security_type')
                    SettingRepository.remove_setting('wallet_entry_type')
                    SettingRepository.remove_setting('key_storage_type')
                    self._view_model.page_navigation.welcome_page()
                else:
                    # Remove blur effect if dialog is rejected
                    self.setGraphicsEffect(None)
            else:
                # If with private key selected, go to next step
                self.current_index = idx + 1
                # Reset the next page to default selection
                self.steps[self.current_index]['widget'].reset_selection()
                self.update_breadcrumbs()
        else:
            # For other selections, proceed normally
            if idx + 1 < len(self.steps):
                # For offline mode, if we're on entry type page (idx=2), next should be key storage (idx=3)
                if self.selected_titles[0] == WalletType.OFFLINE_TYPE_WALLET.value and idx == 2:
                    self.current_index = 3
                else:
                    self.current_index = idx + 1
                # Reset the next page to default selection
                self.steps[self.current_index]['widget'].reset_selection()
                self.update_breadcrumbs()
            else:
                # Update breadcrumbs once before showing dialog
                self.update_breadcrumbs()
                # Then show summary dialog
                dialog = WalletModeSummaryDialog(self._view_model)
                # Add blur effect to parent widget
                blur = QGraphicsBlurEffect()
                blur.setBlurRadius(10)
                self.setGraphicsEffect(blur)
                if dialog.exec() == QDialog.Accepted:
                    # Remove blur effect
                    self.setGraphicsEffect(None)
                    # Clear all selections before going to welcome page
                    self.selected_logos = []
                    self.selected_titles = []
                    self.selected_step_indices = []
                    # Clear all settings from local storage
                    SettingRepository.remove_setting('wallet_type')
                    SettingRepository.remove_setting('wallet_security_type')
                    SettingRepository.remove_setting('wallet_entry_type')
                    SettingRepository.remove_setting('key_storage_type')
                    self._view_model.page_navigation.welcome_page()
                else:
                    # Remove blur effect if dialog is rejected
                    self.setGraphicsEffect(None)

        # Update breadcrumbs once at the end for all non-dialog cases
        if not (idx == 1 and title == WalletSecurityType.WATCH_ONLY.value) and not (idx == len(self.steps) - 1):
            self.update_breadcrumbs()
