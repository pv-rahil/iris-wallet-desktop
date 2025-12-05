"""
This module contains the ToasterPageObjects class, which provides methods for interacting with toaster page elements.
"""
from __future__ import annotations

import time

from accessible_constant import TOASTER_CLOSE_BUTTON
from accessible_constant import TOASTER_DESCRIPTION
from accessible_constant import TOASTER_FRAME
from accessible_constant import TOASTER_TITLE
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.dogtail_config import is_ci_environment


class ToasterPageObjects(BaseOperations):
    """
    A class representing toaster page objects.

    Attributes:
        application (object): The application instance.
        toaster_frame (lambda): A lambda function to get the toaster frame element.
        toaster_title (lambda): A lambda function to get the toaster title element.
        toaster_description (lambda): A lambda function to get the toaster description element.
        toaster_close_button (lambda): A lambda function to get the toaster close button element.
    """

    def __init__(self, application):
        """
        Initializes the ToasterPageObjects instance.

        Args:
            application (object): The application instance.
        """
        super().__init__(application)

        self.toaster_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=TOASTER_FRAME,
        )
        self.toaster_title = lambda: self.perform_action_on_element(
            role_name='label', description=TOASTER_TITLE,
        )
        self.toaster_description = lambda: self.perform_action_on_element(
            role_name='label', description=TOASTER_DESCRIPTION,
        )
        self.toaster_close_button = lambda: self.perform_action_on_element(
            role_name='push button', name=TOASTER_CLOSE_BUTTON,
        )

    def wait_for_toaster(self, timeout=15, poll_interval=0.2):
        """
        Wait for toaster to appear in AT-SPI tree with aggressive polling.

        Args:
            timeout (int): Maximum seconds to wait. Default 15s for CI.
            poll_interval (float): Seconds between polls. Default 0.2s for aggressive detection.

        Returns:
            bool: True if toaster found, False otherwise.
        """

        # Use longer timeout in CI
        if is_ci_environment():
            timeout = 20

        start_time = time.time()
        attempt = 0

        print(
            f"""[TOASTER] Waiting for toaster (timeout={
                timeout
            }s, poll_interval={poll_interval}s)...""",
        )

        while time.time() - start_time < timeout:
            attempt += 1
            try:
                # Search AT-SPI tree directly for toaster panel
                toasters = self.application.findChildren(
                    lambda node: node.roleName == 'panel'
                    and node.name == TOASTER_FRAME,
                )

                if toasters:
                    # Check if any toaster is actually showing
                    for toaster in toasters:
                        if toaster.showing:
                            print(
                                f"""[TOASTER] Found visible toaster after {
                                    attempt
                                } attempts ({time.time() - start_time:.2f}s)""",
                            )
                            return True
            except Exception as e:
                if attempt % 10 == 0:  # Log every 10th attempt to avoid spam
                    print(f"[TOASTER] Attempt {attempt}: {e}")

            time.sleep(poll_interval)

        print(f"[TOASTER] Timeout after {attempt} attempts ({timeout}s)")
        return False

    def click_toaster_frame(self):
        """
        Clicks the toaster frame element if it is displayed.

        Returns:
            bool: True if the element is clicked, False otherwise.
        """
        # First, wait for toaster to appear
        if not self.wait_for_toaster():
            print('[TOASTER] Toaster did not appear within timeout')
            return False

        # Now try to click it
        element = self.toaster_frame()
        if self.do_is_displayed(element):
            # Longer debounce for toasters
            self.do_click(element, debounce_ms=500)
            return True

        return False

    def get_toaster_title(self):
        """
        Gets the text of the toaster title element if it is displayed.

        Returns:
            str: The text of the element if it is displayed, None otherwise.
        """
        return self.do_get_text(self.toaster_title()) if self.do_is_displayed(self.toaster_title()) else None

    def get_toaster_description(self, filter_pattern=None, max_retries=3):
        """
        Gets the text of the toaster description element if it is displayed.
        Fallback: searches AT-SPI tree for the element if primary check fails.

        Args:
            filter_pattern (str, optional): A substring to filter the toaster text.
                                            If provided, only toasters containing this text will be considered.

        Returns:
            str: The text of the element if found, None otherwise.
        """
        for attempt in range(max_retries):
            try:
                # Try standard way first
                element = self.toaster_description()
                if self.do_is_displayed(element):
                    text = self.do_get_text(element)
                    if text:
                        print(
                            f"""[TOASTER] Got description (attempt {
                                attempt + 1
                            }): {text}""",
                        )
                        return text

        # Fallback / Filtered Search: Search AT-SPI tree directly
                print(
                    f'[TOASTER] Searching AT-SPI tree (filter="{
                        filter_pattern
                    }")...',
                )
                matches = self.application.findChildren(
                    lambda node: node.roleName == 'label' and node.description == TOASTER_DESCRIPTION,
                )

                if matches:
                    # Filter matches if pattern is provided
                    if filter_pattern:
                        matches = [
                            m for m in matches if m.name and filter_pattern in m.name
                        ]

                    if matches:
                        # Pick the LAST matched node
                        last_node = matches[-1]
                        if last_node.name:
                            print(f"[TOASTER] Found text: {last_node.name}")
                            return last_node.name

            except Exception as e:
                print(f"[TOASTER] Search failed: {e}")

        return None

    def click_toaster_close_button(self):
        """
        Clicks the toaster close button element if it is displayed.

        Returns:
            bool: True if the element is clicked, False otherwise.
        """
        return self.do_click(self.toaster_close_button()) if self.do_is_displayed(self.toaster_close_button()) else None
