"""
Full GUI Settings Application for Fingerprint Lock Screen.
Replaces console commands with a tabbed settings window.
"""

import os
import subprocess
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFileDialog, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QScrollArea, QFrame, QGroupBox, QApplication
)

from src.fingerprint_dbus import FingerprintManager, FINGER_NAMES
from src.widgets.finger_selector import FingerSelectorWidget
from src.widgets.enroll_progress import EnrollProgressWidget
from src.widgets.finger_card import FingerCardWidget
from src.config import config

# Shared stylesheet
DARK_STYLE = """
QWidget { background: #12121a; color: #e0e0e0; font-family: 'Inter','Cantarell',sans-serif; }
QTabWidget::pane { border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; background: #16162a; }
QTabBar::tab { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.5);
    padding: 10px 24px; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #16162a; color: #FFFFFF; font-weight: 600; }
QTabBar::tab:hover { background: rgba(255,255,255,0.08); color: #FFFFFF; }
QGroupBox { border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;
    padding: 20px 16px 16px 16px; margin-top: 12px; background: rgba(255,255,255,0.02); }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 8px; color: rgba(255,255,255,0.7); }
QPushButton { background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.25);
    border-radius: 10px; color: #60A5FA; padding: 8px 20px; font-size: 13px; }
QPushButton:hover { background: rgba(59,130,246,0.25); }
QPushButton#primary { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3B82F6,stop:1 #6366F1);
    color: white; border: none; font-weight: 600; }
QPushButton#primary:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563EB,stop:1 #4F46E5); }
QPushButton#danger { background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.2); color: #EF4444; }
QPushButton#danger:hover { background: rgba(239,68,68,0.25); }
QComboBox { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px; padding: 6px 12px; color: white; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #1a1a2e; color: white; selection-background-color: #3B82F6; }
QSpinBox { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px; padding: 6px 12px; color: white; }
QCheckBox { color: rgba(255,255,255,0.8); spacing: 8px; }
QCheckBox::indicator { width: 20px; height: 20px; border-radius: 4px;
    border: 2px solid rgba(255,255,255,0.2); background: transparent; }
QCheckBox::indicator:checked { background: #3B82F6; border-color: #3B82F6; }
QScrollArea { border: none; background: transparent; }
"""


