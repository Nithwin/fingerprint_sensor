"""
Failure animation — red shake with flash.
"""

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup,
    pyqtProperty, Qt, QTimer
)
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QWidget


class FailureWidget(QWidget):
    """Red X with shake animation for failed verification."""

    def __init__(self, parent=None, color: str = "#EF4444", size: int = 250):
        super().__init__(parent)
        self._color = QColor(color)
        self._base_size = size
        self._x_progress = 0.0
        self._shake_offset = 0.0
        self._flash_opacity = 0.0
        self._fade_opacity = 1.0
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._on_complete = None

    def play(self, on_complete=None):
        """Play failure animation."""
        self._on_complete = on_complete
        self._x_progress = 0.0
        self._shake_offset = 0.0
        self._flash_opacity = 0.0
        self._fade_opacity = 1.0

        # Flash red
        flash = QPropertyAnimation(self, b"flash_opacity")
        flash.setDuration(200)
        flash.setStartValue(0.0)
        flash.setEndValue(0.5)
        flash.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Draw X
        x_anim = QPropertyAnimation(self, b"x_progress")
        x_anim.setDuration(300)
        x_anim.setStartValue(0.0)
        x_anim.setEndValue(1.0)
        x_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Shake sequence
        shake_seq = QSequentialAnimationGroup(self)
        offsets = [15, -12, 10, -7, 5, -3, 0]
        for off in offsets:
            s = QPropertyAnimation(self, b"shake_offset")
            s.setDuration(50)
            s.setEndValue(float(off))
            s.setEasingCurve(QEasingCurve.Type.Linear)
            shake_seq.addAnimation(s)

        # Sequence: flash -> X + shake
        seq = QSequentialAnimationGroup(self)
        seq.addAnimation(flash)
        seq.addAnimation(x_anim)
        seq.finished.connect(self._start_shake)
        seq.start()

        self._shake_group = shake_seq
        self._main_seq = seq

    def _start_shake(self):
        self._shake_group.finished.connect(self._after_shake)
        self._shake_group.start()

    def _after_shake(self):
        QTimer.singleShot(600, self._fade_out)

    def _fade_out(self):
        fade = QPropertyAnimation(self, b"fade_opacity")
        fade.setDuration(300)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.InCubic)
        fade.finished.connect(lambda: self._on_complete() if self._on_complete else None)
        fade.start()
        self._fade_anim = fade

    @pyqtProperty(float)
    def x_progress(self):
        return self._x_progress

    @x_progress.setter
    def x_progress(self, v):
        self._x_progress = v
        self.update()

    @pyqtProperty(float)
    def shake_offset(self):
        return self._shake_offset

    @shake_offset.setter
    def shake_offset(self, v):
        self._shake_offset = v
        self.update()

    @pyqtProperty(float)
    def flash_opacity(self):
        return self._flash_opacity

    @flash_opacity.setter
    def flash_opacity(self, v):
        self._flash_opacity = v
        self.update()

    @pyqtProperty(float)
    def fade_opacity(self):
        return self._fade_opacity

    @fade_opacity.setter
    def fade_opacity(self, v):
        self._fade_opacity = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._fade_opacity)
        painter.translate(self._shake_offset, 0)

        cx = self.width() / 2
        cy = self.height() / 2
        r = min(self.width(), self.height()) / 2 * 0.35

        # Red flash
        if self._flash_opacity > 0:
            grad = QRadialGradient(cx, cy, r * 2)
            c1 = QColor(self._color)
            c1.setAlphaF(self._flash_opacity * 0.4)
            c2 = QColor(self._color)
            c2.setAlphaF(0)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(grad)
            painter.drawEllipse(int(cx - r * 2), int(cy - r * 2), int(r * 4), int(r * 4))

        # Circle
        circle_color = QColor(self._color)
        circle_color.setAlphaF(0.3)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(circle_color)
        painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        border = QColor(self._color)
        border.setAlphaF(0.9)
        painter.setPen(QPen(border, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        # X mark
        if self._x_progress > 0:
            s = r * 0.35
            pen = QPen(QColor("#FFFFFF"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            if self._x_progress <= 0.5:
                t = self._x_progress / 0.5
                painter.drawLine(int(cx - s), int(cy - s), int(cx - s + 2 * s * t), int(cy - s + 2 * s * t))
            else:
                painter.drawLine(int(cx - s), int(cy - s), int(cx + s), int(cy + s))
                t = (self._x_progress - 0.5) / 0.5
                painter.drawLine(int(cx + s), int(cy - s), int(cx + s - 2 * s * t), int(cy - s + 2 * s * t))

        painter.end()
