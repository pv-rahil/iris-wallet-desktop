"""
Module for handling Windows Hello authentication using the winsdk library.

This module provides functionality to authenticate users using Windows Hello
within a PySide6 application. It includes methods to bring the Windows Security
dialog to the foreground to ensure it is accessible to the user.
"""
# pylint:disable=possibly-used-before-assignment, disable=import-error
from __future__ import annotations

import asyncio
import sys

from src.utils.logging import logger


if sys.platform.startswith('win'):
    from win32 import win32gui
    from win32.lib import win32con
    from winsdk.windows.security.credentials.ui import UserConsentVerificationResult
    from winsdk.windows.security.credentials.ui import UserConsentVerifier
    from winsdk.windows.security.credentials.ui import UserConsentVerifierAvailability


class WindowNativeAuthentication:
    """
    Class for managing Windows Hello authentication and bringing the authentication
    dialog to the foreground.

    Attributes:
        msg (str): The message displayed to the user during authentication.
    """

    def __init__(self, msg):
        """
        Initialize the WindowNativeAuthentication class.

        Args:
            msg (str): The message to display in the Windows Hello authentication dialog.
        """
        self.msg: str = msg

    def _get_hwnd(self):
        """
        Retrieve the handle of the 'Windows Security' window if it is visible.

        Returns:
            int: The handle of the 'Windows Security' window, or None if not found.
        """
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                windows.append((hwnd, title))

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)

        for hwnd, title in windows:
            if title == 'Windows Security':
                return hwnd
        return None

    def _bring_window_to_foreground(self, hwnd):
        """
        Bring the specified window to the foreground and ensure it is focused.

        Args:
            hwnd (int): The handle of the window to bring to the foreground.
        """
        if hwnd:
            try:
                # Show the window
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

                # Bring the window to the foreground
                win32gui.SetForegroundWindow(hwnd)

                # Ensure the window is on top
                win32gui.SetWindowPos(
                    hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                )
                win32gui.SetWindowPos(
                    hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                )

                # Optionally, you can send an activation message to the window
                win32gui.SendMessage(
                    hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0,
                )

                # Force focus on the window
                win32gui.SetFocus(hwnd)
            except Exception as exc:
                logger.error(
                    'Exception occurred at native windows auth while bringing auth ui foreground: %s, Message: %s',
                    type(exc).__name__, str(exc),
                )

    async def authenticate_with_windows_hello(self):
        """
        Authenticate the user using Windows Hello.

        This method checks the availability of Windows Hello, requests user verification,
        and brings the Windows Security dialog to the foreground if necessary.

        Returns:
            bool: True if the user is verified, False otherwise.
        """
        availability = await UserConsentVerifier.check_availability_async()

        if availability == UserConsentVerifierAvailability.AVAILABLE:

            result_op = UserConsentVerifier.request_verification_async(
                self.msg,
            )

            # Poll for the dialog to appear
            hwnd = None
            for _ in range(20):  # Polling up to 20 times (each loop waits 0.1 seconds)
                hwnd = self._get_hwnd()
                if hwnd:
                    break
                await asyncio.sleep(0.1)

            # Bring ui on top of application
            if hwnd is not None:
                self._bring_window_to_foreground(hwnd=hwnd)
            result = await result_op
            return result == UserConsentVerificationResult.VERIFIED
        return True

    def start_windows_native_auth(self):
        """
        Start the Windows Hello authentication process.

        This method runs the asynchronous authentication process and returns the result.

        Returns:
            bool: True if the user is verified, False otherwise.
        """
        authenticated = asyncio.run(self.authenticate_with_windows_hello())
        if authenticated:
            return True
        return False
