"""
Restore wallet page objects module.
"""
from __future__ import annotations

from accessible_constant import RESTORE_CONTINUE_BUTTON
from accessible_constant import RESTORE_DIALOG_BOX
from accessible_constant import RESTORE_FINGERPRINT_INPUT
from accessible_constant import RESTORE_MNEMONIC_INPUT
from accessible_constant import RESTORE_PASSWORD_INPUT
from accessible_constant import RESTORE_XPUB_COLORED_INPUT
from accessible_constant import RESTORE_XPUB_VANILLA_INPUT
from e2e_tests.test.utilities.base_operation import BaseOperations


class RestoreWalletPageObjects(BaseOperations):
    """
    A class to represent Restore wallet page objects.
    """

    def __init__(self, application):
        """
        Initializes the RestoreWalletPageObjects class.

        Args:
            application: The application instance.
        """
        super().__init__(application)

        self.restore_dialog_box = lambda: self.application.parent.child(
            roleName='dialog', name=RESTORE_DIALOG_BOX,
        )
        self.restore_mnemonic_input = lambda: self.restore_dialog_box().child(
            roleName='text', name=RESTORE_MNEMONIC_INPUT,
        )
        self.restore_password_input = lambda: self.restore_dialog_box().child(
            roleName='password text', name=RESTORE_PASSWORD_INPUT,
        )
        # Watch-only / hardware wallet inputs
        self.restore_xpub_vanilla_input = lambda: self.restore_dialog_box().child(
            roleName='text', name=RESTORE_XPUB_VANILLA_INPUT,
        )
        self.restore_xpub_colored_input = lambda: self.restore_dialog_box().child(
            roleName='text', name=RESTORE_XPUB_COLORED_INPUT,
        )
        self.restore_fingerprint_input = lambda: self.restore_dialog_box().child(
            roleName='text', name=RESTORE_FINGERPRINT_INPUT,
        )
        self.restore_continue_button = lambda: self.restore_dialog_box().child(
            roleName='push button', name=RESTORE_CONTINUE_BUTTON,
        )

    def enter_mnemonic_value(self, mnemonic):
        """
        Enters the mnemonic value in the restore mnemonic input field.

        Args:
            mnemonic (str): The mnemonic value to be entered.

        Returns:
            bool: True if the mnemonic value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.restore_mnemonic_input(), mnemonic) if self.do_is_displayed(self.restore_mnemonic_input()) else None

    def enter_password_value(self, password):
        """
        Enters the password value in the restore password input field.

        Args:
            password (str): The password value to be entered.

        Returns:
            bool: True if the password value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.restore_password_input(), password) if self.do_is_displayed(self.restore_password_input()) else None

    def enter_xpub_vanilla_value(self, xpub_vanilla):
        """
        Enters the vanilla xpub in the restore xpub vanilla input field.

        Args:
            xpub_vanilla (str): The xpub vanilla value to be entered.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.restore_xpub_vanilla_input(), xpub_vanilla) if self.do_is_displayed(self.restore_xpub_vanilla_input()) else None

    def enter_xpub_colored_value(self, xpub_colored):
        """
        Enters the colored xpub in the restore xpub colored input field.

        Args:
            xpub_colored (str): The xpub colored value to be entered.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.restore_xpub_colored_input(), xpub_colored) if self.do_is_displayed(self.restore_xpub_colored_input()) else None

    def enter_fingerprint_value(self, fingerprint):
        """
        Enters the master fingerprint in the restore fingerprint input field.

        Args:
            fingerprint (str): The fingerprint value to be entered.

        Returns:
            bool: True if the value is entered successfully, False otherwise.
        """
        return self.do_set_value(self.restore_fingerprint_input(), fingerprint) if self.do_is_displayed(self.restore_fingerprint_input()) else None

    def click_continue_button(self):
        """
        Clicks the continue button.

        Returns:
            bool: True if the continue button is clicked successfully, False otherwise.
        """
        return self.do_click(self.restore_continue_button()) if self.do_is_displayed(self.restore_continue_button()) else None
