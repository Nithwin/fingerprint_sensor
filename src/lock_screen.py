"""
Main Lock Screen — full-screen overlay with fingerprint authentication.
This is the primary UI that users see when the screen is locked.
"""

import subprocess
import os
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtProperty, QThread, pyqtSignal, QObject
)
from PyQt6.QtGui import (
    QColor, QPainter, QPixmap, QImage, QScreen,
    QGuiApplication, QFont, QRadialGradient
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QApplication, QGraphicsOpacityEffect, QSpacerItem,
    QSizePolicy
)

from src.widgets.fingerprint_widget import FingerprintWidget
from src.widgets.clock_widget import ClockWidget
from src.widgets.status_widget import StatusWidget
from src.widgets.password_widget import PasswordWidget
from src.widgets.user_avatar import UserAvatarWidget
from src.fingerprint_dbus import FingerprintManager
from src.auth import PAMAuthenticator
from src.config import config


class VerifyWorker(QObject):
    """Worker to handle fingerprint verification in a separate thread context."""
    verify_result = pyqtSignal(str, bool)  # status, is_match

    def __init__(self, fp_manager):
        super().__init__()
        self._fp = fp_manager

    def start_verify(self):
        """Start fingerprint verification."""
        def on_status(status, is_match):
            self.verify_result.emit(status, is_match)

        self._fp.start_verify("any", on_status=on_status)


