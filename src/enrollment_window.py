"""
Enrollment Management Window — add, test, and remove fingerprints.
Settings-style GUI for managing enrolled fingerprints.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QStackedWidget,
    QApplication, QGraphicsOpacityEffect
)

from src.fingerprint_dbus import FingerprintManager, FINGER_NAMES
from src.widgets.finger_selector import FingerSelectorWidget
from src.widgets.enroll_progress import EnrollProgressWidget
from src.widgets.finger_card import FingerCardWidget
from src.config import config


class EnrollmentWindow(QWidget):
    """
    Management window for fingerprint enrollment.
    
    Features:
    - View all enrolled fingerprints
    - Add new fingerprint with visual hand selector
    - Step-by-step enrollment progress
    - Test enrolled fingerprints
    - Delete individual or all fingerprints
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fingerprint Settings")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #0F0F1A,
                    stop: 0.5 #1A1A2E,
                    stop: 1 #16213E
                );
                font-family: 'Inter', 'Cantarell', sans-serif;
            }
        """)

        self._fp = FingerprintManager()
        self._enrolling = False
        self._current_finger = None

        self._setup_ui()
        self._refresh_enrolled()

    def _setup_ui(self):
        """Build the enrollment UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # Header
        header = QHBoxLayout()

        title = QLabel("🔐 Fingerprint Settings")
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: 600;
                background: transparent;
            }
        """)

        self._device_label = QLabel("")
        self._device_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.4);
                font-size: 13px;
                background: transparent;
            }
        """)

        header_info = QVBoxLayout()
        header_info.addWidget(title)
        header_info.addWidget(self._device_label)
        header.addLayout(header_info)
        header.addStretch()

        # Add button
        self._add_btn = QPushButton("+ Add Fingerprint")
        self._add_btn.setFixedHeight(44)
        self._add_btn.setFixedWidth(180)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #6366F1
                );
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563EB, stop:1 #4F46E5
                );
            }
            QPushButton:disabled {
                background: rgba(100, 100, 100, 0.3);
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        self._add_btn.clicked.connect(self._start_enrollment)
        header.addWidget(self._add_btn)

        main_layout.addLayout(header)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background: rgba(255,255,255,0.06); max-height: 1px;")
        main_layout.addWidget(divider)

        # Stacked widget: enrolled list vs enrollment flow
        self._stack = QStackedWidget()

        # Page 0: Enrolled fingerprints list
        self._list_page = QWidget()
        self._list_page.setStyleSheet("background: transparent;")
        list_layout = QVBoxLayout(self._list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(10)

        self._cards_container = QVBoxLayout()
        self._cards_container.setSpacing(8)
        list_layout.addLayout(self._cards_container)

        self._empty_label = QLabel("No fingerprints enrolled yet.\nClick '+ Add Fingerprint' to get started.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.3);
                font-size: 16px;
                padding: 60px;
                background: transparent;
            }
        """)
        list_layout.addWidget(self._empty_label)
        list_layout.addStretch()

        # Clear all button
        self._clear_btn = QPushButton("Delete All Fingerprints")
        self._clear_btn.setFixedHeight(40)
        self._clear_btn.setFixedWidth(200)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 10px;
                color: #EF4444;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
            }
        """)
        self._clear_btn.clicked.connect(self._delete_all)
        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_row.addWidget(self._clear_btn)
        list_layout.addLayout(clear_row)

        # Page 1: Enrollment flow
        self._enroll_page = QWidget()
        self._enroll_page.setStyleSheet("background: transparent;")
        enroll_layout = QVBoxLayout(self._enroll_page)
        enroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enroll_layout.setSpacing(20)

        self._enroll_title = QLabel("Select a finger to enroll")
        self._enroll_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._enroll_title.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                font-size: 20px;
                font-weight: 500;
                background: transparent;
            }
        """)
        enroll_layout.addWidget(self._enroll_title)

        # Stacked: finger selector vs progress
        self._enroll_stack = QStackedWidget()

        self._finger_selector = FingerSelectorWidget()
        self._finger_selector.finger_selected.connect(self._on_finger_selected)

        self._enroll_progress = EnrollProgressWidget()

        self._enroll_stack.addWidget(self._finger_selector)
        self._enroll_stack.addWidget(self._enroll_progress)
        enroll_layout.addWidget(self._enroll_stack, alignment=Qt.AlignmentFlag.AlignCenter)

        self._enroll_status = QLabel("")
        self._enroll_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._enroll_status.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
                background: transparent;
            }
        """)
        enroll_layout.addWidget(self._enroll_status)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(120, 40)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        cancel_btn.clicked.connect(self._cancel_enrollment)
        enroll_layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._stack.addWidget(self._list_page)
        self._stack.addWidget(self._enroll_page)
        main_layout.addWidget(self._stack)

        # Update device info
        self._update_device_info()

    def _update_device_info(self):
        """Show connected sensor info."""
        if self._fp.has_device():
            info = self._fp.get_device_info()
            name = info.get("name", "Unknown")
            scan_type = info.get("scan-type", "unknown")
            self._device_label.setText(f"Sensor: {name} ({scan_type})")
        else:
            self._device_label.setText("⚠️ No fingerprint sensor detected")
            self._add_btn.setEnabled(False)

    def _refresh_enrolled(self):
        """Refresh the list of enrolled fingerprints."""
        # Clear existing cards
        while self._cards_container.count():
            child = self._cards_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        enrolled = self._fp.list_enrolled_fingers()
        self._finger_selector.set_enrolled_fingers(enrolled)

        if enrolled:
            self._empty_label.hide()
            self._clear_btn.show()
            for finger in enrolled:
                display_name = config.get_finger_name(finger)
                card = FingerCardWidget(finger, display_name)
                card.delete_requested.connect(self._delete_finger)
                card.test_requested.connect(self._test_finger)
                self._cards_container.addWidget(card)
        else:
            self._empty_label.show()
            self._clear_btn.hide()

    def _start_enrollment(self):
        """Show the enrollment flow."""
        self._stack.setCurrentIndex(1)
        self._enroll_stack.setCurrentIndex(0)
        self._enroll_title.setText("Select a finger to enroll")
        self._enroll_status.setText("Click on a finger tip to begin")
        self._add_btn.setEnabled(False)

    def _on_finger_selected(self, finger_name: str):
        """User selected a finger — begin enrollment."""
        self._current_finger = finger_name
        self._enrolling = True
        display = config.get_finger_name(finger_name)

        self._enroll_title.setText(f"Enrolling: {display}")
        self._enroll_stack.setCurrentIndex(1)

        # Get device info for stage count
        info = self._fp.get_device_info()
        stages = info.get("num-enroll-stages", 5)
        self._enroll_progress.set_total_stages(stages)
        self._enroll_progress.reset()
        self._enroll_progress.set_message("Place your finger on the sensor")

        # Start enrollment via fprintd
        if not self._fp.claim_device():
            self._enroll_status.setText("❌ Could not access sensor")
            return

        def on_enroll_status(status, completed):
            if completed:
                self._on_enroll_complete()
            elif status == "enroll-stage-passed":
                self._enroll_progress.advance()
                self._enroll_progress.set_message("Good! Lift and place again...")
                self._enroll_status.setText(self._fp.get_enroll_message(status))
            else:
                msg = self._fp.get_enroll_message(status)
                self._enroll_status.setText(msg)
                self._enroll_progress.set_message(msg)

        success = self._fp.start_enrollment(finger_name, on_status=on_enroll_status)
        if not success:
            self._enroll_status.setText("❌ Failed to start enrollment")

    def _on_enroll_complete(self):
        """Enrollment completed successfully."""
        self._enrolling = False
        self._enroll_title.setText("✅ Fingerprint Enrolled!")
        self._enroll_status.setText("Your fingerprint has been saved successfully.")
        self._enroll_progress.set_message("Complete!")

        try:
            self._fp.release_device()
        except Exception:
            pass

        # Return to list after delay
        QTimer.singleShot(2000, self._finish_enrollment)

    def _cancel_enrollment(self):
        """Cancel ongoing enrollment."""
        if self._enrolling:
            try:
                self._fp.stop_enrollment()
                self._fp.release_device()
            except Exception:
                pass
        self._enrolling = False
        self._finish_enrollment()

    def _finish_enrollment(self):
        """Return to the fingerprint list."""
        self._stack.setCurrentIndex(0)
        self._add_btn.setEnabled(True)
        self._refresh_enrolled()

    def _delete_finger(self, finger_name: str):
        """Delete a specific enrolled finger."""
        display = config.get_finger_name(finger_name)
        reply = QMessageBox.question(
            self, "Delete Fingerprint",
            f"Are you sure you want to delete '{display}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if not self._fp.claim_device():
                QMessageBox.warning(self, "Error", "Could not access sensor")
                return
            self._fp.delete_enrolled_finger(finger_name)
            self._fp.release_device()
            self._refresh_enrolled()

    def _delete_all(self):
        """Delete all enrolled fingerprints."""
        reply = QMessageBox.question(
            self, "Delete All Fingerprints",
            "Are you sure you want to delete ALL enrolled fingerprints?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if not self._fp.claim_device():
                QMessageBox.warning(self, "Error", "Could not access sensor")
                return
            self._fp.delete_enrolled_fingers()
            self._fp.release_device()
            self._refresh_enrolled()

    def _test_finger(self, finger_name: str):
        """Test an enrolled fingerprint."""
        display = config.get_finger_name(finger_name)
        self._enroll_status.setText(f"Testing {display}... Place your finger")

        if not self._fp.claim_device():
            self._enroll_status.setText("Could not access sensor")
            return

        def on_verify(status, is_match):
            try:
                self._fp.release_device()
            except Exception:
                pass
            if is_match:
                QMessageBox.information(self, "Test Result", f"✅ {display} matched!")
            else:
                QMessageBox.warning(self, "Test Result", f"❌ No match: {status}")

        self._fp.start_verify(finger_name, on_status=on_verify)

    def closeEvent(self, event):
        if self._enrolling:
            self._cancel_enrollment()
        self._fp.cleanup()
        super().closeEvent(event)
