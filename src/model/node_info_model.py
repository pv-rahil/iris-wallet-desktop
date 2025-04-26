# pylint: disable=too-few-public-methods
"""
This module defines the NodeInfoModel class, a Singleton responsible for storing and managing node
information data across the entire application.

The NodeInfoModel class is used to set, retrieve, and maintain node information in memory, ensuring
the data can be accessed globally without requiring multiple initializations.

It follows the Singleton pattern to guarantee that only one instance of the class exists at any
given time, preventing unnecessary duplication of data. This is useful when working with node-related
operations where centralized, consistent data management is required.
"""
from __future__ import annotations

from src.model.common_operation_model import NodeInfoResponseModel


class NodeInfoModel:
    """
    A Singleton class to manage and store the node information data for the application.

    The purpose of this class is to ensure that only one instance of the node information
    is stored in memory, allowing global access to this data throughout the application's lifecycle.
    """

    # This class variable will hold the single instance of the class.
    _instance = None

    def __new__(cls):
        """
        Create a new instance of the class or return the existing instance.

        This method is part of the Singleton pattern. It ensures that the class is only instantiated once.
        If an instance already exists, it returns that instance. Otherwise, it creates a new one.

        Returns:
            NodeInfoModel: The single instance of NodeInfoModel.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the instance variables.

        This method initializes the `_node_info` attribute to `None` when the class is first created.
        It ensures that the node information is only initialized once, even in a Singleton pattern.
        """
        if not hasattr(self, 'node_info'):
            self.node_info = None  # Initialize _node_info only once

    def get_node_info(self):
        """
        Get the stored node information.

        This method retrieves the node information that was set using `set_node_info`.
        The data is stored in memory and shared across the entire application.

        Returns:
            NodeInfoResponseModel or None: The stored node information, or None if it hasn't been set yet.
        """
        return self.node_info

    def set_node_info(self, data: NodeInfoResponseModel):
        """
        Store node information in memory.

        This method is used to set the node information that can be accessed globally.
        The data will be stored in the `_node_info` attribute, and this information can later
        be retrieved using `get_node_info`.

        Args:
            data (NodeInfoResponseModel): The node information to store in memory.
        """
        self.node_info = data
