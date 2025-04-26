"""This module contains the ToastManager class,
which represents multiple toaster.
"""
from __future__ import annotations

from src.model.enums.enums_model import ToastPreset
from src.views.components.custom_toast import ToasterUi


class ToastManager:
    """A manager class for displaying various types of toast notifications."""

    @staticmethod
    def _create_toast(description, preset, **kwargs):
        """
        Create and display a toast notification with a specific style and description.

        Args:
            description (str): The text content of the toast notification.
            preset (ToastPreset): The style preset for the toast (e.g., SUCCESS, ERROR).
            **kwargs: Additional options for customization.
                - parent (optional): The parent widget for the toast.
        """
        # Only include parent if it is not None
        parent = kwargs.get('parent', None)
        if parent is not None:
            toast = ToasterUi(parent=parent, description=description)
        else:
            toast = ToasterUi(description=description)

        toast.apply_preset(preset=preset)
        toast.show_toast()

    @staticmethod
    def success(description, **kwargs):
        """
        Show a success toast notification.

        Args:
            description (str): The description of the toast.
            **kwargs: Additional customization options for the toast.
        """
        # Remove 'parent' from kwargs if it is None
        if 'parent' in kwargs and kwargs['parent'] is None:
            del kwargs['parent']

        ToastManager._create_toast(
            description, ToastPreset.SUCCESS, **kwargs,
        )

    @staticmethod
    def error(description, **kwargs):
        """
        Show an error toast notification.

        Args:
            description (str): The description of the toast.
            **kwargs: Additional customization options for the toast.
        """
        ToastManager._create_toast(
            description, ToastPreset.ERROR, **kwargs,
        )

    @staticmethod
    def warning(description, **kwargs):
        """
        Show a warning toast notification.

        Args:
            description (str): The description of the toast.
            **kwargs: Additional customization options for the toast.
        """
        ToastManager._create_toast(
            description, ToastPreset.WARNING, **kwargs,
        )

    @staticmethod
    def info(description, **kwargs):
        """
        Show an informational toast notification.

        Args:
            description (str): The description of the toast.
            **kwargs: Additional customization options for the toast.
        """
        ToastManager._create_toast(
            description, ToastPreset.INFORMATION, **kwargs,
        )

    @staticmethod
    def show_toast(parent, preset, description='', **kwargs):
        """
        Show a toast notification based on the preset type.

        Args:
            parent: The parent widget for the toast. If None, it will not be passed.
            preset (ToastPreset): The style preset for the toast.
            title (str): The title of the toast.
            description (str): The description of the toast.
            **kwargs: Additional customization options for the toast.
        """
        # Only include 'parent' in kwargs if it's not None
        if parent is not None:
            kwargs['parent'] = parent

        if preset == ToastPreset.SUCCESS:
            ToastManager.success(description, **kwargs)
        elif preset == ToastPreset.ERROR:
            ToastManager.error(description, **kwargs)
        elif preset == ToastPreset.WARNING:
            ToastManager.warning(description, **kwargs)
        elif preset == ToastPreset.INFORMATION:
            ToastManager.info(description, **kwargs)
        else:
            raise ValueError(f'Unsupported ToastPreset: {preset}')
