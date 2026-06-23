"""
Pulse glow animation for the fingerprint icon.
Creates a smooth, breathing glow effect while waiting for finger placement.
"""

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup,
    QParallelAnimationGroup, pyqtProperty, QTimer, Qt
)
from PyQt6.QtGui import QColor, QPainter, QRadialGradient, QPen
from PyQt6.QtWidgets import QWidget


class PulseGlowWidget(QWidget):
    """
    A widget that renders an animated pulsing glow ring.
    Used behind the fingerprint icon to create a breathing light effect.
    """

    def __init__(self, parent=None, color: str = "#3B82F6", size: int = 200):
        super().__init__(parent)
        self._glow_opacity = 0.3
        self._glow_radius = 0.7
        self._color = QColor(color)
        self._base_size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Create pulse animation
        self._animation_group = QSequentialAnimationGroup(self)

        # Expand phase
        expand_opacity = QPropertyAnimation(self, b"glow_opacity")
        expand_opacity.setDuration(1200)
        expand_opacity.setStartValue(0.15)
        expand_opacity.setEndValue(0.55)
        expand_opacity.setEasingCurve(QEasingCurve.Type.InOutSine)

        expand_radius = QPropertyAnimation(self, b"glow_radius")
        expand_radius.setDuration(1200)
        expand_radius.setStartValue(0.55)
        expand_radius.setEndValue(0.85)
        expand_radius.setEasingCurve(QEasingCurve.Type.InOutSine)

        expand = QParallelAnimationGroup()
        expand.addAnimation(expand_opacity)
        expand.addAnimation(expand_radius)

        # Contract phase
        contract_opacity = QPropertyAnimation(self, b"glow_opacity")
        contract_opacity.setDuration(1200)
        contract_opacity.setStartValue(0.55)
        contract_opacity.setEndValue(0.15)
        contract_opacity.setEasingCurve(QEasingCurve.Type.InOutSine)

        contract_radius = QPropertyAnimation(self, b"glow_radius")
        contract_radius.setDuration(1200)
        contract_radius.setStartValue(0.85)
        contract_radius.setEndValue(0.55)
        contract_radius.setEasingCurve(QEasingCurve.Type.InOutSine)

        contract = QParallelAnimationGroup()
        contract.addAnimation(contract_opacity)
        contract.addAnimation(contract_radius)

        self._animation_group.addAnimation(expand)
        self._animation_group.addAnimation(contract)
        self._animation_group.setLoopCount(-1)  # Infinite loop

    def start(self):
        """Start the pulse animation."""
        self._animation_group.start()

    def stop(self):
        """Stop the pulse animation."""
        self._animation_group.stop()

    def set_color(self, color: str):
        """Change the glow color."""
        self._color = QColor(color)
        self.update()

    # --- Qt Properties for animation ---

    @pyqtProperty(float)
    def glow_opacity(self):
        return self._glow_opacity

    @glow_opacity.setter
    def glow_opacity(self, value):
        self._glow_opacity = value
        self.update()

    @pyqtProperty(float)
    def glow_radius(self):
        return self._glow_radius

    @glow_radius.setter
    def glow_radius(self, value):
        self._glow_radius = value
        self.update()

    def paintEvent(self, event):
        """Paint the glow effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        max_radius = min(self.width(), self.height()) / 2

        # Outer glow gradient
        gradient = QRadialGradient(center_x, center_y, max_radius * self._glow_radius)
        inner_color = QColor(self._color)
        inner_color.setAlphaF(self._glow_opacity * 0.8)
        mid_color = QColor(self._color)
        mid_color.setAlphaF(self._glow_opacity * 0.4)
        outer_color = QColor(self._color)
        outer_color.setAlphaF(0)

        gradient.setColorAt(0.0, inner_color)
        gradient.setColorAt(0.5, mid_color)
        gradient.setColorAt(1.0, outer_color)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(
            int(center_x - max_radius), int(center_y - max_radius),
            int(max_radius * 2), int(max_radius * 2)
        )

        # Inner bright ring
        ring_radius = max_radius * self._glow_radius * 0.65
        ring_color = QColor(self._color)
        ring_color.setAlphaF(self._glow_opacity * 0.7)
        pen = QPen(ring_color, 2.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            int(center_x - ring_radius), int(center_y - ring_radius),
            int(ring_radius * 2), int(ring_radius * 2)
        )

        painter.end()