class SettingsApp(QWidget):
    """Full GUI settings application with tabs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Fingerprint Lock — Settings")
        self.setMinimumSize(860, 640)
        self.setStyleSheet(DARK_STYLE)

        self._fp = FingerprintManager()
        self._enrolling = False
        self._current_finger = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        hdr = QLabel("🔐 Fingerprint Lock Screen")
        hdr.setStyleSheet("font-size: 26px; font-weight: 700; background: transparent;")
        layout.addWidget(hdr)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_fingerprints_tab(), "👆 Fingerprints")
        self._tabs.addTab(self._build_background_tab(), "🖼️ Background")
        self._tabs.addTab(self._build_integration_tab(), "⚙️ Integration")
        layout.addWidget(self._tabs)

        self._refresh_enrolled()

    # ── Fingerprints Tab ──────────────────────────────────────

    def _build_fingerprints_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setSpacing(12)

        # Device info
        self._dev_label = QLabel("")
        self._dev_label.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 13px; background: transparent;")
        lay.addWidget(self._dev_label)

        # Action row
        row = QHBoxLayout()
        self._add_btn = QPushButton("+ Add Fingerprint")
        self._add_btn.setObjectName("primary")
        self._add_btn.setFixedHeight(42)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._start_enrollment_gui)
        row.addWidget(self._add_btn)
        
        self._update_device_info()
        row.addStretch()

        self._clear_btn = QPushButton("Delete All")
        self._clear_btn.setObjectName("danger")
        self._clear_btn.setFixedHeight(42)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._delete_all)
        row.addWidget(self._clear_btn)
        lay.addLayout(row)

        # Cards area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._cards_widget)
        lay.addWidget(scroll)

        self._empty = QLabel("No fingerprints enrolled yet.\nClick '+ Add Fingerprint' to get started.")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 15px; padding: 40px; background: transparent;")
        self._cards_layout.addWidget(self._empty)

        # Enrollment overlay (hidden by default)
        self._enroll_overlay = QWidget(page)
        self._enroll_overlay.setStyleSheet("background: rgba(18,18,26,0.95); border-radius: 12px;")
        self._enroll_overlay.hide()
        ov_lay = QVBoxLayout(self._enroll_overlay)
        ov_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ov_lay.setSpacing(16)

        self._enroll_title = QLabel("Select a finger to enroll")
        self._enroll_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._enroll_title.setStyleSheet("font-size: 20px; font-weight: 500; background: transparent;")
        ov_lay.addWidget(self._enroll_title)

        self._finger_selector = FingerSelectorWidget()
        self._finger_selector.finger_selected.connect(self._on_finger_selected)
        ov_lay.addWidget(self._finger_selector, alignment=Qt.AlignmentFlag.AlignCenter)

        self._enroll_progress = EnrollProgressWidget()
        self._enroll_progress.hide()
        ov_lay.addWidget(self._enroll_progress, alignment=Qt.AlignmentFlag.AlignCenter)

        self._enroll_status = QLabel("")
        self._enroll_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._enroll_status.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 14px; background: transparent;")
        ov_lay.addWidget(self._enroll_status)

        cancel = QPushButton("Cancel")
        cancel.setFixedWidth(120)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self._cancel_enrollment)
        ov_lay.addWidget(cancel, alignment=Qt.AlignmentFlag.AlignCenter)

        return page

    # ── Background Tab ────────────────────────────────────────

    def _build_background_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setSpacing(16)

        # Background type
        grp = QGroupBox("Background Type")
        gl = QVBoxLayout(grp)

        self._bg_combo = QComboBox()
        self._bg_combo.addItems(["Blur Desktop (Default)", "Custom Wallpaper", "Video Background"])
        current = config.get("background_type", "blur")
        idx_map = {"blur": 0, "image": 1, "video": 2}
        self._bg_combo.setCurrentIndex(idx_map.get(current, 0))
        self._bg_combo.currentIndexChanged.connect(self._on_bg_type_changed)
        gl.addWidget(self._bg_combo)
        lay.addWidget(grp)

        # File picker
        grp2 = QGroupBox("Background File")
        gl2 = QVBoxLayout(grp2)

        file_row = QHBoxLayout()
        self._bg_path_label = QLabel(config.get("background_path", "") or "No file selected")
        self._bg_path_label.setStyleSheet("color: rgba(255,255,255,0.5); background: transparent;")
        file_row.addWidget(self._bg_path_label, 1)

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_btn.clicked.connect(self._browse_background)
        file_row.addWidget(self._browse_btn)
        gl2.addLayout(file_row)

        # Preview
        self._preview = QLabel()
        self._preview.setFixedHeight(200)
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setStyleSheet("background: rgba(0,0,0,0.3); border-radius: 10px;")
        gl2.addWidget(self._preview)
        self._update_preview()

        lay.addWidget(grp2)
        self._bg_file_group = grp2

        # Blur settings
        grp3 = QGroupBox("Blur Settings")
        gl3 = QHBoxLayout(grp3)
        gl3.addWidget(QLabel("Blur Radius:"))
        self._blur_spin = QSpinBox()
        self._blur_spin.setRange(0, 100)
        self._blur_spin.setValue(config.get("blur_radius", 40))
        self._blur_spin.valueChanged.connect(lambda v: config.set("blur_radius", v))
        gl3.addWidget(self._blur_spin)
        gl3.addStretch()
        lay.addWidget(grp3)

        lay.addStretch()

        # Apply
        apply_btn = QPushButton("Apply Background Settings")
        apply_btn.setObjectName("primary")
        apply_btn.setFixedHeight(44)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_background)
        lay.addWidget(apply_btn)

        self._on_bg_type_changed(self._bg_combo.currentIndex())
        return page

    # ── Integration Tab ───────────────────────────────────────

    def _build_integration_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setSpacing(16)

        # Set as default
        grp = QGroupBox("Lock Screen Integration")
        gl = QVBoxLayout(grp)

        desc = QLabel(
            "Replace the default GNOME lock screen with this fingerprint lock screen.\n"
            "This creates a D-Bus service that listens for screen lock events."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: rgba(255,255,255,0.5); background: transparent;")
        gl.addWidget(desc)

        self._default_btn = QPushButton("Set as Default Lock Screen")
        self._default_btn.setObjectName("primary")
        self._default_btn.setFixedHeight(44)
        self._default_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._default_btn.clicked.connect(self._set_as_default)
        gl.addWidget(self._default_btn)

        self._restore_btn = QPushButton("Restore GNOME Default")
        self._restore_btn.setObjectName("danger")
        self._restore_btn.setFixedHeight(44)
        self._restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._restore_btn.clicked.connect(self._restore_default)
        gl.addWidget(self._restore_btn)

        self._integration_status = QLabel("")
        self._integration_status.setStyleSheet("color: rgba(255,255,255,0.4); background: transparent;")
        gl.addWidget(self._integration_status)
        lay.addWidget(grp)

        # Behavior
        grp2 = QGroupBox("Behavior")
        gl2 = QVBoxLayout(grp2)

        self._lock_suspend = QCheckBox("Lock on suspend / sleep")
        self._lock_suspend.setChecked(config.get("lock_on_suspend", True))
        self._lock_suspend.toggled.connect(lambda v: config.set("lock_on_suspend", v))
        gl2.addWidget(self._lock_suspend)

        self._lock_lid = QCheckBox("Lock on lid close")
        self._lock_lid.setChecked(config.get("lock_on_lid_close", True))
        self._lock_lid.toggled.connect(lambda v: config.set("lock_on_lid_close", v))
        gl2.addWidget(self._lock_lid)

        self._show_clock = QCheckBox("Show clock on lock screen")
        self._show_clock.setChecked(config.get("show_clock", True))
        self._show_clock.toggled.connect(lambda v: config.set("show_clock", v))
        gl2.addWidget(self._show_clock)

        timeout_row = QHBoxLayout()
        timeout_row.addWidget(QLabel("Max verify attempts:"))
        self._max_attempts = QSpinBox()
        self._max_attempts.setRange(1, 20)
        self._max_attempts.setValue(config.get("max_verify_attempts", 5))
        self._max_attempts.valueChanged.connect(lambda v: config.set("max_verify_attempts", v))
        timeout_row.addWidget(self._max_attempts)
        timeout_row.addStretch()
        gl2.addLayout(timeout_row)

        lay.addWidget(grp2)

        # Test buttons
        grp3 = QGroupBox("Quick Actions")
        gl3 = QHBoxLayout(grp3)

        demo_btn = QPushButton("🖥️ Preview Lock Screen")
        demo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        demo_btn.clicked.connect(self._preview_lock)
        gl3.addWidget(demo_btn)

        status_btn = QPushButton("📊 Sensor Status")
        status_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        status_btn.clicked.connect(self._show_status)
        gl3.addWidget(status_btn)

        lay.addWidget(grp3)
        lay.addStretch()

        self._update_integration_status()
        return page

    # ── Fingerprint Logic ─────────────────────────────────────

    def _update_device_info(self):
        if self._fp.has_device():
            info = self._fp.get_device_info()
            self._dev_label.setText(f"Sensor: {info.get('name','Unknown')} ({info.get('scan-type','unknown')})")
        else:
            self._dev_label.setText("⚠️ No fingerprint sensor detected — run scripts/setup-driver.sh first")
            self._add_btn.setEnabled(False)

    def _refresh_enrolled(self):
        while self._cards_layout.count():
            child = self._cards_layout.takeAt(0)
            if child.widget():
                if child.widget() == self._empty:
                    child.widget().setParent(None)
                else:
                    child.widget().deleteLater()

        enrolled = self._fp.list_enrolled_fingers()
        self._finger_selector.set_enrolled_fingers(enrolled)

        if enrolled:
            self._empty.hide()
            self._clear_btn.show()
            for f in enrolled:
                card = FingerCardWidget(f, config.get_finger_name(f))
                card.delete_requested.connect(self._delete_finger)
                card.test_requested.connect(self._test_finger)
                self._cards_layout.addWidget(card)
        else:
            self._cards_layout.addWidget(self._empty)
            self._empty.show()
            self._clear_btn.hide()

    def _start_enrollment_gui(self):
        self._enroll_overlay.setGeometry(self._tabs.widget(0).rect())
        self._enroll_overlay.show()
        self._enroll_overlay.raise_()
        self._enroll_title.setText("Select a finger to enroll")
        self._finger_selector.show()
        self._enroll_progress.hide()
        self._enroll_status.setText("Click on a finger tip to begin")

    def _on_finger_selected(self, finger_name):
        self._current_finger = finger_name
        self._enrolling = True
        display = config.get_finger_name(finger_name)
        self._enroll_title.setText(f"Enrolling: {display}")
        self._finger_selector.hide()
        self._enroll_progress.show()

        info = self._fp.get_device_info()
        stages = info.get("num-enroll-stages", 5)
        self._enroll_progress.set_total_stages(stages)
        self._enroll_progress.reset()
        self._enroll_progress.set_message("Place your finger on the sensor")

        if not self._fp.claim_device():
            self._enroll_status.setText("❌ Could not access sensor")
            return

        def on_status(status, completed):
            if completed:
                self._on_enroll_complete()
            elif status == "enroll-stage-passed":
                self._enroll_progress.advance()
                self._enroll_progress.set_message("Good! Lift and place again...")
                self._enroll_status.setText(self._fp.get_enroll_message(status))
            else:
                self._enroll_status.setText(self._fp.get_enroll_message(status))

        self._fp.start_enrollment(finger_name, on_status=on_status)

    def _on_enroll_complete(self):
        self._enrolling = False
        self._enroll_title.setText("✅ Fingerprint Enrolled!")
        self._enroll_status.setText("Saved successfully.")
        try:
            self._fp.release_device()
        except Exception:
            pass
        QTimer.singleShot(1500, self._finish_enrollment)

    def _cancel_enrollment(self):
        if self._enrolling:
            try:
                self._fp.stop_enrollment()
                self._fp.release_device()
            except Exception:
                pass
        self._enrolling = False
        self._finish_enrollment()

    def _finish_enrollment(self):
        self._enroll_overlay.hide()
        self._refresh_enrolled()

    def _delete_finger(self, name):
        if QMessageBox.question(self, "Delete", f"Delete '{config.get_finger_name(name)}'?") == QMessageBox.StandardButton.Yes:
            self._fp.claim_device()
            self._fp.delete_enrolled_finger(name)
            self._fp.release_device()
            self._refresh_enrolled()

    def _delete_all(self):
        if QMessageBox.question(self, "Delete All", "Delete ALL fingerprints?") == QMessageBox.StandardButton.Yes:
            self._fp.claim_device()
            self._fp.delete_enrolled_fingers()
            self._fp.release_device()
            self._refresh_enrolled()

    def _test_finger(self, name):
        display = config.get_finger_name(name)
        if not self._fp.claim_device():
            QMessageBox.warning(self, "Error", "Could not access sensor")
            return

        def on_verify(status, is_match):
            try:
                self._fp.release_device()
            except Exception:
                pass
            if is_match:
                QMessageBox.information(self, "Test", f"✅ {display} matched!")
            else:
                QMessageBox.warning(self, "Test", f"❌ No match: {status}")

        self._fp.start_verify(name, on_status=on_verify)

    # ── Background Logic ──────────────────────────────────────

    def _on_bg_type_changed(self, idx):
        type_map = {0: "blur", 1: "image", 2: "video"}
        config.set("background_type", type_map.get(idx, "blur"))
        self._bg_file_group.setVisible(idx != 0)

    def _browse_background(self):
        bg_type = config.get("background_type", "blur")
        if bg_type == "video":
            filt = "Videos (*.mp4 *.webm *.mkv *.avi)"
        else:
            filt = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"

        path, _ = QFileDialog.getOpenFileName(self, "Select Background", os.path.expanduser("~"), filt)
        if path:
            config.set("background_path", path)
            self._bg_path_label.setText(path)
            self._update_preview()

    def _update_preview(self):
        path = config.get("background_path", "")
        if path and os.path.exists(path) and config.get("background_type") != "video":
            px = QPixmap(path)
            if not px.isNull():
                self._preview.setPixmap(px.scaled(
                    self._preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
                return
        self._preview.setText("No preview available" if config.get("background_type") == "video"
                             else "Select an image to preview")

    def _apply_background(self):
        config.save()
        QMessageBox.information(self, "Applied", "Background settings saved.\nChanges will appear next time the lock screen activates.")

    # ── Integration Logic ─────────────────────────────────────

    def _set_as_default(self):
        project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        service_content = f"""[Unit]
