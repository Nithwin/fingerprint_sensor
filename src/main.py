#!/usr/bin/env python3
"""
Fingerprint Lock Screen — Main Entry Point

Usage:
    python3 -m src.main lock          # Show lock screen
    python3 -m src.main lock --demo   # Demo mode (windowed, no grab)
    python3 -m src.main enroll        # Open enrollment settings
    python3 -m src.main status        # Show sensor and enrollment status
    python3 -m src.main test          # Quick fingerprint test
"""

import sys
import os
import signal

# Set up D-Bus main loop before importing Qt
import dbus
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QFontDatabase


def setup_app():
    """Initialize Qt application with styling."""
    app = QApplication(sys.argv)
    app.setApplicationName("Fingerprint Lock")
    app.setApplicationVersion("1.0.0")

    # Load Inter font if available
    font_paths = [
        "/usr/share/fonts/google-inter-fonts/",
        "/usr/share/fonts/inter/",
    ]
    for path in font_paths:
        if os.path.exists(path):
            for f in os.listdir(path):
                if f.endswith((".ttf", ".otf")):
                    QFontDatabase.addApplicationFont(os.path.join(path, f))

    # Default font
    font = QFont("Inter", 12)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    return app


def cmd_lock(demo=False):
    """Show the lock screen."""
    app = setup_app()

    from src.lock_screen import LockScreen
    lock = LockScreen(demo_mode=demo)

    def on_unlock():
        print("[Main] Screen unlocked!")
        app.quit()

    lock.unlocked.connect(on_unlock)

    if demo:
        lock.resize(1000, 700)
        lock.show()
    else:
        lock.showFullScreen()

    # Allow Ctrl+C in demo mode
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec())


def cmd_enroll():
    """Open enrollment management window."""
    app = setup_app()

    from src.enrollment_window import EnrollmentWindow
    window = EnrollmentWindow()
    window.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())


def cmd_status():
    """Print sensor and enrollment status."""
    from src.fingerprint_dbus import FingerprintManager

    fp = FingerprintManager()

    print("=" * 50)
    print("  Fingerprint Sensor Status")
    print("=" * 50)

    devices = fp.get_devices()
    if not devices:
        print("\n  ❌ No fingerprint sensor detected!")
        print("  Make sure the elanmoc2 driver is installed.")
        print("  Run: scripts/setup-driver.sh")
        return

    print(f"\n  ✅ Found {len(devices)} device(s)")

    info = fp.get_device_info()
    if info:
        print(f"  Name:         {info.get('name', 'Unknown')}")
        print(f"  Scan type:    {info.get('scan-type', 'Unknown')}")
        print(f"  Enroll stages: {info.get('num-enroll-stages', 'Unknown')}")

    print(f"\n  Enrolled fingerprints:")
    enrolled = fp.list_enrolled_fingers()
    if enrolled:
        from src.config import config
        for finger in enrolled:
            name = config.get_finger_name(finger)
            print(f"    ✅ {name} ({finger})")
    else:
        print("    (none)")

    print()


def cmd_test():
    """Quick fingerprint verification test."""
    from src.fingerprint_dbus import FingerprintManager
    import time

    fp = FingerprintManager()

    if not fp.has_device():
        print("❌ No fingerprint sensor detected!")
        return

    enrolled = fp.list_enrolled_fingers()
    if not enrolled:
        print("❌ No fingerprints enrolled! Run: python3 -m src.main enroll")
        return

    print("Place your finger on the sensor...")

    result = {"done": False, "match": False}

    def on_status(status, is_match):
        result["done"] = True
        result["match"] = is_match
        msg = fp.get_verify_message(status)
        if is_match:
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")

    fp.claim_device()
    fp.start_verify("any", on_status=on_status)

    # Wait for result (with timeout)
    import gi
    gi.require_version("GLib", "2.0")
    from gi.repository import GLib
    loop = GLib.MainLoop()

    def check_done():
        if result["done"]:
            loop.quit()
            return False
        return True

    GLib.timeout_add(100, check_done)
    GLib.timeout_add(15000, lambda: (loop.quit(), print("⏰ Timeout!")))
    loop.run()

    fp.cleanup()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "lock":
        demo = "--demo" in sys.argv
        cmd_lock(demo=demo)
    elif command == "enroll":
        cmd_enroll()
    elif command == "status":
        cmd_status()
    elif command == "test":
        cmd_test()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
