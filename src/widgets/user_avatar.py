"""
User avatar widget — displays the user's profile picture or initials.
"""

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QColor, QPainter, QPixmap, QPainterPath, QFont,
    QLinearGradient, QBrush, QPen
)
from PyQt6.QtWidgets import QWidget


class UserAvatarWidget(QWidget):
    """Circular user avatar with gradient fallback."""

    def __init__(self, parent=None, size: int = 90):
        super().__init__(parent)
        self._size = size
        self._pixmap = None
        self._initials = "U"
        self._display_name = ""
        self.setFixedSize(size + 20, size + 40)  # Extra space for name
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_avatar(self, path: str):
        """Load avatar from file path."""
        try:
            px = QPixmap(path)
            if not px.isNull():
                self._pixmap = px.scaled(
                    self._size, self._size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
        except Exception:
            pass

    def set_initials(self, name: str):
        """Set initials from display name."""
        self._display_name = name
        parts = name.strip().split()
        if len(parts) >= 2:
            self._initials = (parts[0][0] + parts[-1][0]).upper()
        elif parts:
            self._initials = parts[0][0].upper()
        else:
            self._initials = "U"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        avatar_cy = self._size / 2 + 2
        r = self._size / 2

        if self._pixmap and not self._pixmap.isNull():
            # Clip to circle and draw image
            path = QPainterPath()
            path.addEllipse(QRectF(cx - r, avatar_cy - r, r * 2, r * 2))
            painter.setClipPath(path)
            painter.drawPixmap(
                int(cx - r), int(avatar_cy - r),
                int(r * 2), int(r * 2),
                self._pixmap
            )
            painter.setClipping(False)
        else:
            # Gradient background circle
            gradient = QLinearGradient(cx - r, avatar_cy - r, cx + r, avatar_cy + r)
            gradient.setColorAt(0, QColor("#6366F1"))
            gradient.setColorAt(1, QColor("#3B82F6"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(
                int(cx - r), int(avatar_cy - r), int(r * 2), int(r * 2)
            )

            # Draw initials
            font = QFont("Inter", int(r * 0.65))
            font.setWeight(QFont.Weight.Light)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255, 230))
            painter.drawText(
                QRectF(cx - r, avatar_cy - r, r * 2, r * 2),
                Qt.AlignmentFlag.AlignCenter,
                self._initials
            )

        # Circle border
        border_color = QColor(255, 255, 255, 40)
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            int(cx - r), int(avatar_cy - r), int(r * 2), int(r * 2)
        )

        # Display name below avatar
        if self._display_name:
            name_font = QFont("Inter", 18)
            name_font.setWeight(QFont.Weight.Normal)
            painter.setFont(name_font)
            painter.setPen(QColor(255, 255, 255, 230))
            name_rect = QRectF(0, avatar_cy + r + 8, self.width(), 30)
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, self._display_name)

        painter.end()
