# pylint: disable=too-many-instance-attributes, redefined-outer-name, consider-using-with
"""
This module provides a test environment for the Iris Wallet application.
It includes classes and fixtures for setting up and tearing down the test environment.
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time

import keyring
import pytest
from dogtail.tree import root

from accessible_constant import APP1_NAME
from accessible_constant import APP2_NAME
from accessible_constant import APP3_NAME
from accessible_constant import FAKEUSB_MOUNT_PATH
from accessible_constant import FIRST_APPLICATION
from accessible_constant import FIRST_APPLICATION_PATH
from accessible_constant import FIRST_SERVICE
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import SECOND_APPLICATION
from accessible_constant import SECOND_APPLICATION_PATH
from accessible_constant import SECOND_SERVICE
from accessible_constant import THIRD_APPLICATION
from accessible_constant import THIRD_APPLICATION_PATH
from accessible_constant import THIRD_SERVICE
from e2e_tests.test.features.main_features import MainFeatures
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.fake_usb import FakeUSB
from e2e_tests.test.utilities.reset_app import delete_app_data
from e2e_tests.test.utilities.translation_utils import TranslationManager
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
        # Track originally requested count before we possibly bump due to variant
        self._requested_instances = self.num_instances
        # Initialize process attributes
        self.first_process = None
        self.second_process = None
        self.rgb_processes: list = []
        self.third_process = None

        # Determine whether to enable Fake USB environment based on variant
        self.wallet_variant_name = (wallet_variant_name or '').lower()
        # Force-enable second instance ONLY for load flows when single instance requested
        if self.wallet_variant_name in LOAD_WALLET_VARIANT and self.num_instances < 2:
            self.num_instances = 2
        # Lazy-create FakeUSB only when needed during launch
        self.fake_usb = None

        self.reset_app_data()
        self.remove_keyring_entries(service=FIRST_SERVICE, app_name=APP1_NAME)
        self.remove_keyring_entries(service=SECOND_SERVICE, app_name=APP2_NAME)
        if self.num_instances >= 3:
            self.remove_keyring_entries(
                service=THIRD_SERVICE, app_name=APP3_NAME,
            )

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
            [f"e2e_tests/applications/iris-wallet-vault_{
                APP1_NAME
            }-{__version__}-x86_64.AppImage"],
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
                [f"e2e_tests/applications/iris-wallet-vault_{
                    APP2_NAME
                }-{__version__}-x86_64.AppImage"],
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
                [f"e2e_tests/applications/iris-wallet-vault_{
                    APP3_NAME
                }-{__version__}-x86_64.AppImage"],
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

    def restart_single_instance(self, reset_data: bool = True):
        """Restart only the first application instance and ensure environment runs single-instance.

        This is useful for flows where we initially needed multiple instances (e.g. load/on-device),
        but subsequent tests should continue with a single app instance only.
        """
        # Terminate any running processes (first/second/third if present)
        self.terminate()

        # Force the environment to single-instance going forward
        self.num_instances = 1

        # Optionally clear app data (first app only is strictly necessary here)
        if reset_data:
            self.reset_app_data()

        # Relaunch only the first application
        self.launch_applications()

    def reset_second_instance(self, reset_data: bool = True):
        """Reset and relaunch only the second application instance.

        This is useful when a test uses the second app to prepare credentials/backup
        for a load/restore flow in the first app, and needs the second app to be
        re-initialized immediately after the load completes for the remainder of the suite.

        Args:
            reset_data (bool): If True, clears the second app's data directory before relaunching.
        """
        # If only one instance is active, nothing to do
        if self.num_instances < 2:
            return

        # Kill only the second process
        self.terminate_process(self.second_process)
        self.second_process = None

        # Optionally clear only the second app's data
        if reset_data:
            actual_path = os.path.dirname(local_store.get_path())
            app2_data = actual_path.replace(APP_NAME, SECOND_APPLICATION_PATH)
            delete_app_data(app2_data)

        # Recreate Fake USB environment if required by variant
        env = None
        if self.wallet_variant_name in REQUIRE_USB_VARIANTS:
            # Ensure fake_usb exists (create if not yet created)
            if not self.fake_usb:
                self.fake_usb = FakeUSB()
            env = self.fake_usb.setup()

        # Relaunch second application and reinitialize its page abstractions
        self.second_process = subprocess.Popen(
            [f"e2e_tests/applications/iris-wallet-vault_{APP2_NAME}-{__version__}-x86_64.AppImage"],
            env=env,
        )
        self.wait_for_application(SECOND_APPLICATION)

        subprocess.run(
            ['wmctrl', '-r', SECOND_APPLICATION, '-b', 'add,maximized_vert,maximized_horz'],
            check=True,
        )

        self.second_application = root.child(roleName='frame', name=SECOND_APPLICATION)
        self.second_page_features = MainFeatures(self.second_application)
        self.second_page_objects = MainPageObjects(self.second_application)
        self.second_page_operations = BaseOperations(self.second_application)

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
    # Register the environment so features can trigger environment-level resets
    base_operation = BaseOperations()
    base_operation.register_current_environment(env)
    yield env
    env.terminate()


@pytest.fixture
def wallets_and_operations(test_environment: TestEnvironment):
    """
    A fixture that provides dynamic access to the TestEnvironment handles.
    """

    class _HandlesProxy:
        """
        A proxy class that provides dynamic access to the TestEnvironment handles.
        """
        def __init__(self, env: TestEnvironment):
            self._env = env

        # Features
        @property
        def first_page_features(self):
            """
            Returns the first page features.
            """
            return self._env.first_page_features

        @property
        def second_page_features(self):
            """
            Returns the second page features.
            """
            return self._env.second_page_features if self._env.num_instances >= 2 else None

        @property
        def third_page_features(self):
            """
            Returns the third page features.
            """
            return self._env.third_page_features if self._env.num_instances >= 3 else None

        # Objects
        @property
        def first_page_objects(self):
            """
            Returns the first page objects.
            """
            return self._env.first_page_objects

        @property
        def second_page_objects(self):
            """
            Returns the second page objects.
            """
            return self._env.second_page_objects if self._env.num_instances >= 2 else None

        @property
        def third_page_objects(self):
            """
            Returns the third page objects.
            """
            return self._env.third_page_objects if self._env.num_instances >= 3 else None

        # Operations
        @property
        def first_page_operations(self):
            """
            Returns the first page operations.
            """
            return self._env.first_page_operations

        @property
        def second_page_operations(self):
            """
            Returns the second page operations.
            """
            return self._env.second_page_operations if self._env.num_instances >= 2 else None

        @property
        def third_page_operations(self):
            """
            Returns the third page operations.
            """
            return self._env.third_page_operations if self._env.num_instances >= 3 else None

    return _HandlesProxy(test_environment)


@pytest.fixture(scope='session', autouse=True)
def load_qm_translation():
    """Load the .qm translation file once per test session."""
    TranslationManager.load_translation()
