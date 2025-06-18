# pylint: disable=too-many-instance-attributes, too-many-statements,invalid-name
"""A custom toggle switch widget for Qt applications using PySide6."""
from __future__ import annotations

from PySide6.QtCore import Property
from PySide6.QtCore import QPoint
from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Slot
from PySide6.QtGui import QBrush
from PySide6.QtGui import QColor
from PySide6.QtGui import QCursor
from PySide6.QtGui import QFont
from PySide6.QtGui import QPainter
from PySide6.QtGui import QPaintEvent
from PySide6.QtGui import QPen
from PySide6.QtWidgets import QCheckBox


class ToggleSwitch(QCheckBox):
    """
    A custom toggle switch widget for Qt applications using PySide6.
    """

    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)
    _black_pen = QPen(Qt.black)

    def __init__(
        self,
        parent=None,
    ):
        """
        Initialize the ToggleSwitch widget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            checked_color (str, optional): Color of the bar when checked. Defaults to "#01A781".
            handle_color (QColor, optional): Color of the handle. Defaults to Qt.white.
            h_scale (float, optional): Horizontal scale factor. Defaults to 1.0.
            v_scale (float, optional): Vertical scale factor. Defaults to 1.0.
            fontSize (int, optional): Font size for the text. Defaults to 10.
        """
        super().__init__(parent)
        checked_color = '#01A781'
        handle_color = Qt.white
        h_scale = 1.0
        v_scale = 1.0
        fontSize = 10
        self._bar_brush = QBrush(Qt.gray)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())
        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(Qt.white)

        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0
        self._h_scale = h_scale
        self._v_scale = v_scale
        self._fontSize = fontSize
        self.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.stateChanged.connect(self.handle_state_change)

    def sizeHint(self):
        """
        Provide a recommended size for the toggle switch.

        Returns:
            QSize: The recommended size.
        """
        return QSize(58, 45)

    def hitButton(self, pos: QPoint):
        """
        Determine if a given point is within the toggle switch's clickable area.

        Args:
            pos (QPoint): The point to check.

        Returns:
            bool: True if the point is within the clickable area, False otherwise.
        """
        return self.contentsRect().contains(pos)

    def paintEvent(self, _e: QPaintEvent):
        """
        Paint the toggle switch.

        Args:
            e (QPaintEvent): The paint event.
        """
        contRect = self.contentsRect()
        width = contRect.width() * self._h_scale
        height = contRect.height() * self._v_scale
        handleRadius = round(0.24 * height)

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(0, 0, width - handleRadius, 0.42 * height)
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        trailLength = contRect.width() * self._h_scale - 2 * handleRadius
        xLeft = contRect.center().x() - (trailLength + handleRadius) / 2
        xPos = xLeft + handleRadius + trailLength * self._handle_position

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

            p.setPen(self._black_pen)
            p.setFont(QFont('Helvetica', self._fontSize, 75))
            p.drawText(
                xLeft + handleRadius / 2,
                contRect.center().y() + handleRadius / 2, '',
            )
        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.setPen(self._light_grey_pen)
        p.drawEllipse(
            QPointF(xPos, barRect.center().y()),
            handleRadius, handleRadius,
        )
        p.end()

    @Slot(int)
    def handle_state_change(self, value):
        """
        Handle changes in the toggle switch's state.

        Args:
            value (int): The new state value.
        """
        self._handle_position = 1 if value else 0

    @Property(float)
    def handle_toggle_position(self):
        """
        Property for the handle position.

        Returns:
            float: The current handle position.
        """
        return self._handle_position

    @handle_toggle_position.setter
    def handle_position(self, pos):
        """
        Set the handle position and trigger a repaint.

        Args:
            pos (float): The new handle position.
        """
        self._handle_position = pos
        self.update()

    def setH_scale(self, value):
        """
        Set the horizontal scale factor and trigger a repaint.

        Args:
            value (float): The new horizontal scale factor.
        """
        self._h_scale = value
        self.update()

    def setV_scale(self, value):
        """
        Set the vertical scale factor and trigger a repaint.

        Args:
            value (float): The new vertical scale factor.
        """
        self._v_scale = value
        self.update()

    def setFontSize(self, value):
        """
        Set the font size and trigger a repaint.

        Args:
            value (int): The new font size.
        """
        self._fontSize = value
        self.update()
