"""
Clock widget — shows time and date on the lock screen.
"""

from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QFont, QFontDatabase
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ClockWidget(QWidget):
    """Displays current time and date with fade-in animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._opacity = 0.0

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        # Time label
        self._time_label = QLabel("00:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 72px;
                font-weight: 200;
                font-family: 'Inter', 'Cantarell', 'Segoe UI', sans-serif;
                background: transparent;
                letter-spacing: 2px;
            }
        """)

        # Date label
        self._date_label = QLabel("Monday, January 1")
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._date_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.65);
                font-size: 18px;
                font-weight: 400;
                font-family: 'Inter', 'Cantarell', 'Segoe UI', sans-serif;
                background: transparent;
                letter-spacing: 1px;
            }
        """)

        layout.addWidget(self._time_label)
        layout.addWidget(self._date_label)

        # Update timer
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)
        self._update_timer.timeout.connect(self._update_time)
        self._update_time()
        self._update_timer.start()

    def _update_time(self):
        now = QDateTime.currentDateTime()
        self._time_label.setText(now.toString("hh:mm"))
        self._date_label.setText(now.toString("dddd, MMMM d, yyyy"))

    def fade_in(self, duration=600):
        """Animate fade-in."""
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._fade_anim = anim
