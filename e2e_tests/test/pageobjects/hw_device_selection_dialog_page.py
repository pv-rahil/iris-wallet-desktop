# pylint:disable=too-many-instance-attributes
"""
Hardware device selection dialog page objects class for interacting with the hardware device selection dialog page.
"""
from __future__ import annotations

from accessible_constant import HW_DEVICE_SELECTION_DIALOG
from accessible_constant import HW_DEVICE_SELECTION_DIALOG_CANCEL_BUTTON
from accessible_constant import HW_DEVICE_SELECTION_DIALOG_CONNECT_BUTTON
from accessible_constant import LEDGER_EMULATOR_RADIO_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class HWDeviceSelectionDialogPageObjects(BaseOperations):
    """
    Hardware device selection dialog page objects class for interacting with the hardware device selection dialog page.
    """

    def __init__(self, application):
        """
        Initializes the HardwareDeviceSelectionDialogPageObjects class.

        Args:
            application: The application object.
        """
        super().__init__(application)

        self.hw_device_selection_dialog = lambda: self.application.parent.child(
            roleName='dialog', name=HW_DEVICE_SELECTION_DIALOG,
        )
        self.connect_button = lambda: self.hw_device_selection_dialog().child(
            roleName='push button', name=HW_DEVICE_SELECTION_DIALOG_CONNECT_BUTTON,
        )
        self.cancel_button = lambda: self.hw_device_selection_dialog().child(
            roleName='push button', name=HW_DEVICE_SELECTION_DIALOG_CANCEL_BUTTON,
        )
        self.ledger_emulator_radio_button = lambda: self.hw_device_selection_dialog().child(
            roleName='radio button', name=LEDGER_EMULATOR_RADIO_BUTTON,
        )

    def click_connect_button(self):
        """Clicks the connect button."""
        return self.do_click(self.connect_button()) if self.do_is_displayed(self.connect_button()) else None

    def click_cancel_button(self):
        """Clicks the cancel button."""
        return self.do_click(self.cancel_button()) if self.do_is_displayed(self.cancel_button()) else None

    def click_ledger_emulator_radio_button(self):
        """Clicks the ledger emulator radio button."""
        return self.do_click(self.ledger_emulator_radio_button()) if self.do_is_displayed(self.ledger_emulator_radio_button()) else None
