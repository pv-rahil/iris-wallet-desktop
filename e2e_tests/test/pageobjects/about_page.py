# pylint: disable=too-many-instance-attributes
"""This module contains the page object for about page"""
from __future__ import annotations

from dogtail.rawinput import keyCombo
from dogtail.tree import root

from accessible_constant import DOWNLOAD_DEBUG_LOG
from accessible_constant import FILE_CHOOSER
from accessible_constant import INDEXER_URL_ACCESSIBLE_DESCRIPTION
from accessible_constant import INDEXER_URL_COPY_BUTTON
from accessible_constant import RGB_PROXY_URL_ACCESSIBLE_DESCRIPTION
from accessible_constant import RGB_PROXY_URL_COPY_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class AboutPageObjects(BaseOperations):
    """Class for about page object"""

    def __init__(self, application):
        super().__init__(application)

        self.indexer_url_label = lambda: self.perform_action_on_element(
            role_name='label', description=INDEXER_URL_ACCESSIBLE_DESCRIPTION,
        )
        self.rgb_proxy_url = lambda: self.perform_action_on_element(
            role_name='label', description=RGB_PROXY_URL_ACCESSIBLE_DESCRIPTION,
        )
        self.indexer_url_copy_button = lambda: self.perform_action_on_element(
            role_name='push button', name=INDEXER_URL_COPY_BUTTON,
        )
        self.rgb_proxy_url_copy_button = lambda: self.perform_action_on_element(
            role_name='push button', name=RGB_PROXY_URL_COPY_BUTTON,
        )
        self.download_debug_log = lambda: self.perform_action_on_element(
            role_name='push button', name=DOWNLOAD_DEBUG_LOG,
        )
        self.file_explorer = lambda: root.child(
            roleName=FILE_CHOOSER,
        )

    def get_indexer_url(self):
        """Returns the indexer url"""
        return self.do_get_text(self.indexer_url_label()) if self.do_is_displayed(self.indexer_url_label()) else None

    def get_rgb_proxy_url(self):
        """Returns the rgb proxy url"""
        return self.do_get_text(self.rgb_proxy_url()) if self.do_is_displayed(self.rgb_proxy_url()) else None

    def click_indexer_url_copy_button(self):
        """Clicks on Indexer url copy button"""
        return self.do_click(self.indexer_url_copy_button()) if self.do_is_displayed(self.indexer_url_copy_button()) else None

    def click_rgb_proxy_url_copy_button(self):
        """Clicks on RGB proxy url copy button"""
        return self.do_click(self.rgb_proxy_url_copy_button()) if self.do_is_displayed(self.rgb_proxy_url_copy_button()) else None

    def click_download_debug_log(self):
        """Clicks on the download debug log button"""
        return self.do_click(self.download_debug_log()) if self.do_is_displayed(self.download_debug_log()) else None

    def press_enter(self):
        """Presses the enter key"""
        if self.do_is_displayed(self.file_explorer()):
            self.file_explorer().grabFocus()
            keyCombo('enter')
            return True
        return False

    def copying_logs_filename(self):
        """Returns the filename of the copying logs"""
        if self.do_is_displayed(self.file_explorer()):
            self.file_explorer().grabFocus()
            keyCombo('<Control>c')

            return self.do_get_copied_address()

        return None
