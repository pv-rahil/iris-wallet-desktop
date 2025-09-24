"""USB sync dialog page objects module."""
from __future__ import annotations

from dogtail.tree import root

from accessible_constant import USB_SYNC_DIALOG
from accessible_constant import USB_SYNC_DIALOG_CANCEL_BUTTON
from accessible_constant import USB_SYNC_DIALOG_CONTINUE_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class USBSyncDialogPageObjects(BaseOperations):
    """
    USB sync dialog page objects class.
    """

    def __init__(self, application):
        """
        Initializes the USBSyncDialogPageObjects class.

        Args:
            application: The application instance.
        """
        super().__init__(application)

        # Lazy evaluation of elements using lambdas
        self.usb_sync_dialog = lambda: root.child(
            roleName='dialog', name=USB_SYNC_DIALOG,
        )
        self.cancel_button = lambda: self.perform_action_on_element(
            application_name=self.usb_sync_dialog(),
            role_name='push button', name=USB_SYNC_DIALOG_CANCEL_BUTTON,
        )
        self.continue_button = lambda: self.perform_action_on_element(
            application_name=self.usb_sync_dialog(),
            role_name='push button', name=USB_SYNC_DIALOG_CONTINUE_BUTTON,
        )

    def click_usb_sync_dialog(self):
        """
        Clicks the USB sync dialog if it is displayed.
        """
        return self.do_click(self.usb_sync_dialog()) if self.do_is_displayed(self.usb_sync_dialog()) else None

    def click_cancel_button(self):
        """
        Clicks the cancel button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.cancel_button()) if self.do_is_displayed(self.cancel_button()) else None

    def click_continue_button(self):
        """
        Clicks the continue button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.continue_button()) if self.do_is_displayed(self.continue_button()) else None
