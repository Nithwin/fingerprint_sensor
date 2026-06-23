"""
Ripple animation effect for fingerprint scanning.
Creates expanding concentric rings when a finger is detected on the sensor.
"""

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, pyqtProperty, Qt, QTimer
)
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class RippleRing:
    """Single expanding ring in the ripple effect."""

    def __init__(self):
        self.radius = 0.0
        self.opacity = 0.8
        self.line_width = 2.5


class RippleWidget(QWidget):
    """
    Renders expanding concentric ripple rings.
    Triggered when the fingerprint sensor detects a finger.
    """

    MAX_RINGS = 3

    def __init__(self, parent=None, color: str = "#F59E0B", size: int = 250):
        super().__init__(parent)
        self._color = QColor(color)
        self._rings: list[RippleRing] = []
        self._base_size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._active = False

        # Ring spawn timer
        self._spawn_timer = QTimer(self)
        self._spawn_timer.setInterval(300)
        self._spawn_timer.timeout.connect(self._spawn_ring)

        # Animation update timer (60fps)
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)  # ~60fps
        self._update_timer.timeout.connect(self._update_rings)

    def start(self):
        """Start the ripple animation."""
        self._active = True
        self._rings.clear()
        self._spawn_ring()
        self._spawn_timer.start()
        self._update_timer.start()

    def stop(self):
        """Stop the ripple animation."""
        self._active = False
        self._spawn_timer.stop()
        self._update_timer.stop()
        self._rings.clear()
        self.update()

    def set_color(self, color: str):
        """Change the ripple color."""
        self._color = QColor(color)

    def _spawn_ring(self):
        """Spawn a new expanding ring."""
        if len(self._rings) < self.MAX_RINGS:
            ring = RippleRing()
            ring.radius = 0.1
            ring.opacity = 0.7
            ring.line_width = 3.0
            self._rings.append(ring)

    def _update_rings(self):
        """Update ring positions and fade."""
        rings_to_remove = []
        for ring in self._rings:
            ring.radius += 0.015
            ring.opacity -= 0.012
            ring.line_width = max(0.5, ring.line_width - 0.03)

            if ring.opacity <= 0 or ring.radius >= 1.0:
                rings_to_remove.append(ring)

        for ring in rings_to_remove:
            self._rings.remove(ring)

        self.update()

    def paintEvent(self, event):
        """Paint the ripple rings."""
        if not self._rings:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        max_radius = min(self.width(), self.height()) / 2

        for ring in self._rings:
            radius = max_radius * ring.radius
            color = QColor(self._color)
            color.setAlphaF(max(0, min(1, ring.opacity)))

            pen = QPen(color, ring.line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                int(center_x - radius), int(center_y - radius),
                int(radius * 2), int(radius * 2)
            )

        painter.end()
