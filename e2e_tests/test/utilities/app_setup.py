# pylint: disable=too-many-instance-attributes, redefined-outer-name, consider-using-with
"""
This module provides a test environment for the Iris Wallet application.
It includes classes and fixtures for setting up and tearing down the test environment.
"""
from __future__ import annotations

import os
import signal
import subprocess
import time
import shutil

import keyring
import pytest
from dogtail.tree import root

from accessible_constant import APP1_NAME, FAKEUSB_MOUNT_PATH
from accessible_constant import APP2_NAME, APP3_NAME
from accessible_constant import FIRST_APPLICATION, SECOND_APPLICATION, THIRD_APPLICATION
from accessible_constant import FIRST_APPLICATION_PATH, SECOND_APPLICATION_PATH, THIRD_APPLICATION_PATH
from accessible_constant import FIRST_SERVICE, SECOND_SERVICE, THIRD_SERVICE
from accessible_constant import REQUIRE_USB_VARIANTS
from e2e_tests.test.features.main_features import MainFeatures
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.reset_app import delete_app_data
from e2e_tests.test.utilities.translation_utils import TranslationManager
from e2e_tests.test.utilities.fake_usb import FakeUSB
from src.utils.constant import APP_NAME
from src.utils.constant import IS_NATIVE_AUTHENTICATION_ENABLED
from src.utils.constant import NATIVE_LOGIN_ENABLED
from src.utils.local_store import local_store
from src.version import __version__


