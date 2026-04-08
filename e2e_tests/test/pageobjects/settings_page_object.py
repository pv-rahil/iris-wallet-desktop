# pylint: disable=too-many-instance-attributes, too-many-public-methods
"""This module represents the page object for the settings page"""
from __future__ import annotations

import os
import time

from dogtail.rawinput import press
from dogtail.rawinput import pressKey
from dogtail.rawinput import release

from accessible_constant import ASK_AUTH_FOR_APP_LOGIN_TOGGLE
from accessible_constant import ASK_AUTH_FOR_IMPORTANT_QUESTION_TOGGLE
from accessible_constant import HIDE_EXHAUSTED_ASSETS_TOGGLE
from accessible_constant import INPUT_BOX_NAME
from accessible_constant import KEYRING_TOGGLE_BUTTON
from accessible_constant import SET_DEFAULT_FEE_RATE
from accessible_constant import SET_DEFAULT_MIN_EXPIRATION
from accessible_constant import SPECIFY_INDEXER_URL
from accessible_constant import SPECIFY_RGB_PROXY_URL
from e2e_tests.test.utilities.base_operation import BaseOperations


class SettingsPageObjects(BaseOperations):
    """Class for settings page objects"""

    def __init__(self, application):
        """Class for the settings page object"""

        super().__init__(application)

        # Settings frames
        self.keyring_toggle_button = lambda: self.perform_action_on_element(
            role_name='check box', name=KEYRING_TOGGLE_BUTTON,
        )
        self.login_auth_toggle_button = lambda: self.perform_action_on_element(
            role_name='check box', name=ASK_AUTH_FOR_APP_LOGIN_TOGGLE,
        )
        self.default_fee_rate_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=SET_DEFAULT_FEE_RATE,
        )
        self.set_min_confirmation_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=SET_DEFAULT_MIN_EXPIRATION,
        )
        self.specify_indexer_url_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=SPECIFY_INDEXER_URL,
        )
        self.specify_rgb_proxy_url_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=SPECIFY_RGB_PROXY_URL,
        )
        self.save_button = lambda: self.perform_action_on_element(
            role_name='push button', name='Save',
        )
        self.hide_exhausted_asset_toggle_button = lambda: self.perform_action_on_element(
            role_name='check box', name=HIDE_EXHAUSTED_ASSETS_TOGGLE,
        )

        self.ask_auth_for_imp_question_toggle = lambda: self.perform_action_on_element(
            role_name='check box', name=ASK_AUTH_FOR_IMPORTANT_QUESTION_TOGGLE,
        )

        # Input Boxes in Frames
        self.input_box = lambda: self.perform_action_on_element(
            role_name='text', name=INPUT_BOX_NAME,
        )

    def clear_input_box(self):
        """Clears the input box."""
        return self.do_clear_text(self.input_box()) if self.do_is_displayed(self.input_box()) else None

    def enter_input_value(self, value):
        """Enters a value in the input box."""
        return self.do_set_value(self.input_box(), value) if self.do_is_displayed(self.input_box()) else None

    def click_keyring_toggle_button(self):
        """Click on keyring toggle button"""
        if self.do_is_displayed(self.keyring_toggle_button()):
            self.keyring_toggle_button().grabFocus()
            return pressKey('space')

    def click_login_app_toggle_button(self):
        """Click on login app toggle button"""
        if self.do_is_displayed(self.login_auth_toggle_button()):
            self.login_auth_toggle_button().grabFocus()
            return pressKey('space')

    def _click_frame_with_press_release(self, frame):
        """Click on a frame using press and release method."""
        if not self.do_is_displayed(frame):
            return None
        pos = frame.position
        center_x = int(pos[0] + frame.size[0]//2)
        center_y = int(pos[1] + frame.size[1]//2)
        press(center_x, center_y)
        time.sleep(0.2)
        release(center_x, center_y)
        time.sleep(0.5)
        return True

    # Default Fee Rate
    def click_default_fee_rate_frame(self):
        """Click on the default fee rate frame"""
        return self._click_frame_with_press_release(self.default_fee_rate_frame())

    # Minimum Confirmation

    def click_set_min_confirmation_frame(self):
        """Click on the set minimum confirmation frame"""
        return self._click_frame_with_press_release(self.set_min_confirmation_frame())

    # Indexer URL

    def click_set_indexer_url_frame(self):
        """Click on the indexer URL frame"""
        return self._click_frame_with_press_release(self.specify_indexer_url_frame())

    # RGB Proxy URL

    def click_set_rgb_proxy_url_frame(self):
        """Click on the RGB proxy URL frame"""
        return self._click_frame_with_press_release(self.specify_rgb_proxy_url_frame())
    # Save Button

    def click_save_button(self):
        """Click on the save button to save settings"""
        return self.do_click(self.save_button()) if self.do_is_displayed(self.save_button()) else None

    def click_hide_exhausted_asset_toggle_button(self):
        """Click on the Hide exhausted asset toggle button"""
        if self.do_is_displayed(self.hide_exhausted_asset_toggle_button()):
            self.hide_exhausted_asset_toggle_button().grabFocus()
            return pressKey('space')

    def click_ask_auth_imp_question(self):
        """Click on the ask auth imp question toggle button"""
        if self.do_is_displayed(self.ask_auth_for_imp_question_toggle()):
            self.ask_auth_for_imp_question_toggle().grabFocus()
            return pressKey('space')

    def set_keyring_enable_ci(self):
        """Use Plaintext keyring (enable) only in CI."""
        if os.getenv('CI') == 'true':
            os.environ['PYTHON_KEYRING_BACKEND'] = 'keyrings.alt.file.PlaintextKeyring'
