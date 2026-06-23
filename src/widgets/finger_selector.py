"""
Finger selector widget — visual hand diagram for selecting which finger to enroll.
"""

from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QPainterPath, QFont,
    QLinearGradient, QBrush
)
from PyQt6.QtWidgets import QWidget

from src.fingerprint_dbus import FINGER_NAMES


# Finger positions on the hand (relative coordinates 0-1)
# Left hand finger tip positions
LEFT_FINGER_POSITIONS = {
    "left-thumb":          (0.82, 0.62, 22, 28),
    "left-index-finger":   (0.28, 0.18, 18, 26),
    "left-middle-finger":  (0.42, 0.10, 18, 28),
    "left-ring-finger":    (0.56, 0.15, 17, 26),
    "left-little-finger":  (0.70, 0.25, 15, 24),
}

# Right hand finger tip positions
RIGHT_FINGER_POSITIONS = {
    "right-thumb":          (0.18, 0.62, 22, 28),
    "right-index-finger":   (0.72, 0.18, 18, 26),
    "right-middle-finger":  (0.58, 0.10, 18, 28),
    "right-ring-finger":    (0.44, 0.15, 17, 26),
    "right-little-finger":  (0.30, 0.25, 15, 24),
}


class FingerSelectorWidget(QWidget):
    """
    Visual hand diagram where users click to select which finger to enroll.
    Shows both hands with clickable finger tips.
    """

    finger_selected = pyqtSignal(str)  # Emits finger name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(700, 380)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._selected = None
        self._hovered = None
        self._enrolled: set[str] = set()
        self.setMouseTracking(True)

    def set_enrolled_fingers(self, fingers: list[str]):
        """Mark which fingers are already enrolled."""
        self._enrolled = set(fingers)
        self.update()

    def _get_all_positions(self):
        """Get all finger positions mapped to widget coordinates."""
        positions = {}
        # Left hand (left side of widget)
        lw, lh = 320, 350
        lx, ly = 10, 15
        for name, (rx, ry, w, h) in LEFT_FINGER_POSITIONS.items():
            positions[name] = (lx + rx * lw, ly + ry * lh, w, h)

        # Right hand (right side of widget)
        rw, rh = 320, 350
        rx_off, ry_off = 370, 15
        for name, (rx, ry, w, h) in RIGHT_FINGER_POSITIONS.items():
            positions[name] = (rx_off + rx * rw, ry_off + ry * rh, w, h)

        return positions

    def _finger_at(self, pos):
        """Get finger name at given position, or None."""
        for name, (x, y, w, h) in self._get_all_positions().items():
            dist = ((pos.x() - x) ** 2 + (pos.y() - y) ** 2) ** 0.5
            if dist < max(w, h):
                return name
        return None

    def mouseMoveEvent(self, event):
        finger = self._finger_at(event.pos())
        if finger != self._hovered:
            self._hovered = finger
            self.update()

    def mousePressEvent(self, event):
        finger = self._finger_at(event.pos())
        if finger:
            self._selected = finger
            self.update()
            self.finger_selected.emit(finger)

    def leaveEvent(self, event):
        self._hovered = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Title labels
        font = QFont("Inter", 14)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(QRectF(10, 340, 320, 30), Qt.AlignmentFlag.AlignCenter, "Left Hand")
        painter.drawText(QRectF(370, 340, 320, 30), Qt.AlignmentFlag.AlignCenter, "Right Hand")

        # Draw stylized hands
        self._draw_hand(painter, 10, 15, 320, 330, is_left=True)
        self._draw_hand(painter, 370, 15, 320, 330, is_left=False)

        # Draw finger hotspots
        positions = self._get_all_positions()
        for name, (x, y, w, h) in positions.items():
            is_enrolled = name in self._enrolled
            is_hovered = name == self._hovered
            is_selected = name == self._selected

            # Determine color
            if is_selected:
                color = QColor("#3B82F6")
                opacity = 0.9
            elif is_enrolled:
                color = QColor("#10B981")
                opacity = 0.7
            elif is_hovered:
                color = QColor("#60A5FA")
                opacity = 0.6
            else:
                color = QColor(255, 255, 255)
                opacity = 0.2

            # Draw finger tip circle
            color.setAlphaF(opacity)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(int(x - w/2), int(y - h/2), w, h)

            # Border
            border = QColor(255, 255, 255, 100 if not is_hovered else 200)
            painter.setPen(QPen(border, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(int(x - w/2), int(y - h/2), w, h)

            # Enrolled checkmark
            if is_enrolled:
                painter.setPen(QPen(QColor(255, 255, 255, 220), 2))
                s = min(w, h) * 0.2
                painter.drawLine(int(x - s), int(y), int(x - s/3), int(y + s * 0.7))
                painter.drawLine(int(x - s/3), int(y + s * 0.7), int(x + s), int(y - s * 0.5))

        painter.end()

    def _draw_hand(self, painter, x, y, w, h, is_left):
        """Draw a simplified hand outline."""
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.5))
        painter.setBrush(QColor(255, 255, 255, 8))

        path = QPainterPath()
        # Simplified hand shape
        if is_left:
            path.moveTo(x + w * 0.5, y + h)         # Wrist center
            path.lineTo(x + w * 0.15, y + h)         # Wrist left
            path.lineTo(x + w * 0.12, y + h * 0.55)  # Palm left
            path.quadTo(x + w * 0.65, y + h * 0.5,
                       x + w * 0.85, y + h * 0.55)    # Thumb curve
            path.lineTo(x + w * 0.85, y + h * 0.7)   # Thumb
            path.lineTo(x + w * 0.75, y + h * 0.85)   # Palm bottom right
            path.lineTo(x + w * 0.75, y + h)          # Wrist right
            path.lineTo(x + w * 0.5, y + h)
        else:
            # Mirror for right hand
            path.moveTo(x + w * 0.5, y + h)
            path.lineTo(x + w * 0.85, y + h)
            path.lineTo(x + w * 0.88, y + h * 0.55)
            path.quadTo(x + w * 0.35, y + h * 0.5,
                       x + w * 0.15, y + h * 0.55)
            path.lineTo(x + w * 0.15, y + h * 0.7)
            path.lineTo(x + w * 0.25, y + h * 0.85)
            path.lineTo(x + w * 0.25, y + h)
            path.lineTo(x + w * 0.5, y + h)

        painter.drawPath(path)
