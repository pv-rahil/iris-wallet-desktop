"""View model to handle network connectivity check or other logic for header"""
from __future__ import annotations

import socket

from PySide6.QtCore import QObject
from PySide6.QtCore import QThread
from PySide6.QtCore import QTimer
from PySide6.QtCore import Signal

from src.utils.constant import PING_DNS_ADDRESS_FOR_NETWORK_CHECK
from src.utils.constant import PING_DNS_SERVER_CALL_INTERVAL
from src.utils.page_navigation_events import PageNavigationEventManager
from src.utils.usb_detector import USBDetector


class NetworkCheckerThread(QThread):
    """Thread to handle network connectivity checking."""
    network_status_signal = Signal(bool)

    def run(self):
        """Run the network check once."""
        is_connected = self.check_internet_conn()
        self.network_status_signal.emit(is_connected)

    def check_internet_conn(self):
        """Check internet connection and return status."""
        try:
            socket.create_connection(
                (PING_DNS_ADDRESS_FOR_NETWORK_CHECK, 53), timeout=3,
            )
            return True
        except OSError:
            return False


class HeaderFrameViewModel(QObject):
    """Handles network connectivity in the UI."""
    network_status_signal = Signal(bool)
    usb_status_signal = Signal(bool)

    def __init__(self):
        super().__init__()
        self.network_checker = None

        # Use QTimer in the main thread
        self.timer = QTimer(self)
        self.timer.setInterval(PING_DNS_SERVER_CALL_INTERVAL)
        self.timer.timeout.connect(self.start_network_check)

        # USB check timer
        self.usb_timer = QTimer(self)
        self.usb_timer.setInterval(5000)  # Check every 5 seconds
        self.usb_timer.timeout.connect(self.handle_usb_status)

        # Start checking
        self.timer.start()
        self.usb_timer.start()

    def start_network_check(self):
        """Start a new network check using a separate thread."""
        self.network_checker = NetworkCheckerThread()
        self.network_checker.network_status_signal.connect(
            self.handle_network_status,
        )
        self.network_checker.start()

    def handle_network_status(self, is_connected):
        """Emit network status signal."""
        self.network_status_signal.emit(is_connected)

    def stop_network_checker(self):
        """Stop network checking when it's no longer needed."""
        self.timer.stop()
        # self.usb_timer.stop()

    def handle_usb_status(self):
        self.event_based_navigation = PageNavigationEventManager.get_instance()
        """Emit usb status signal"""
        usb = USBDetector()
        if usb.is_usb_connected():
            self.event_based_navigation.detect_usb_dialog_box.emit(True)
            # self.usb_status_signal.emit(True)

        else:
            # self.usb_status_signal.emit(False)
            self.event_based_navigation.detect_usb_dialog_box.emit(False)

