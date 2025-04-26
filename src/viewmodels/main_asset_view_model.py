"""This module contains the mainAssetViewModel class, which represents the view model
for the term and conditions page activities.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.service.main_asset_page_service import MainAssetPageDataService
from src.model.common_operation_model import MainPageDataResponseModel
from src.model.enums.enums_model import ToastPreset
from src.utils.cache import Cache
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NODE_CHANGING_STATE
from src.utils.worker import ThreadManager


class MainAssetViewModel(QObject, ThreadManager):
    """This class represents the activities of the main asset page."""
    asset_loaded = Signal(bool)
    loading_started = Signal(bool)
    message = Signal(ToastPreset, str)
    assets: MainPageDataResponseModel | None = None
    loading_finished = Signal(bool)

    # Assuming page_navigation is of type Any
    def __init__(self, page_navigation: Any) -> None:
        super().__init__()
        self._page_navigation = page_navigation

    def get_assets(self, rgb_asset_hard_refresh: bool = False):
        """This method get assets"""
        if rgb_asset_hard_refresh:
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
        self.loading_started.emit(True)

        def on_success(response: MainPageDataResponseModel, is_data_ready=True) -> None:
            """This method is used  handle onsuccess for the main asset page."""
            if response:
                if response.nia is not None:
                    response.nia.reverse()
                if response.uda is not None:
                    response.uda.reverse()
                if response.cfa is not None:
                    response.cfa.reverse()

            if response is not None:
                self.assets = response
                self.asset_loaded.emit(True)
                if is_data_ready:
                    self.loading_finished.emit(True)

        def on_error(error: CommonException) -> None:
            """This method is used  handle onerror for the main asset page."""
            self.asset_loaded.emit(False)
            self.loading_finished.emit(True)
            if error.message == ERROR_NODE_CHANGING_STATE:
                self.message.emit(ToastPreset.INFORMATION, error.message)
            else:
                self.message.emit(ToastPreset.ERROR, error.message)

        self.run_in_thread(
            MainAssetPageDataService.get_assets,
            {
                'key': 'mainassetviewmodel_get_asset',
                'use_cache': True,
                'callback': on_success,
                'error_callback': on_error,
            },
        )

    def navigate_issue_asset(self, where):
        """
        It Navigates the page according to page name
        """
        where()
