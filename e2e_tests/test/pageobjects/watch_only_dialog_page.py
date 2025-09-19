"""Watch only dialog page objects module."""
from __future__ import annotations

from dogtail.tree import root
from accessible_constant import WATCH_ONLY_CANCEL_BUTTON, WATCH_ONLY_CHECKBOX, WATCH_ONLY_CONTINUE_BUTTON, WATCH_ONLY_DIALOG, WATCH_ONLY_MASTER_FINGERPRINT, WATCH_ONLY_XPUB_COLORED, WATCH_ONLY_XPUB_VANILLA
from e2e_tests.test.utilities.base_operation import BaseOperations


class WatchOnlyDialogPageObjects(BaseOperations):
    """
    Watch only dialog page objects class.
    """

    def __init__(self, application):
        """
        Initializes the WatchOnlyDialogPageObjects class.

        Args:
            application: The application instance.
        """
        super().__init__(application)

        # Lazy evaluation of elements using lambdas
        self.watch_only_dialog = lambda: root.child(
            roleName='dialog', name=WATCH_ONLY_DIALOG,
        )
        self.watch_only_xpub_vanilla = lambda: self.perform_action_on_element(application=self.watch_only_dialog(),
            role_name='text', name=WATCH_ONLY_XPUB_VANILLA,
        )
        self.watch_only_xpub_colored = lambda: self.perform_action_on_element(application=self.watch_only_dialog(),
            role_name='text', name=WATCH_ONLY_XPUB_COLORED,
        )
        self.watch_only_master_fingerprint = lambda: self.perform_action_on_element(application=self.watch_only_dialog(),
            role_name='text', name=WATCH_ONLY_MASTER_FINGERPRINT,
        )
        self.watch_only_checkbox = lambda: self.perform_action_on_element(application=self.watch_only_dialog(),
            role_name='check box', name=WATCH_ONLY_CHECKBOX,
        )
        self.cancel_button = lambda: self.perform_action_on_element(application=self.watch_only_dialog(),
            role_name='push button', name=WATCH_ONLY_CANCEL_BUTTON,
        )
        self.continue_button = lambda: self.perform_action_on_element(application=self.watch_only_dialog(),
            role_name='push button', name=WATCH_ONLY_CONTINUE_BUTTON,
        )

    def click_watch_only_dialog(self):
        """
        Clicks the watch only dialog if it is displayed.
        """
        return self.do_click(self.watch_only_dialog()) if self.do_is_displayed(self.watch_only_dialog()) else None

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

    def enter_xpub_vanilla_value(self, xpub_vanilla):
        """
        Enters the vanilla xpub in the watch only vanilla xpub input field.

        Args:
            xpub_vanilla (str): The vanilla xpub value to be entered.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.watch_only_xpub_vanilla(), xpub_vanilla) if self.do_is_displayed(self.watch_only_xpub_vanilla()) else None
        
    def enter_xpub_colored_value(self, xpub_colored):
        """
        Enters the colored xpub in the watch only colored xpub input field.

        Args:
            xpub_colored (str): The colored xpub value to be entered.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.watch_only_xpub_colored(), xpub_colored) if self.do_is_displayed(self.watch_only_xpub_colored()) else None

    def enter_fingerprint_value(self, fingerprint):
        """
        Enters the master fingerprint in the watch only fingerprint input field.

        Args:
            fingerprint (str): The fingerprint value to be entered.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.watch_only_master_fingerprint(), fingerprint) if self.do_is_displayed(self.watch_only_master_fingerprint()) else None

    def click_checkbox(self):
        """
        Clicks the checkbox if it is displayed.

        Returns:
            The result of the click action or None if the checkbox is not displayed.
        """
        return self.do_click(self.watch_only_checkbox()) if self.do_is_displayed(self.watch_only_checkbox()) else None
        