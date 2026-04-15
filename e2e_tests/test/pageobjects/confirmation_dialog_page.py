"""
Confirmation Dialog page objects for interacting with the confirmation dialog page.
"""
from __future__ import annotations

from dogtail.rawinput import keyCombo

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import CONFIRMATION_DIALOG_CANCEL_BUTTON
from accessible_constant import CONFIRMATION_DIALOG_CHECKBOX
from accessible_constant import CONFIRMATION_DIALOG_CONTINUE_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class ConfirmationDialogPageObjects(BaseOperations):
    """Page object for the Confirmation Dialog page."""

    def __init__(self, application):
        super().__init__(application)

        self.confirmation_dialog = lambda: self.application.parent.child(
            roleName='dialog', name=CONFIRMATION_DIALOG,
        )
        self.confirmation_continue_button = lambda: self.perform_action_on_element(
            role_name='push button', name=CONFIRMATION_DIALOG_CONTINUE_BUTTON, application_node=self.confirmation_dialog(),
        )
        self.confirmation_checkbox = lambda: self.perform_action_on_element(
            role_name='check box', name=CONFIRMATION_DIALOG_CHECKBOX, application_node=self.confirmation_dialog(),
        )
        self.confirmation_cancel_button = lambda: self.perform_action_on_element(
            role_name='push button', name=CONFIRMATION_DIALOG_CANCEL_BUTTON, application_node=self.confirmation_dialog(),
        )

    def click_confirmation_dialog(self):
        """
        Clicks the confirmation dialog on the confirmation dialog page.
        """
        return self.do_click(self.confirmation_dialog()) if self.do_is_displayed(self.confirmation_dialog()) else None

    def click_confirmation_continue_button(self):
        """
        Clicks the confirmation continue button on the confirmation dialog page.
        """
        return self.do_click(self.confirmation_continue_button()) if self.do_is_displayed(self.confirmation_continue_button()) else None

    def click_confirmation_checkbox(self):
        """
        Clicks the confirmation checkbox on the confirmation dialog page.
        """
        if self.do_is_displayed(self.confirmation_checkbox()):
            self.confirmation_checkbox().grabFocus()
            keyCombo('space')
            return True
        return False

    def click_confirmation_cancel_button(self):
        """
        Clicks the confirmation cancel button on the confirmation dialog page.
        """
        return self.do_click(self.confirmation_cancel_button()) if self.do_is_displayed(self.confirmation_cancel_button()) else None
