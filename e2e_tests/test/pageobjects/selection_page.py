"""
Wallet selection page objects module.
"""
from __future__ import annotations

import time

from accessible_constant import OPTION_1_FRAME
from accessible_constant import OPTION_2_FRAME
from accessible_constant import WALLET_SELECTION_CONTINUE_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class SelectionPageObjects(BaseOperations):
    """
    Selection page objects class.
    """

    def __init__(self, application):
        """
        Initializes the SelectionPageObjects class.

        Args:
            application: The application instance.
        """
        super().__init__(application)

        # Lazy evaluation of elements using lambdas
        self.option_1_button = lambda: self.get_first_element(
            role_name='panel', name=OPTION_1_FRAME,
        )
        self.option_2_button = lambda: self.get_first_element(
            role_name='panel', name=OPTION_2_FRAME,
        )
        self.continue_button = lambda: self.get_first_element(
            role_name='push button', name=WALLET_SELECTION_CONTINUE_BUTTON,
        )

    def click_option_1_button(self):
        """
        Clicks the option 1 button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.option_1_button()) if self.do_is_displayed(self.option_1_button()) else None

    def click_option_2_button(self):
        """
        Clicks the option 2 button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.option_2_button()) if self.do_is_displayed(self.option_2_button()) else None

    def click_continue_button(self):
        """
        Clicks the continue button if it is displayed.
        """
        return self.do_click(self.continue_button()) if self.do_is_displayed(self.continue_button()) else None

    def select_option(self, which: int):
        """
        Select option by index: 1 or 2.
        """
        time.sleep(1)
        if which == 1:
            return self.click_option_1_button()
        if which == 2:
            return self.click_option_2_button()
        return None