class LockScreen(QWidget):
    """
    Full-screen lock screen with fingerprint authentication.
    
    Features:
    - Blurred desktop background
    - Animated fingerprint scanning
    - Password fallback
    - Multi-monitor support
    - Keyboard grab (prevents Alt+Tab, etc.)
    """

    unlocked = pyqtSignal()

    def __init__(self, parent=None, demo_mode=False):
        super().__init__(parent)
        self._demo_mode = demo_mode
        self._verify_attempts = 0
        self._max_attempts = config.get("max_verify_attempts", 5)
        self._password_mode = False
        self._is_verifying = False
        self._bg_opacity = 0.0

        # Initialize services
        self._fp = FingerprintManager()
        self._pam = PAMAuthenticator()

        # Window setup
        if not demo_mode:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setWindowTitle("Fingerprint Lock — Demo Mode")
            self.setMinimumSize(900, 650)

        self._setup_background()
        self._setup_ui()

    def _setup_background(self):
        """Capture and blur the current desktop for background."""
        self._bg_pixmap = None
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                self._bg_pixmap = screen.grabWindow(0)
        except Exception:
            pass

    def _setup_ui(self):
        """Build the lock screen UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Central content area
        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(16)

        # Top spacer
        content_layout.addSpacerItem(
            QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Clock
        self._clock = ClockWidget()
        content_layout.addWidget(self._clock, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addSpacerItem(
            QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        # User avatar
        self._avatar = UserAvatarWidget(size=80)
        display_name = self._pam.get_user_display_name()
        self._avatar.set_initials(display_name)

        avatar_path = self._pam.get_user_avatar_path()
        if avatar_path:
            self._avatar.set_avatar(avatar_path)

        content_layout.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addSpacerItem(
            QSpacerItem(20, 24, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        # Fingerprint widget
        self._fingerprint = FingerprintWidget(size=180)
        content_layout.addWidget(self._fingerprint, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status message
        self._status = StatusWidget()
        content_layout.addWidget(self._status, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addSpacerItem(
            QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        # Password widget (initially hidden)
        self._password = PasswordWidget()
        self._password.password_submitted.connect(self._on_password_submit)
        self._password.set_fingerprint_link_callback(self._switch_to_fingerprint)
        content_layout.addWidget(self._password, alignment=Qt.AlignmentFlag.AlignCenter)

        # "Other sign-in options" label
        self._signin_options = QLabel("Other sign-in options")
        self._signin_options.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._signin_options.setCursor(Qt.CursorShape.PointingHandCursor)
        self._signin_options.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 13px;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
                padding: 8px;
            }
            QLabel:hover {
                color: rgba(255, 255, 255, 0.8);
            }
        """)
        self._signin_options.mousePressEvent = lambda e: self._switch_to_password()
        content_layout.addWidget(self._signin_options, alignment=Qt.AlignmentFlag.AlignCenter)

        # Bottom spacer
        content_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Bottom status bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(30, 0, 30, 20)

        # Battery / Network info (placeholder)
        self._system_info = QLabel("")
        self._system_info.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.4);
                font-size: 12px;
                font-family: 'Inter', 'Cantarell', sans-serif;
                background: transparent;
            }
        """)
        self._update_system_info()
        bottom_bar.addWidget(self._system_info)
        bottom_bar.addStretch()

        content_layout.addLayout(bottom_bar)

        main_layout.addWidget(content)

        # System info update timer
        self._sys_timer = QTimer(self)
        self._sys_timer.setInterval(30000)
        self._sys_timer.timeout.connect(self._update_system_info)
        self._sys_timer.start()

    def _update_system_info(self):
        """Update battery and network status."""
        info_parts = []
        # Battery
        try:
            bat_path = "/sys/class/power_supply/BAT0/capacity"
            if os.path.exists(bat_path):
                with open(bat_path) as f:
                    capacity = f.read().strip()
                info_parts.append(f"🔋 {capacity}%")
            # Charging status
            status_path = "/sys/class/power_supply/BAT0/status"
            if os.path.exists(status_path):
                with open(status_path) as f:
                    status = f.read().strip()
                if status == "Charging":
                    info_parts[-1] += " ⚡"
        except Exception:
            pass

        # Hostname
        info_parts.append(f"🖥️ {self._pam.get_hostname()}")

        self._system_info.setText("    ".join(info_parts))

    def paintEvent(self, event):
        """Paint the background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw blurred/darkened background
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            # Scale to fill
            scaled = self._bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # Dark overlay with gradient
        gradient = QRadialGradient(
            self.width() / 2, self.height() / 2,
            max(self.width(), self.height()) / 1.5
        )
        gradient.setColorAt(0, QColor(10, 10, 30, 180))
        gradient.setColorAt(0.7, QColor(5, 5, 20, 210))
        gradient.setColorAt(1, QColor(0, 0, 10, 240))
        painter.fillRect(self.rect(), gradient)

        # Subtle noise/grain effect via dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))

        painter.end()

    def showEvent(self, event):
        """Called when lock screen is shown."""
        super().showEvent(event)
        if not self._demo_mode:
            self.showFullScreen()
            self.grabKeyboard()
            self.grabMouse()

        # Start fingerprint scanning
        self._start_fingerprint_verify()

    def closeEvent(self, event):
        """Cleanup on close."""
        self._fp.cleanup()
        if not self._demo_mode:
            self.releaseKeyboard()
            self.releaseMouse()
        super().closeEvent(event)

    def _start_fingerprint_verify(self):
        """Begin fingerprint verification."""
        if self._password_mode or self._is_verifying:
            return

        if not self._fp.has_device():
            self._status.set_message("No fingerprint sensor found", "#F59E0B")
            self._switch_to_password()
            return

        enrolled = self._fp.list_enrolled_fingers()
        if not enrolled:
            self._status.set_message("No fingerprints enrolled", "#F59E0B")
            QTimer.singleShot(2000, self._switch_to_password)
            return

        self._is_verifying = True
        self._fingerprint.set_idle()
        self._status.set_idle()

        def on_verify(status, is_match):
            self._is_verifying = False
            if is_match:
                self._on_verify_success()
            else:
                self._on_verify_failure(status)

        if not self._fp.claim_device():
            self._status.set_error("Could not access fingerprint sensor")
            self._switch_to_password()
            return

        # Brief delay then start verify
        QTimer.singleShot(500, lambda: self._fp.start_verify("any", on_status=on_verify))

    def _on_verify_success(self):
        """Handle successful fingerprint verification."""
        self._fingerprint.set_success(on_complete=self._do_unlock)
        self._status.set_success()

    def _on_verify_failure(self, status: str):
        """Handle failed fingerprint verification."""
        self._verify_attempts += 1
        remaining = self._max_attempts - self._verify_attempts
        msg = self._fp.get_verify_message(status)

        self._fingerprint.set_failure(on_complete=lambda: self._after_failure(remaining))
        self._status.set_failure(remaining)

    def _after_failure(self, remaining: int):
        """After failure animation completes."""
        try:
            self._fp.release_device()
        except Exception:
            pass

        if remaining <= 0:
            self._switch_to_password()
        else:
            # Retry fingerprint after a short delay
            QTimer.singleShot(1000, self._start_fingerprint_verify)

    def _switch_to_password(self):
        """Switch to password input mode."""
        self._password_mode = True
        self._is_verifying = False
        try:
            self._fp.stop_verify()
            self._fp.release_device()
        except Exception:
            pass
        self._fingerprint.set_idle()
        self._status.set_password_mode()
        self._password.show_animated()
        self._signin_options.hide()

    def _switch_to_fingerprint(self):
        """Switch back to fingerprint mode."""
        self._password_mode = False
        self._verify_attempts = 0
        self._password.hide_animated()
        self._signin_options.show()
        QTimer.singleShot(300, self._start_fingerprint_verify)

    def _on_password_submit(self, password: str):
        """Handle password submission."""
        success, message = self._pam.verify_password(password)
        if success:
            self._status.set_success()
            self._do_unlock()
        else:
            self._password.show_error("Incorrect password. Try again.")

    def _do_unlock(self):
        """Perform the unlock — close lock screen."""
        # Fade out animation
        QTimer.singleShot(800, self._complete_unlock)

    def _complete_unlock(self):
        """Complete the unlock process."""
        try:
            self._fp.cleanup()
        except Exception:
            pass
        if not self._demo_mode:
            self.releaseKeyboard()
            self.releaseMouse()
        self.unlocked.emit()
        self.close()

    def keyPressEvent(self, event):
        """Handle key presses on lock screen."""
        key = event.key()

        # Escape shows password input
        if key == Qt.Key.Key_Escape:
            if self._password_mode:
                self._switch_to_fingerprint()
            else:
                self._switch_to_password()
            return

        # Any printable key switches to password mode
        if not self._password_mode and event.text().isprintable() and event.text():
            self._switch_to_password()
            # Forward the key press to password input
            self._password._input.setText(event.text())
            self._password._input.setFocus()
            return

        super().keyPressEvent(event)
