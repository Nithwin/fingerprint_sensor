"""
Particle burst effect for success/celebration moments.
"""

import math
import random
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget


class Particle:
    def __init__(self, x, y, angle, speed, color, size):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.size = size
        self.life = 1.0
        self.decay = random.uniform(0.012, 0.03)
        self.gravity = 0.08

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.98
        self.life -= self.decay
        self.size = max(0, self.size * 0.98)

    @property
    def alive(self):
        return self.life > 0 and self.size > 0.3


class ParticleBurstWidget(QWidget):
    """Spawns a burst of colored particles from center."""

    def __init__(self, parent=None, size: int = 300):
        super().__init__(parent)
        self._particles: list[Particle] = []
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def burst(self, colors=None, count=40):
        """Emit a burst of particles."""
        if colors is None:
            colors = ["#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE", "#FFFFFF"]

        cx, cy = self.width() / 2, self.height() / 2
        self._particles.clear()
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            size = random.uniform(2, 6)
            color = QColor(random.choice(colors))
            self._particles.append(Particle(cx, cy, angle, speed, color, size))
        self._timer.start()

    def _tick(self):
        self._particles = [p for p in self._particles if p.alive]
        for p in self._particles:
            p.update()
        if not self._particles:
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        if not self._particles:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self._particles:
            c = QColor(p.color)
            c.setAlphaF(max(0, min(1, p.life)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c)
            painter.drawEllipse(int(p.x - p.size/2), int(p.y - p.size/2), int(p.size), int(p.size))
        painter.end()
