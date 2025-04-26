# pylint: disable=too-few-public-methods
"""This module contains the MessageBox class,
which represents the UI for message box.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from src.utils.helpers import load_stylesheet


class MessageBox():
    """This class represents a message box in the application."""

    def __init__(self, message_type, message_text):
        self.message_type = message_type
        self.message_text = message_text

        msg_box = QMessageBox()
        msg_box.setObjectName('msg_box')
        msg_box.setWindowFlags(Qt.FramelessWindowHint)
        msg_box.setStyleSheet(load_stylesheet())
        message_title = message_type.capitalize()
        msg_box.setWindowTitle(message_title)

        if self.message_type == 'information':
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(self.message_text)
        elif self.message_type == 'warning':
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText(self.message_text)
        elif self.message_type == 'critical':
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText(self.message_text)
        elif self.message_type == 'success':
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(self.message_text)
        else:
            msg_box.setIcon(QMessageBox.NoIcon)
            msg_box.setText(self.message_text)

        msg_box.exec()