class TestEnvironment:
    """
    A class representing the test environment for the iris wallet application.
    """

    def __init__(self, multi_instance=True, wallet_variant_name: str | None = None):
        """
        Initializes the test environment.

        Args:
            multi_instance (bool): If True, launches both applications. Otherwise, only launches one.
        """
        # Backward-compatible: bool -> 1 or 2, int -> exact number of instances
        if isinstance(multi_instance, bool):
            self.num_instances = 2 if multi_instance else 1
        elif isinstance(multi_instance, int):
            self.num_instances = max(1, min(3, multi_instance))
        else:
            self.num_instances = 2
        # Initialize process attributes
        self.first_process = None
        self.second_process = None
        self.rgb_processes = []
        self.third_process = None

        # Determine whether to enable Fake USB environment based on variant
        self.wallet_variant_name = (wallet_variant_name or '').lower()
        # Lazy-create FakeUSB only when needed during launch
        self.fake_usb = None

        self.reset_app_data()
        self.remove_keyring_entries(service=FIRST_SERVICE, app_name=APP1_NAME)
        self.remove_keyring_entries(service=SECOND_SERVICE, app_name=APP2_NAME)
        if self.num_instances >= 3:
            self.remove_keyring_entries(service=THIRD_SERVICE, app_name=APP3_NAME)

        self.launch_applications()

    def reset_app_data(self):
        """Resets the app data by deleting relevant directories."""
        actual_path = os.path.dirname(local_store.get_path())
        app1_data = actual_path.replace(APP_NAME, FIRST_APPLICATION_PATH)
        app2_data = actual_path.replace(APP_NAME, SECOND_APPLICATION_PATH)
        app3_data = actual_path.replace(APP_NAME, THIRD_APPLICATION_PATH)

        delete_app_data(app1_data)
        if self.num_instances >= 2:
            delete_app_data(app2_data)
        if self.num_instances >= 3:
            delete_app_data(app3_data)

        shutil.rmtree(FAKEUSB_MOUNT_PATH, ignore_errors=True)

    def launch_applications(self):
        """Launches the required iris wallet applications and maximizes the windows."""
        env = None
        if self.wallet_variant_name in REQUIRE_USB_VARIANTS:
            self.fake_usb = FakeUSB()
            env = self.fake_usb.setup()

        self.first_process = subprocess.Popen(
            [f"e2e_tests/applications/iris-wallet-vault_{APP1_NAME}-{__version__}-x86_64.AppImage"],
            env=env,
        )
        self.wait_for_application(FIRST_APPLICATION)

        # Maximize first application window
        subprocess.run(
            [
                'wmctrl', '-r', FIRST_APPLICATION, '-b',
                'add,maximized_vert,maximized_horz',
            ],
            check=True,
        )
        self.first_application = root.child(
            roleName='frame', name=FIRST_APPLICATION,
        )
        self.first_page_features = MainFeatures(self.first_application)
        self.first_page_objects = MainPageObjects(self.first_application)
        self.first_page_operations = BaseOperations(self.first_application)
        if self.num_instances >= 2:
            self.second_process = subprocess.Popen(
                [f"e2e_tests/applications/iris-wallet-vault_{APP2_NAME}-{__version__}-x86_64.AppImage"],
                env=env,
            )
            self.wait_for_application(SECOND_APPLICATION)

            # Maximize second application window
            subprocess.run(
                [
                    'wmctrl', '-r', SECOND_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            self.second_application = root.child(
                roleName='frame', name=SECOND_APPLICATION,
            )
            self.second_page_features = MainFeatures(self.second_application)
            self.second_page_objects = MainPageObjects(self.second_application)
            self.second_page_operations = BaseOperations(
                self.second_application,
            )

        if self.num_instances >= 3:
            self.third_process = subprocess.Popen(
                [f"e2e_tests/applications/iris-wallet-vault_{APP3_NAME}-{__version__}-x86_64.AppImage"],
                env=env,
            )
            self.wait_for_application(THIRD_APPLICATION)

            subprocess.run(
                [
                    'wmctrl', '-r', THIRD_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            self.third_application = root.child(
                roleName='frame', name=THIRD_APPLICATION,
            )
            self.third_page_features = MainFeatures(self.third_application)
            self.third_page_objects = MainPageObjects(self.third_application)
            self.third_page_operations = BaseOperations(
                self.third_application,
            )

    def wait_for_application(self, app_name, timeout=10):
        """Waits for an application to be fully loaded dynamically."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if root.child(roleName='frame', name=app_name):
                    return True
            except Exception:
                pass
            time.sleep(0.5)  # Avoid excessive CPU usage
        raise TimeoutError(
            f"""Application '{app_name}' failed to start within {
                timeout
            } seconds""",
        )

    def terminate_process(self, process):
        """Gracefully terminates a process and its children."""
        if not process:
            return

        pid = process.pid
        if not pid:
            return

        os.kill(pid, signal.SIGKILL)

    def terminate(self):
        """Cleans up the test environment by shutting down applications"""
        self.terminate_process(self.first_process)
        if self.num_instances >= 2:
            self.terminate_process(self.second_process)
        if self.num_instances >= 3:
            self.terminate_process(self.third_process)

        if self.fake_usb:
            self.fake_usb.cleanup()

    def restart(self, reset_data=True):
        """Restarts the application by terminating, optionally resetting data, and relaunching."""
        self.terminate()

        if reset_data:
            self.reset_app_data()

        self.launch_applications()

    def restart_application(self, which: str = 'second', reset_data: bool = False):
        """Restart only a specific application window (first|second|third).

        Args:
            which: One of 'first', 'second', 'third'. Defaults to 'second'.
            reset_data: If True, clears ONLY that app's data before relaunching.
        """
        # Compute paths for selective reset
        actual_path = os.path.dirname(local_store.get_path())
        app1_data = actual_path.replace(APP_NAME, FIRST_APPLICATION_PATH)
        app2_data = actual_path.replace(APP_NAME, SECOND_APPLICATION_PATH)
        app3_data = actual_path.replace(APP_NAME, THIRD_APPLICATION_PATH)

        # Choose env if FakeUSB is enabled (for offline variants)
        env = self.fake_usb.setup() if self.fake_usb else None

        if which == 'first':
            self.terminate_process(self.first_process)
            if reset_data:
                delete_app_data(app1_data)
            # Relaunch first
            self.first_process = subprocess.Popen(
                [f"e2e_tests/applications/iris-wallet-vault_{APP1_NAME}-{__version__}-x86_64.AppImage"],
                env=env,
            )
            self.wait_for_application(FIRST_APPLICATION)
            subprocess.run(['wmctrl', '-r', FIRST_APPLICATION, '-b', 'add,maximized_vert,maximized_horz'], check=True)
            self.first_application = root.child(roleName='frame', name=FIRST_APPLICATION)
            self.first_page_features = MainFeatures(self.first_application)
            self.first_page_objects = MainPageObjects(self.first_application)
            self.first_page_operations = BaseOperations(self.first_application)
            return

        if which == 'second':
            self.terminate_process(self.second_process)
            if reset_data:
                delete_app_data(app2_data)
            # Relaunch second
            self.second_process = subprocess.Popen(
                [f"e2e_tests/applications/iris-wallet-vault_{APP2_NAME}-{__version__}-x86_64.AppImage"],
                env=env,
            )
            self.wait_for_application(SECOND_APPLICATION)
            subprocess.run(['wmctrl', '-r', SECOND_APPLICATION, '-b', 'add,maximized_vert,maximized_horz'], check=True)
            self.second_application = root.child(roleName='frame', name=SECOND_APPLICATION)
            self.second_page_features = MainFeatures(self.second_application)
            self.second_page_objects = MainPageObjects(self.second_application)
            self.second_page_operations = BaseOperations(self.second_application)
            return

        if which == 'third':
            self.terminate_process(self.third_process)
            if reset_data:
                delete_app_data(app3_data)
            # Relaunch third
            self.third_process = subprocess.Popen(
                [f"e2e_tests/applications/iris-wallet-vault_{APP3_NAME}-{__version__}-x86_64.AppImage"],
                env=env,
            )
            self.wait_for_application(THIRD_APPLICATION)
            subprocess.run(['wmctrl', '-r', THIRD_APPLICATION, '-b', 'add,maximized_vert,maximized_horz'], check=True)
            self.third_application = root.child(roleName='frame', name=THIRD_APPLICATION)
            self.third_page_features = MainFeatures(self.third_application)
            self.third_page_objects = MainPageObjects(self.third_application)
            self.third_page_operations = BaseOperations(self.third_application)
            return

        raise ValueError("which must be one of: 'first', 'second', 'third'")

    def restart_second(self, reset_data: bool = False):
        """Convenience wrapper to restart only the second application."""
        self.restart_application('second', reset_data=reset_data)

    def remove_keyring_entries(self, service, app_name):
        """Removes keyring entries for a given service and application name."""
        keys = [
            NATIVE_LOGIN_ENABLED,
            IS_NATIVE_AUTHENTICATION_ENABLED,
        ]

        for key in keys:
            try:
                keyring.delete_password(service, f"{key}_{app_name}")
                print(f"Removed {key}{app_name} from keyring.")
            except keyring.errors.PasswordDeleteError:
                print(f"No entry found for {key}_{app_name}.")


@pytest.fixture(scope='module')
def test_environment(request, wallet_variant_name: str):
    """
    A fixture that sets up and tears down the test environment.

    Use `request.param` to determine if multi-instance should be enabled.
    """
    multi_instance = getattr(request, 'param', True)
    env = TestEnvironment(
        multi_instance=multi_instance,
        wallet_variant_name=wallet_variant_name,
    )
    yield env
    env.terminate()


@pytest.fixture
def wallets_and_operations(test_environment: TestEnvironment) -> WalletTestSetup:
    """
    A fixture that initializes the wallets and operations objects.
    """
    return WalletTestSetup(
        first_page_features=test_environment.first_page_features,
        second_page_features=test_environment.second_page_features
        if test_environment.num_instances >= 2
        else None,
        first_page_objects=test_environment.first_page_objects,
        second_page_objects=test_environment.second_page_objects
        if test_environment.num_instances >= 2
        else None,
        first_page_operations=test_environment.first_page_operations,
        second_page_operations=test_environment.second_page_operations
        if test_environment.num_instances >= 2
        else None,
        third_page_features=test_environment.third_page_features
        if test_environment.num_instances >= 3
        else None,
        third_page_objects=test_environment.third_page_objects
        if test_environment.num_instances >= 3
        else None,
        third_page_operations=test_environment.third_page_operations
        if test_environment.num_instances >= 3
        else None,
    )


@pytest.fixture(scope='session', autouse=True)
def load_qm_translation():
    """Load the .qm translation file once per test session."""
    TranslationManager.load_translation()
