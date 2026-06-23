"""
Finger card widget — displays an enrolled fingerprint with name and delete button.
"""

from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)


class FingerCardWidget(QWidget):
    """Card showing an enrolled finger with delete and test actions."""

    delete_requested = pyqtSignal(str)  # finger_name
    test_requested = pyqtSignal(str)    # finger_name

    def __init__(self, finger_name: str, display_name: str, parent=None):
        super().__init__(parent)
        self._finger_name = finger_name
        self._display_name = display_name
        self.setFixedHeight(70)
        self.setMinimumWidth(400)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
            QWidget:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.12);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 16, 12)

        # Fingerprint icon
        icon = QLabel("🔒")
        icon.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background: transparent;
                border: none;
            }
        """)

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)

        name_label = QLabel(display_name)
        name_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 15px;
                font-weight: 500;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
                border: none;
            }
        """)

        detail_label = QLabel(finger_name.replace("-", " ").title())
        detail_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.45);
                font-size: 12px;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
                border: none;
            }
        """)

        info.addWidget(name_label)
        info.addWidget(detail_label)

        # Action buttons
        test_btn = QPushButton("Test")
        test_btn.setFixedSize(60, 32)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.2);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 8px;
                color: #60A5FA;
                font-size: 12px;
                font-family: 'Inter', sans-serif;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.35);
            }
        """)
        test_btn.clicked.connect(lambda: self.test_requested.emit(self._finger_name))

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(32, 32)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 8px;
                color: #EF4444;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._finger_name))

        layout.addWidget(icon)
        layout.addLayout(info)
        layout.addStretch()
        layout.addWidget(test_btn)
        layout.addWidget(del_btn)
