"""
Password input widget — fallback authentication when fingerprint fails.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QGraphicsOpacityEffect
)


class PasswordWidget(QWidget):
    """
    Password input with submit button.
    Shows/hides with smooth animation.
    """

    password_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        # Password input row
        input_row = QHBoxLayout()
        input_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._input = QLineEdit()
        self._input.setEchoMode(QLineEdit.EchoMode.Password)
        self._input.setPlaceholderText("Password")
        self._input.setFixedWidth(300)
        self._input.setFixedHeight(48)
        self._input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1.5px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                color: #FFFFFF;
                font-size: 16px;
                font-family: 'Inter', 'Cantarell', sans-serif;
                padding: 0 20px;
                selection-background-color: rgba(59, 130, 246, 0.5);
            }
            QLineEdit:focus {
                border-color: rgba(59, 130, 246, 0.6);
                background: rgba(255, 255, 255, 0.12);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.35);
            }
        """)
        self._input.returnPressed.connect(self._submit)

        self._submit_btn = QPushButton("→")
        self._submit_btn.setFixedSize(48, 48)
        self._submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._submit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.7);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.9);
            }
            QPushButton:pressed {
                background: rgba(59, 130, 246, 1.0);
            }
        """)
        self._submit_btn.clicked.connect(self._submit)

        input_row.addWidget(self._input)
        input_row.addWidget(self._submit_btn)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet("""
            QLabel {
                color: #EF4444;
                font-size: 13px;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
            }
        """)
        self._error_label.hide()

        # "Use fingerprint" link
        self._fp_link = QLabel("Use fingerprint instead")
        self._fp_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fp_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fp_link.setStyleSheet("""
            QLabel {
                color: rgba(59, 130, 246, 0.8);
                font-size: 13px;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
            }
            QLabel:hover {
                color: rgba(59, 130, 246, 1.0);
                text-decoration: underline;
            }
        """)

        layout.addLayout(input_row)
        layout.addWidget(self._error_label)
        layout.addWidget(self._fp_link)

        # Opacity effect for show/hide
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)
        self.hide()

    def show_animated(self):
        """Show with fade-in."""
        self.show()
        self._input.clear()
        self._error_label.hide()
        anim = QPropertyAnimation(self._opacity, b"opacity")
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._show_anim = anim
        self._input.setFocus()

    def hide_animated(self):
        """Hide with fade-out."""
        anim = QPropertyAnimation(self._opacity, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.hide)
        anim.start()
        self._hide_anim = anim

    def show_error(self, message: str):
        """Show an error message below the input."""
        self._error_label.setText(message)
        self._error_label.show()
        self._input.clear()
        self._input.setFocus()

    def _submit(self):
        password = self._input.text()
        if password:
            self.password_submitted.emit(password)

    def set_fingerprint_link_callback(self, callback):
        """Set callback for 'Use fingerprint instead' link."""
        self._fp_link.mousePressEvent = lambda e: callback()

    def focus_input(self):
        """Focus the password input field."""
        self._input.setFocus()
