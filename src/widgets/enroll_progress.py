"""
Enrollment progress widget — shows swipe count and progress during enrollment.
"""

import math
from PyQt6.QtCore import (
    Qt, QRectF, QTimer, pyqtProperty, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QConicalGradient
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class EnrollProgressWidget(QWidget):
    """
    Circular progress ring showing enrollment progress.
    Displays current stage (e.g., "3 of 5") with animation.
    """

    def __init__(self, parent=None, total_stages: int = 5, size: int = 200):
        super().__init__(parent)
        self._total = total_stages
        self._current = 0
        self._progress = 0.0  # 0.0 to 1.0 animated
        self._pulse_opacity = 0.0
        self.setFixedSize(size + 40, size + 80)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._size = size

        # Status label below ring
        self._label = QLabel("Place your finger on the sensor")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
            }
        """)

    def set_total_stages(self, total: int):
        self._total = total

    def advance(self):
        """Advance to next stage with animation."""
        self._current += 1
        target = self._current / self._total

        anim = QPropertyAnimation(self, b"progress")
        anim.setDuration(400)
        anim.setStartValue(self._progress)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim = anim

        # Brief pulse
        pulse = QPropertyAnimation(self, b"pulse_opacity")
        pulse.setDuration(300)
        pulse.setKeyValueAt(0, 0.0)
        pulse.setKeyValueAt(0.3, 0.5)
        pulse.setKeyValueAt(1.0, 0.0)
        pulse.start()
        self._pulse_anim = pulse

    def reset(self):
        self._current = 0
        self._progress = 0.0
        self.update()

    def set_message(self, text: str):
        self._label.setText(text)

    @pyqtProperty(float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, v):
        self._progress = v
        self.update()

    @pyqtProperty(float)
    def pulse_opacity(self):
        return self._pulse_opacity

    @pulse_opacity.setter
    def pulse_opacity(self, v):
        self._pulse_opacity = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = self._size / 2 + 10
        r = self._size / 2 - 10

        # Background ring
        bg_pen = QPen(QColor(255, 255, 255, 25), 6)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Progress ring
        if self._progress > 0:
            progress_color = QColor("#3B82F6")
            progress_pen = QPen(progress_color, 6)
            progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(progress_pen)

            span = int(-self._progress * 360 * 16)
            start = 90 * 16
            painter.drawArc(
                QRectF(cx - r, cy - r, r * 2, r * 2),
                start, span
            )

        # Pulse effect
        if self._pulse_opacity > 0:
            pulse_color = QColor("#3B82F6")
            pulse_color.setAlphaF(self._pulse_opacity * 0.3)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(pulse_color)
            painter.drawEllipse(QRectF(cx - r - 5, cy - r - 5, (r + 5) * 2, (r + 5) * 2))

        # Stage text
        font = QFont("Inter", 36)
        font.setWeight(QFont.Weight.Light)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 230))
        painter.drawText(
            QRectF(cx - r, cy - r, r * 2, r * 2),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._current}/{self._total}"
        )

        # Label
        label_font = QFont("Inter", 13)
        painter.setFont(label_font)
        painter.setPen(QColor(255, 255, 255, 170))
        label_rect = QRectF(0, cy + r + 12, self.width(), 30)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._label.text())

        painter.end()
