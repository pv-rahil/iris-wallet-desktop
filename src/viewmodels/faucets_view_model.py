"""This module contains the FaucetsViewModel class, which represents the view model
for the faucets page.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.service.faucet_service import FaucetService
from src.model.rgb_faucet_model import ListAvailableAsset
from src.model.rgb_faucet_model import RequestAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_FAUCET_ASSET_SENT
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class FaucetsViewModel(QObject, ThreadManager):
    """This class represents the activities of the faucets page."""
    start_loading = Signal(bool)
    stop_loading = Signal(bool)
    faucet_list = Signal(ListAvailableAsset)
    faucet_available = Signal(bool)

    def __init__(self, page_navigation) -> None:
        """Initialize the FaucetsViewModel with the given page navigation."""
        super().__init__()
        self._page_navigation = page_navigation
        self.sidebar = None

    def get_faucet_list(self):
        """
        Retrieve the list of faucet assets.
        """
        self.start_loading.emit(True)
        self.run_in_thread(
            FaucetService.list_available_asset,
            {
                'args': [],
                'callback': self.on_success_get_faucet_list,
                'error_callback': self.on_error,
            },
        )

    def on_success_get_faucet_list(self, response: ListAvailableAsset):
        """This method is used  handle onsuccess for the get faucet asset list."""
        self.faucet_list.emit(response.faucet_assets)
        self.stop_loading.emit(False)
        self.faucet_available.emit(True)

    def on_error(self) -> None:
        """This method is used  handle onerror for the get faucet asset list"""
        self.stop_loading.emit(False)
        self.faucet_list.emit(None)
        self.faucet_available.emit(False)

    def request_faucet_asset(self):
        """
        This method request the faucet asset.
        """
        self.start_loading.emit(True)
        self.run_in_thread(
            FaucetService.request_asset_from_faucet,
            {
                'args': [],
                'callback': self.on_success_get_faucet_asset,
                'error_callback': self.on_error_get_asset,
            },
        )

    def on_success_get_faucet_asset(self, response: RequestAssetResponseModel):
        """This method is used to handle onSuccess for asset receipt."""
        self.stop_loading.emit(False)
        ToastManager.success(
            description=INFO_FAUCET_ASSET_SENT.format(response.asset.name),
        )
        self._page_navigation.fungibles_asset_page()
        self.sidebar = self._page_navigation.sidebar()
        if self.sidebar is not None:
            self.sidebar.my_fungibles.setChecked(True)

    def on_error_get_asset(self, error: CommonException) -> None:
        """This method is used to handle onerror for asset receipt."""
        self.stop_loading.emit(False)
        ToastManager.error(
            description=error.message,
        )
