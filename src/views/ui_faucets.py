# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import,implicit-str-concat
"""This module contains the FaucetsWidget,
 which represents the UI for faucet page.
 """
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.header_frame import HeaderFrame
from src.views.components.loading_screen import LoadingTranslucentScreen


class FaucetsWidget(QWidget):
    """This class represents all the UI elements of the enter wallet password page."""

    def __init__(self, view_model):
        self.render_timer = RenderTimer(task_name='FaucetsWidget Rendering')
        self.render_timer.start()
        super().__init__()
        self._view_model: MainViewModel = view_model
        self.faucet_frame = None
        self.single_frame_horizontal_layout = None
        self.single_frame_horizontal_layout = None
        self.faucet_request_button = None
        self.faucet_name_label = None
        self._loading_translucent_screen = None
        self.setStyleSheet(load_stylesheet('views/qss/faucet_style.qss'))
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(0)
        self.grid_layout.setObjectName('grid_layout')
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.faucets_widget = QWidget(self)
        self.faucets_widget.setObjectName('faucets_widget')
        self.faucets_widget.setMinimumSize(QSize(492, 80))

        self.faucet_vertical_layout = QVBoxLayout(self.faucets_widget)
        self.faucet_vertical_layout.setObjectName('verticalLayout_2')
        self.faucet_vertical_layout.setContentsMargins(25, 12, 25, 1)
        self.faucet_vertical_layout.setSpacing(12)
        self.faucets_title_frame = HeaderFrame(
            title_name='faucets', title_logo_path=':/assets/faucets.png',
        )
        self.faucets_title_frame.action_button.hide()
        self.faucets_title_frame.refresh_page_button.hide()
        self.faucet_vertical_layout.addWidget(self.faucets_title_frame)

        self.get_faucets_title_label = QLabel(self.faucets_widget)
        self.get_faucets_title_label.setObjectName('get_faucets_title_label')
        self.get_faucets_title_label.setMinimumSize(QSize(0, 54))
        self.get_faucets_title_label.setMaximumSize(QSize(16777215, 54))

        self.get_faucets_title_label.setAlignment(Qt.AlignCenter)

        self.faucet_vertical_layout.addWidget(
            self.get_faucets_title_label, 0, Qt.AlignLeft,
        )

        self.faucet_frame_vertical_layout = QVBoxLayout()
        self.faucet_frame_vertical_layout.setSpacing(8)
        self.faucet_frame_vertical_layout.setObjectName(
            'faucet_frame_vertical_layout',
        )
        self.faucet_vertical_layout.addLayout(
            self.faucet_frame_vertical_layout,
        )
        self.widget_vertical_spacer = QSpacerItem(
            20, 337, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )
        self.faucet_vertical_layout.addItem(self.widget_vertical_spacer)
        self.grid_layout.addWidget(self.faucets_widget, 0, 0, 1, 1)
        self._view_model.faucets_view_model.get_faucet_list()
        self.setup_ui_connection()
        self.retranslate_ui()

    def create_faucet_frames(self, faucets_list):
        """This method creates the faucet frames according to the faucet list."""
        for i in reversed(range(self.faucet_vertical_layout.count())):
            widget = self.faucet_vertical_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        # Remove the existing spacer if it exists
        if hasattr(self, 'widget_vertical_spacer') and self.widget_vertical_spacer:
            self.faucet_vertical_layout.removeItem(self.widget_vertical_spacer)
            self.widget_vertical_spacer = None

        # If the faucet list is None, create a placeholder frame
        if faucets_list is None:
            faucet_frame = self.create_faucet_frame(
                'Not yet available', 'NA', False,
            )
            self.faucet_vertical_layout.addWidget(faucet_frame)
        else:
            # Create faucet frames for each faucet in the list
            for name in faucets_list:
                faucet_frame = self.create_faucet_frame(
                    name.asset_name, name.asset_id, True,
                )
                self.faucet_vertical_layout.addWidget(faucet_frame)

        # Add a vertical spacer at the end
        self.widget_vertical_spacer = QSpacerItem(
            20, 337, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )
        self.faucet_vertical_layout.addItem(self.widget_vertical_spacer)

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.start_faucets_loading_screen()
        self._view_model.faucets_view_model.faucet_list.connect(
            self.create_faucet_frames,
        )
        self._view_model.faucets_view_model.start_loading.connect(
            self.start_faucets_loading_screen,
        )
        self._view_model.faucets_view_model.stop_loading.connect(
            self.stop_faucets_loading_screen,
        )

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.get_faucets_title_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'get_faucets', None,
            ),
        )

    def create_faucet_frame(self, asset_name, asset_id, is_faucets_available):
        """This method creates the single faucet frame"""
        # Create a frame for each faucet
        self.faucet_frame = QFrame(self.faucets_widget)
        self.faucet_frame.setObjectName('faucet_frame')
        self.faucet_frame.setStyleSheet(
            load_stylesheet('views/qss/faucet_style.qss'),
        )
        self.faucet_frame.setMinimumSize(QSize(335, 70))
        self.faucet_frame.setMaximumSize(QSize(335, 16777215))

        self.faucet_frame.setFrameShape(QFrame.StyledPanel)
        self.faucet_frame.setFrameShadow(QFrame.Raised)
        self.single_frame_horizontal_layout = QHBoxLayout(self.faucet_frame)
        self.single_frame_horizontal_layout.setObjectName(
            'single_frame_horizontal_layout',
        )
        self.single_frame_horizontal_layout.setContentsMargins(12, -1, 12, -1)
        if asset_name is None or not asset_name:
            asset_name = 'Not yet available'
        self.faucet_name_label = QLabel(asset_name, self.faucet_frame)

        self.faucet_name_label.setObjectName('faucet_name_label')

        self.faucet_name_label.setWordWrap(True)

        self.single_frame_horizontal_layout.addWidget(self.faucet_name_label)
        if is_faucets_available:
            self.faucet_request_button = QPushButton(self.faucet_frame)
            self.faucet_request_button.setObjectName('faucet_request_button')
            self.faucet_request_button.setMinimumSize(QSize(102, 40))
            self.faucet_request_button.setMaximumSize(QSize(102, 40))
            self.faucet_request_button.setCursor(
                QCursor(Qt.CursorShape.PointingHandCursor),
            )
            icon = QIcon()
            icon.addFile(
                ':/assets/get_faucets.png', QSize(),
                QIcon.Mode.Normal, QIcon.State.Off,
            )
            self.faucet_request_button.setIcon(icon)

            self.single_frame_horizontal_layout.addWidget(
                self.faucet_request_button,
            )

            self.faucet_frame_vertical_layout.addWidget(self.faucet_frame)
            self.faucet_request_button.clicked.connect(
                lambda: self.get_faucet_asset(asset_id),
            )
            self.faucet_request_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'request', None,
                ),
            )

        return self.faucet_frame

    def get_faucet_asset(self, _name):
        """This method retrieve the faucet list"""
        self._view_model.faucets_view_model.request_faucet_asset()

    def start_faucets_loading_screen(self):
        """This method handled show loading screen on faucet page"""
        self._loading_translucent_screen = LoadingTranslucentScreen(
            parent=self, description_text='Loading', dot_animation=True,
        )
        self._loading_translucent_screen.start()
        self._loading_translucent_screen.make_parent_disabled_during_loading(
            True,
        )

    def stop_faucets_loading_screen(self):
        """This method handled show loading screen on faucet page"""
        self._loading_translucent_screen.stop()
        self._loading_translucent_screen.make_parent_disabled_during_loading(
            False,
        )
        self.render_timer.stop()