Description=Fingerprint Lock Screen Service
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m src.main dbus-service
WorkingDirectory={project}
Restart=on-failure

[Install]
WantedBy=graphical-session.target
"""
        svc_dir = os.path.expanduser("~/.config/systemd/user")
        os.makedirs(svc_dir, exist_ok=True)
        svc_path = os.path.join(svc_dir, "fingerprint-lock.service")
        with open(svc_path, "w") as f:
            f.write(service_content)

        config.set("is_default_lock", True)
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "fingerprint-lock.service"], check=True)
            subprocess.run(["systemctl", "--user", "start", "fingerprint-lock.service"], check=False)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Service setup partially failed: {e}\nYou may need to log out and back in.")

        self._update_integration_status()
        QMessageBox.information(self, "Done", "Fingerprint lock set as default!\nIt will activate on screen lock events.")

    def _restore_default(self):
        try:
            subprocess.run(["systemctl", "--user", "stop", "fingerprint-lock.service"], check=False)
            subprocess.run(["systemctl", "--user", "disable", "fingerprint-lock.service"], check=False)
        except Exception:
            pass
        config.set("is_default_lock", False)
        self._update_integration_status()
        QMessageBox.information(self, "Restored", "GNOME default lock screen restored.")

    def _update_integration_status(self):
        is_default = config.get("is_default_lock", False)
        if is_default:
            self._integration_status.setText("✅ Fingerprint Lock is the active lock screen")
            self._integration_status.setStyleSheet("color: #10B981; background: transparent;")
            self._default_btn.setEnabled(False)
            self._restore_btn.setEnabled(True)
        else:
            self._integration_status.setText("Using GNOME default lock screen")
            self._default_btn.setEnabled(True)
            self._restore_btn.setEnabled(False)

    def _preview_lock(self):
        project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.Popen(["python3", "-m", "src.main", "lock", "--demo"], cwd=project)

    def _show_status(self):
        lines = []
        if self._fp.has_device():
            info = self._fp.get_device_info()
            lines.append(f"✅ Sensor: {info.get('name','Unknown')}")
            lines.append(f"   Type: {info.get('scan-type','Unknown')}")
            lines.append(f"   Stages: {info.get('num-enroll-stages','?')}")
        else:
            lines.append("❌ No fingerprint sensor detected")

        enrolled = self._fp.list_enrolled_fingers()
        lines.append(f"\nEnrolled: {len(enrolled)} fingerprint(s)")
        for f in enrolled:
            lines.append(f"  ✅ {config.get_finger_name(f)}")

        QMessageBox.information(self, "Sensor Status", "\n".join(lines))

    def closeEvent(self, event):
        if self._enrolling:
            self._cancel_enrollment()
        self._fp.cleanup()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_enroll_overlay') and self._enroll_overlay.isVisible():
            self._enroll_overlay.setGeometry(self._tabs.widget(0).rect())
