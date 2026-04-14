# pylint:disable=too-many-instance-attributes
"""
Backup page objects class for interacting with the backup page.
"""
from __future__ import annotations

import os
import re
import subprocess
import time

import pyotp
from dotenv import load_dotenv

from accessible_constant import BACKUP_CLOSE_BUTTON
from accessible_constant import BACKUP_WALLET_DATA_BUTTON
from accessible_constant import BACKUP_WINDOW
from accessible_constant import CONFIGURE_BACKUP_BUTTON
from accessible_constant import MNEMONIC_FRAME
from accessible_constant import SHOW_MNEMONIC_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations

load_dotenv()

GOOGLE_AUTHENTICATOR = os.getenv('GOOGLE_AUTHENTICATOR')


class BackupPageObjects(BaseOperations):
    """
    Backup page objects class for interacting with the backup page.
    """

    def __init__(self, application):
        """
        Initializes the BackupPageObjects class.

        Args:
            application: The application object.
        """
        super().__init__(application)

        self.configure_button = lambda: self.perform_action_on_element(
            role_name='push button', name=CONFIGURE_BACKUP_BUTTON,
        )
        self.backup_close_button = lambda: self.perform_action_on_element(
            role_name='push button', name=BACKUP_CLOSE_BUTTON,
        )
        self.show_mnemonic_button = lambda: self.perform_action_on_element(
            role_name='push button', name=SHOW_MNEMONIC_BUTTON,
        )
        self.backup_window = lambda: self.application.parent.child(
            roleName='filler', name=BACKUP_WINDOW,
        )
        self.email_input = lambda: self.perform_action_on_element(
            role_name='text', name='Email or phone', application_node=self.backup_window(),
        )
        self.next_button = lambda: self.perform_action_on_element(
            role_name='push button', name='Next', application_node=self.backup_window(),
        )
        self.password_input = lambda: self.perform_action_on_element(
            role_name='password text', name='Enter your password', application_node=self.backup_window(),
        )
        self.try_another_way_button = lambda: self.perform_action_on_element(
            role_name='push button', name='Try another way', application_node=self.backup_window(),
        )
        self.google_authenticator = lambda: self.perform_action_on_element(
            role_name='link', name='Get a verification code from the Google Authenticator app', application_node=self.backup_window(),
        )
        self.enter_code = lambda: self.perform_action_on_element(
            role_name='text', name='Enter code', application_node=self.backup_window(),
        )
        self.continue_button = lambda: self.perform_action_on_element(
            role_name='push button', name='Continue', application_node=self.backup_window(),
        )
        self.backup_wallet_data_button = lambda: self.perform_action_on_element(
            role_name='push button', name=BACKUP_WALLET_DATA_BUTTON,
        )
        self.mnemonic_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=MNEMONIC_FRAME,
        )

    def click_show_mnemonic_button(self):
        """Clicks the mnemonic button."""
        return self.do_click(self.show_mnemonic_button()) if self.do_is_displayed(self.show_mnemonic_button()) else None

    def click_configurable_button(self):
        """
        Clicks the configure button.

        Returns:
            The result of the click action.
        """
        return self.do_click(self.configure_button()) if self.do_is_displayed(self.configure_button()) else None

    def click_backup_close_button(self):
        """
        Clicks the backup close button.

        Returns:
            The result of the click action.
        """
        return self.do_click(self.backup_close_button()) if self.do_is_displayed(self.backup_close_button()) else None

    def click_backup_window(self):
        """
        Clicks the backup window.

        Returns:
            The result of the click action.
        """
        if self.do_is_displayed(self.backup_window()):
            self.do_click(self.backup_window())
            subprocess.run(
                [
                    'wmctrl', '-r', ':ACTIVE:', '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=False, capture_output=True, timeout=2,
            )
            return True
        return False

    def enter_email(self, email):
        """
        Enters the email.

        Args:
            email: The email to enter.

        Returns:
            The result of the enter action.
        """
        return self.do_set_value(self.email_input(), email) if self.do_is_displayed(self.email_input()) else None

    def click_next_button(self):
        """
        Clicks the next button.

        Returns:
            The result of the click action.
        """
        return self.do_click(self.next_button()) if self.do_is_displayed(self.next_button()) else None

    def enter_password(self, password):
        """
        Enters the password.

        Args:
            password: The password to enter.

        Returns:
            The result of the enter action.
        """
        return self.do_set_value(self.password_input(), password) if self.do_is_displayed(self.password_input()) else None

    def click_try_another_way_button(self):
        """
        Clicks the try another way button.

        Returns:
            The result of the click action.
        """
        if self.do_is_displayed(self.try_another_way_button()):
            self.try_another_way_button().grabFocus()
            return self.do_click(self.try_another_way_button())
        return None

    def click_google_authenticator_button(self):
        """
        Clicks the Google Authenticator button.

        Returns:
            The result of the click action.
        """
        if self.do_is_displayed(self.google_authenticator()):
            self.google_authenticator().grabFocus()
            return self.do_click(self.google_authenticator())
        return None

    def enter_security_code(self, code):
        """
        Enters the security code.

        Args:
            code: The security code to enter.

        Returns:
            The result of the enter action.
        """
        return self.do_set_value(self.enter_code(), code) if self.do_is_displayed(self.enter_code()) else None

    def get_security_otp(self):
        """
        Gets the security OTP.

        Returns:
            The security OTP.
        """
        totp = pyotp.TOTP(GOOGLE_AUTHENTICATOR)

        # Get fresh OTP with enough time remaining for typing
        # 30 seconds buffer ensures enough time for slow typing
        while True:
            time_remaining = totp.interval - (time.time() % totp.interval)

            if time_remaining < 25:
                # Not enough time - wait for new OTP cycle
                # Wait for new OTP + small buffer
                time.sleep(time_remaining + 0.5)
            else:
                # Enough time - get fresh OTP and return
                otp_code = totp.now()
                break

        # Format the OTP as "XXX XXX"
        formatted_otp = f"{otp_code[:3]} {otp_code[3:]}"

        return formatted_otp

    def click_continue_button(self):
        """
        Clicks the continue button.

        Returns:
            The result of the click action.
        """
        if self.do_is_displayed(self.continue_button()):
            self.continue_button().grabFocus()
            return self.do_click(self.continue_button())
        return None

    def click_backup_wallet_data_button(self):
        """
        Clicks the backup wallet data button.
        """
        return self.do_click(self.backup_wallet_data_button()) if self.do_is_displayed(self.backup_wallet_data_button()) else None

    def get_mnemonic(self):
        """
        Gets the mnemonic as a formatted string.
        """
        children = self.mnemonic_frame().children
        mnemonic_parts = [child.name for child in children if child.name]

        # Remove numerical prefixes like '1.', '2.', etc.
        cleaned_mnemonic = [
            re.sub(r'^\d+\.\s*', '', word)
            for word in mnemonic_parts
        ]

        # Join words into a single string
        return ' '.join(cleaned_mnemonic)
