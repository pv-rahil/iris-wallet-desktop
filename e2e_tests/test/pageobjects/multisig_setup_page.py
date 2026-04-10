"""Multisig setup page objects module."""
from __future__ import annotations

from accessible_constant import MULTISIG_BACK_BUTTON
from accessible_constant import MULTISIG_COLORED_XPUB_COPY_BUTTON
from accessible_constant import MULTISIG_CONTINUE_BUTTON
from accessible_constant import MULTISIG_COSIGNER_CARD
from accessible_constant import MULTISIG_COSIGNER_IMPORT_BUTTON
from accessible_constant import MULTISIG_COSIGNER_RESET_BUTTON
from accessible_constant import MULTISIG_COSIGNER_STRING_COPY_BUTTON
from accessible_constant import MULTISIG_COSIGNER_STRING_INPUT
from accessible_constant import MULTISIG_EXPORT_BUTTON
from accessible_constant import MULTISIG_REQUIRED_SIGNER_INPUT
from accessible_constant import MULTISIG_REVIEW_COSIGNER_STRING_INPUT
from accessible_constant import MULTISIG_SETUP_PAGE
from accessible_constant import MULTISIG_TOTAL_SIGNER_INPUT
from e2e_tests.test.utilities.base_operation import BaseOperations


class MultisigSetupPageObjects(BaseOperations):
    """
    Multisig setup page objects class.
    """

    def __init__(self, application):
        """
        Initializes the MultisigSetupPageObjects class.

        Args:
            application: The application instance.
        """
        super().__init__(application)
        self.application = application

        # Lazy evaluation of elements using lambdas
        self.multisig_setup_page = lambda: self.application.child(
            roleName='panel', name=MULTISIG_SETUP_PAGE,
        )
        self.total_signer_input = lambda: self.perform_action_on_element(
            role_name='text', name=MULTISIG_TOTAL_SIGNER_INPUT,
            application_node=application,
        )
        self.required_signer_input = lambda: self.perform_action_on_element(
            role_name='text', name=MULTISIG_REQUIRED_SIGNER_INPUT,
            application_node=application,
        )
        self.continue_button = lambda: self.perform_action_on_element(
            role_name='push button', name=MULTISIG_CONTINUE_BUTTON,
            application_node=application,
        )
        self.back_button = lambda: self.perform_action_on_element(
            role_name='push button', name=MULTISIG_BACK_BUTTON,
            application_node=application,
        )
        self.export_button = lambda: self.perform_action_on_element(
            role_name='push button', name=MULTISIG_EXPORT_BUTTON,
            application_node=application,
        )
        self.colored_xpub_copy_button = lambda: self.perform_action_on_element(
            role_name='push button', name=MULTISIG_COLORED_XPUB_COPY_BUTTON,
            application_node=application,
        )
        self.cosigner_string_copy_button = lambda: self.perform_action_on_element(
            role_name='push button', name=MULTISIG_COSIGNER_STRING_COPY_BUTTON,
            application_node=application,
        )

    def get_review_cosigner_string_input(self):
        """
        Get the review frame cosigner string input field.
        Used by watch-only multisig wallets to enter the first cosigner's data.

        Returns:
            The review frame cosigner string input element or None.
        """
        return self.perform_action_on_element(
            role_name='text', name=MULTISIG_REVIEW_COSIGNER_STRING_INPUT,
            application_node=self.application,
        )

    def enter_review_cosigner_string(self, cosigner_string: str):
        """
        Enter cosigner string into the review frame input field.
        Used by watch-only multisig wallets to enter the first cosigner's data.

        Args:
            cosigner_string: The cosigner details string to enter.

        Returns:
            bool: True if successful, False otherwise.
        """
        input_field = self.get_review_cosigner_string_input()
        if input_field and self.do_is_displayed(input_field):
            return self.do_set_text(input_field, cosigner_string)
        return None

    def get_cosigner_card(self, index: int):
        """
        Get cosigner card by index.

        Args:
            index: The cosigner index (2, 3, etc.)

        Returns:
            The cosigner card element or None.
        """
        return self.perform_action_on_element(
            role_name='panel', name=f'{MULTISIG_COSIGNER_CARD}_{index}',
            application_node=self.application,
        )

    def get_cosigner_string_input(self, index: int):
        """
        Get cosigner string input by index.

        Args:
            index: The cosigner index (2, 3, etc.)

        Returns:
            The cosigner string input element or None.
        """
        return self.perform_action_on_element(
            role_name='text', name=f'{MULTISIG_COSIGNER_STRING_INPUT}_{index}',
            application_node=self.application,
        )

    def get_cosigner_import_button(self, index: int):
        """
        Get cosigner import button by index.

        Args:
            index: The cosigner index (2, 3, etc.)

        Returns:
            The cosigner import button element or None.
        """
        return self.perform_action_on_element(
            role_name='push button', name=f'{MULTISIG_COSIGNER_IMPORT_BUTTON}_{index}',
            application_node=self.application,
        )

    def get_cosigner_reset_button(self, index: int):
        """
        Get cosigner reset button by index.

        Args:
            index: The cosigner index (2, 3, etc.)

        Returns:
            The cosigner reset button element or None.
        """
        return self.perform_action_on_element(
            role_name='push button', name=f'{MULTISIG_COSIGNER_RESET_BUTTON}_{index}',
            application_node=self.application,
        )

    def click_continue_button(self):
        """
        Clicks the continue button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.continue_button().queryAction().doAction(0) if self.do_is_displayed(self.continue_button()) else None

    def click_back_button(self):
        """
        Clicks the back button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.back_button()) if self.do_is_displayed(self.back_button()) else None

    def click_export_button(self):
        """
        Clicks the export button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.export_button()) if self.do_is_displayed(self.export_button()) else None

    def click_colored_xpub_copy_button(self):
        """
        Clicks the colored xpub copy button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.colored_xpub_copy_button()) if self.do_is_displayed(self.colored_xpub_copy_button()) else None

    def click_cosigner_string_copy_button(self):
        """
        Clicks the cosigner string copy button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.cosigner_string_copy_button()) if self.do_is_displayed(self.cosigner_string_copy_button()) else None

    def enter_total_signer_value(self, total_signers: int):
        """
        Enters the total number of signers.

        Args:
            total_signers (int): The total number of signers.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.total_signer_input(), str(total_signers)) if self.do_is_displayed(self.total_signer_input()) else None

    def enter_required_signer_value(self, required_signers: int):
        """
        Enters the required number of signers for threshold.

        Args:
            required_signers (int): The required number of signers.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.required_signer_input(), str(required_signers)) if self.do_is_displayed(self.required_signer_input()) else None

    def get_total_signer_value(self) -> str | None:
        """
        Gets the total signer input value.

        Returns:
            str: The total signer value or None if not displayed.
        """
        return self.do_get_value(self.total_signer_input()) if self.do_is_displayed(self.total_signer_input()) else None

    def get_required_signer_value(self) -> str | None:
        """
        Gets the required signer input value.

        Returns:
            str: The required signer value or None if not displayed.
        """
        return self.do_get_value(self.required_signer_input()) if self.do_is_displayed(self.required_signer_input()) else None

    def expand_cosigner_card(self, index: int):
        """
        Expand a cosigner card by clicking on it.

        Args:
            index: The cosigner index (2, 3, etc.)

        Returns:
            The result of the click action or None.
        """
        card = self.get_cosigner_card(index)
        if card and self.do_is_displayed(card):
            try:
                return card.queryAction().doAction(0)
            except Exception:
                return self.do_click(card)
        return None

    def enter_cosigner_string(self, index: int, cosigner_string: str):
        """
        Enter cosigner string into the input field for a specific cosigner.

        Args:
            index: The cosigner index (2, 3, etc.)
            cosigner_string: The cosigner details string to enter.

        Returns:
            bool: True if successful, False otherwise.
        """
        input_field = self.get_cosigner_string_input(index)
        if input_field and self.do_is_displayed(input_field):
            return self.do_set_text(input_field, cosigner_string)
        return None

    def click_cosigner_import_button(self, index: int):
        """
        Click the import button for a specific cosigner.

        Args:
            index: The cosigner index (2, 3, etc.)

        Returns:
            The result of the click action or None.
        """
        button = self.get_cosigner_import_button(index)
        if button and self.do_is_displayed(button):
            try:
                return button.queryAction().doAction(0)
            except Exception:
                return self.do_click(button)
        return None

    def click_cosigner_reset_button(self, index: int):
        """
        Click the reset button for a specific cosigner.

        Args:
            index: The cosigner index (2, 3, etc.)

        Returns:
            The result of the click action or None.
        """
        button = self.get_cosigner_reset_button(index)
        if button and self.do_is_displayed(button):
            try:
                return button.queryAction().doAction(0)
            except Exception:
                return self.do_click(button)
        return None

    def import_cosigner_data(self, index: int, cosigner_string: str):
        """
        Complete flow to import cosigner data: expand card, enter string, click import.

        Args:
            index: The cosigner index (2, 3, etc.)
            cosigner_string: The cosigner details string to import.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Expand the card first
        self.expand_cosigner_card(index)

        # Enter the cosigner string
        result = self.enter_cosigner_string(index, cosigner_string)
        if not result:
            return False

        # Click import button
        return self.click_cosigner_import_button(index)
