"""
Success animation — green checkmark morph with particle burst.
"""

import math
import random
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    pyqtProperty, Qt, QTimer, QPointF
)
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QWidget


class SuccessWidget(QWidget):
    """Animated success indicator with checkmark and particle burst."""

    def __init__(self, parent=None, color: str = "#10B981", size: int = 250):
        super().__init__(parent)
        self._color = QColor(color)
        self._base_size = size
        self._check_progress = 0.0
        self._ring_opacity = 0.0
        self._ring_scale = 0.8
        self._fade_opacity = 1.0
        self._particles = []
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._on_complete = None

        self._particle_timer = QTimer(self)
        self._particle_timer.setInterval(16)
        self._particle_timer.timeout.connect(self._update_particles)

    def play(self, on_complete=None):
        self._on_complete = on_complete
        self._check_progress = 0.0
        self._ring_opacity = 0.0
        self._ring_scale = 0.8
        self._fade_opacity = 1.0
        self._particles.clear()

        group = QParallelAnimationGroup(self)

        ring_op = QPropertyAnimation(self, b"ring_opacity")
        ring_op.setDuration(300)
        ring_op.setStartValue(0.0)
        ring_op.setEndValue(1.0)
        ring_op.setEasingCurve(QEasingCurve.Type.OutCubic)

        ring_sc = QPropertyAnimation(self, b"ring_scale")
        ring_sc.setDuration(400)
        ring_sc.setStartValue(0.5)
        ring_sc.setEndValue(1.0)
        ring_sc.setEasingCurve(QEasingCurve.Type.OutBack)

        check = QPropertyAnimation(self, b"check_progress")
        check.setDuration(500)
        check.setStartValue(0.0)
        check.setEndValue(1.0)
        check.setEasingCurve(QEasingCurve.Type.OutCubic)

        group.addAnimation(ring_op)
        group.addAnimation(ring_sc)
        group.addAnimation(check)
        group.finished.connect(self._on_anim_done)
        group.start()
        self._group = group

        QTimer.singleShot(250, self._spawn_particles)

    def _spawn_particles(self):
        cx, cy = self.width() / 2, self.height() / 2
        colors = ["#10B981", "#34D399", "#6EE7B7", "#A7F3D0", "#FFFFFF"]
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            size = random.uniform(2, 5)
            self._particles.append({
                "x": cx, "y": cy, "angle": angle, "speed": speed,
                "size": size, "life": 1.0, "color": random.choice(colors),
                "decay": random.uniform(0.015, 0.035)
            })
        self._particle_timer.start()

    def _update_particles(self):
        alive = []
        for p in self._particles:
            p["x"] += math.cos(p["angle"]) * p["speed"]
            p["y"] += math.sin(p["angle"]) * p["speed"]
            p["speed"] *= 0.96
            p["life"] -= p["decay"]
            p["size"] = max(0, p["size"] * 0.97)
            if p["life"] > 0 and p["size"] > 0.3:
                alive.append(p)
        self._particles = alive
        if not self._particles:
            self._particle_timer.stop()
        self.update()

    def _on_anim_done(self):
        QTimer.singleShot(400, self._fade_out)

    def _fade_out(self):
        fade = QPropertyAnimation(self, b"fade_opacity")
        fade.setDuration(400)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.InCubic)
        fade.finished.connect(
            lambda: self._on_complete() if self._on_complete else None
        )
        fade.start()
        self._fade_anim = fade

    @pyqtProperty(float)
    def check_progress(self):
        return self._check_progress

    @check_progress.setter
    def check_progress(self, v):
        self._check_progress = v
        self.update()

    @pyqtProperty(float)
    def ring_opacity(self):
        return self._ring_opacity

    @ring_opacity.setter
    def ring_opacity(self, v):
        self._ring_opacity = v
        self.update()

    @pyqtProperty(float)
    def ring_scale(self):
        return self._ring_scale

    @ring_scale.setter
    def ring_scale(self, v):
        self._ring_scale = v
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

        cx = self.width() / 2
        cy = self.height() / 2
        r = min(self.width(), self.height()) / 2 * 0.35

        # Success ring
        if self._ring_opacity > 0:
            radius = r * self._ring_scale
            fill = QColor(self._color)
            fill.setAlphaF(self._ring_opacity * 0.3)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawEllipse(
                int(cx - radius), int(cy - radius),
                int(radius * 2), int(radius * 2)
            )
            border = QColor(self._color)
            border.setAlphaF(self._ring_opacity * 0.9)
            painter.setPen(QPen(border, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                int(cx - radius), int(cy - radius),
                int(radius * 2), int(radius * 2)
            )

        # Checkmark
        if self._check_progress > 0:
            pen = QPen(QColor("#FFFFFF"), 4, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            s = r * 0.5
            p1 = QPointF(cx - s * 0.5, cy + s * 0.05)
            p2 = QPointF(cx - s * 0.1, cy + s * 0.45)
            p3 = QPointF(cx + s * 0.55, cy - s * 0.35)

            path = QPainterPath()
            if self._check_progress <= 0.4:
                t = self._check_progress / 0.4
                mid = QPointF(p1.x() + (p2.x()-p1.x())*t,
                             p1.y() + (p2.y()-p1.y())*t)
                path.moveTo(p1)
                path.lineTo(mid)
            else:
                path.moveTo(p1)
                path.lineTo(p2)
                t = (self._check_progress - 0.4) / 0.6
                end = QPointF(p2.x() + (p3.x()-p2.x())*t,
                             p2.y() + (p3.y()-p2.y())*t)
                path.lineTo(end)
            painter.drawPath(path)

        # Particles
        for p in self._particles:
            c = QColor(p["color"])
            c.setAlphaF(max(0, p["life"]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c)
            sz = int(p["size"])
            painter.drawEllipse(int(p["x"]-sz/2), int(p["y"]-sz/2), sz, sz)

        painter.end()
