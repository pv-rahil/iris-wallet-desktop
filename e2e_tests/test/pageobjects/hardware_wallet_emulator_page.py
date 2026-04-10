# pylint:disable=too-many-instance-attributes
"""
Hardware wallet emulator page objects class for interacting with the hardware wallet emulator page.
"""
from __future__ import annotations

import subprocess
import time

from dogtail.rawinput import keyCombo
from dogtail.tree import root

from e2e_tests.test.utilities.base_operation import BaseOperations


class HardwareWalletEmulatorPageObjects(BaseOperations):
    """
    Hardware wallet emulator page objects class for interacting with the hardware wallet emulator page.
    """

    def __init__(self, application):
        """
        Initializes the HardwareWalletEmulatorPageObjects class.

        Args:
            application: The application object.
        """
        super().__init__(application)

        self.hw_emulator_window = lambda: root.child(
            roleName='filler', name='Ledger Nano SP Emulator',
        )

    def wait_for_emulator_screen(self, timeout: int = 30) -> bool:
        """
        Wait for the emulator to show a screen with navigable content.
        Polls until the emulator window has child elements (screen content).

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if screen content detected, False if timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                window = self.hw_emulator_window()
                # Check if window has content (labels, text, etc.)
                children = window.findChildren(
                    lambda x: x.roleName in ['label', 'text', 'push button']
                )
                if children:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def wait_for_screen_change(self, timeout: int = 30) -> bool:
        """
        Wait for the emulator screen content to change.
        This detects when a new request is received by comparing screen content.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if screen changed, False if timeout.
        """
        # Get initial screen content
        try:
            window = self.hw_emulator_window()
            initial_children = window.findChildren(
                lambda x: x.roleName in ['label', 'text', 'push button']
            )
            initial_content = [c.name for c in initial_children if c.name]
        except Exception:
            initial_content = []

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                window = self.hw_emulator_window()
                children = window.findChildren(
                    lambda x: x.roleName in ['label', 'text', 'push button']
                )
                current_content = [c.name for c in children if c.name]

                # Check if content changed (new screen)
                if current_content and current_content != initial_content:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def press_left_and_right(self, duration: float = 0.3):
        """
        Press and hold the Left and Right arrow keys simultaneously
        using xdotool.

        :param duration: time in seconds to hold the keys
        """
        # keydown both
        subprocess.run(['xdotool', 'keydown', 'Left'], check=True)
        subprocess.run(['xdotool', 'keydown', 'Right'], check=True)

        time.sleep(duration)

        # keyup both
        subprocess.run(['xdotool', 'keyup', 'Left'], check=True)
        subprocess.run(['xdotool', 'keyup', 'Right'], check=True)

    def click_right_arrow_key(self, num, delay: float = 0.2):
        """Clicks the right arrow key.

        Args:
            num: Number of times to press the right arrow key.
            delay: Delay in seconds between each key press (default 0.2s).
        """
        for _ in range(num):
            keyCombo('Right')
            time.sleep(delay)
