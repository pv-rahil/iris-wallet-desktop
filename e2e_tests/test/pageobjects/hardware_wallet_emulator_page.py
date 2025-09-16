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

        
    def press_left_and_right(self, duration: float = 0.3):
        """
        Press and hold the Left and Right arrow keys simultaneously
        using xdotool.

        :param duration: time in seconds to hold the keys
        """
        # keydown both
        subprocess.run(["xdotool", "keydown", "Left"])
        subprocess.run(["xdotool", "keydown", "Right"])

        time.sleep(duration)

        # keyup both
        subprocess.run(["xdotool", "keyup", "Left"])
        subprocess.run(["xdotool", "keyup", "Right"])

    
    def click_right_arrow_key(self,num):
        """Clicks the right arrow key."""
        for _ in range(num):
            keyCombo("Right")

