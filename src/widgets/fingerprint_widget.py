"""
Fingerprint icon widget with SVG rendering and state management.
Coordinates the pulse, ripple, success, and failure animations.
"""

import math
from PyQt6.QtCore import (
    Qt, QRectF, QPointF, pyqtSignal, pyqtProperty,
    QPropertyAnimation, QEasingCurve, QTimer
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QPainterPath, QRadialGradient,
    QLinearGradient, QFont
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout

from src.animations.pulse import PulseGlowWidget
from src.animations.ripple import RippleWidget
from src.animations.success import SuccessWidget
from src.animations.failure import FailureWidget


class FingerprintWidget(QWidget):
    """
    Central fingerprint icon that manages all animation states.
    
    States:
    - IDLE: Pulsing blue glow, waiting for finger
    - SCANNING: Amber ripple, finger detected
    - SUCCESS: Green checkmark + particles
    - FAILURE: Red X + shake
    """

    # Signals
    state_changed = pyqtSignal(str)

    STATE_IDLE = "idle"
    STATE_SCANNING = "scanning"
    STATE_SUCCESS = "success"
    STATE_FAILURE = "failure"

    def __init__(self, parent=None, size: int = 220):
        super().__init__(parent)
        self._size = size
        self._state = self.STATE_IDLE
        self._icon_opacity = 1.0
        self._icon_scale = 1.0
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Stacked layout for overlaying animations
        layout = QStackedLayout(self)
        layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # Animation layers
        self._pulse = PulseGlowWidget(self, "#3B82F6", size)
        self._ripple = RippleWidget(self, "#F59E0B", size)
        self._success = SuccessWidget(self, "#10B981", size)
        self._failure = FailureWidget(self, "#EF4444", size)

        layout.addWidget(self._pulse)
        layout.addWidget(self._ripple)
        layout.addWidget(self._success)
        layout.addWidget(self._failure)

        self._ripple.hide()
        self._success.hide()
        self._failure.hide()

        self.setLayout(layout)

    def set_idle(self):
        """Switch to idle state with pulsing glow."""
        self._state = self.STATE_IDLE
        self._ripple.stop()
        self._ripple.hide()
        self._success.hide()
        self._failure.hide()
        self._pulse.show()
        self._pulse.start()
        self._icon_opacity = 1.0
        self.update()
        self.state_changed.emit(self.STATE_IDLE)

    def set_scanning(self):
        """Switch to scanning state with ripple effect."""
        self._state = self.STATE_SCANNING
        self._pulse.set_color("#F59E0B")
        self._ripple.show()
        self._ripple.start()
        self._success.hide()
        self._failure.hide()
        self.update()
        self.state_changed.emit(self.STATE_SCANNING)

    def set_success(self, on_complete=None):
        """Play success animation."""
        self._state = self.STATE_SUCCESS
        self._pulse.stop()
        self._pulse.hide()
        self._ripple.stop()
        self._ripple.hide()
        self._failure.hide()
        self._success.show()
        self._success.play(on_complete=on_complete)
        self.state_changed.emit(self.STATE_SUCCESS)

    def set_failure(self, on_complete=None):
        """Play failure animation."""
        self._state = self.STATE_FAILURE
        self._pulse.stop()
        self._ripple.stop()
        self._ripple.hide()
        self._success.hide()
        self._failure.show()

        def _after_fail():
            self._failure.hide()
            self._pulse.set_color("#3B82F6")
            self.set_idle()
            if on_complete:
                on_complete()

        self._failure.play(on_complete=_after_fail)
        self.state_changed.emit(self.STATE_FAILURE)

    def paintEvent(self, event):
        """Draw the fingerprint icon on top of animations."""
        super().paintEvent(event)
        if self._state == self.STATE_SUCCESS or self._state == self.STATE_FAILURE:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._icon_opacity)

        cx = self.width() / 2
        cy = self.height() / 2
        scale = self._size * 0.15  # fingerprint size

        # Draw stylized fingerprint icon
        self._draw_fingerprint(painter, cx, cy, scale)
        painter.end()

    def _draw_fingerprint(self, painter, cx, cy, scale):
        """Draw a stylized fingerprint using curved arcs."""
        if self._state == self.STATE_SCANNING:
            color = QColor("#F59E0B")
        else:
            color = QColor("#FFFFFF")

        color.setAlphaF(0.9)
        pen = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Fingerprint ridges — concentric arcs with varying angles
        ridges = [
            (0.3, -140, 280),
            (0.45, -130, 260),
            (0.6, -120, 240),
            (0.75, -110, 220),
            (0.9, -100, 200),
            (1.05, -90, 180),
            (1.2, -80, 160),
        ]

        for (r_mult, start_angle, span_angle) in ridges:
            r = scale * r_mult
            rect = QRectF(cx - r, cy - r, r * 2, r * 2)
            painter.drawArc(rect, start_angle * 16, span_angle * 16)

        # Central dot
        dot_color = QColor(color)
        dot_color.setAlphaF(0.6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(int(cx - 2), int(cy - 2), 4, 4)
