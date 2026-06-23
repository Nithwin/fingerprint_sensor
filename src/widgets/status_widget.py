"""
Status widget — shows messages like "Touch sensor to unlock" or "Try again".
"""

from PyQt6.QtCore import (
    Qt, pyqtProperty, QPropertyAnimation, QEasingCurve,
    QSequentialAnimationGroup, QTimer
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class StatusWidget(QWidget):
    """Displays status messages with smooth fade transitions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("Touch sensor to unlock")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 16px;
                font-weight: 400;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
                padding: 8px 20px;
            }
        """)
        layout.addWidget(self._label)
        self._current_text = "Touch sensor to unlock"

    def set_message(self, text: str, color: str = "rgba(255,255,255,0.7)",
                    duration: int = 0):
        """
        Set a status message with fade transition.
        
        Args:
            text: Message to display
            color: CSS color string
            duration: Auto-clear after ms (0 = permanent)
        """
        self._label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 16px;
                font-weight: 400;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
                padding: 8px 20px;
            }}
        """)
        self._label.setText(text)
        self._current_text = text

        if duration > 0:
            QTimer.singleShot(duration, lambda: self.set_message(
                "Touch sensor to unlock"))

    def set_idle(self):
        self.set_message("Touch sensor to unlock")

    def set_scanning(self):
        self.set_message("Reading fingerprint...", "#F59E0B")

    def set_success(self):
        self.set_message("Welcome back!", "#10B981")

    def set_failure(self, attempts_left: int = 0):
        msg = "Fingerprint not recognized"
        if attempts_left > 0:
            msg += f" — {attempts_left} attempts remaining"
        self.set_message(msg, "#EF4444", duration=3000)

    def set_error(self, msg: str):
        self.set_message(msg, "#EF4444", duration=5000)

    def set_password_mode(self):
        self.set_message("Enter password to unlock", "rgba(255,255,255,0.7)")
