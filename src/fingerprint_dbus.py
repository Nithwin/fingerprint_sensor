"""
D-Bus client for fprintd — the Fingerprint Authentication Daemon.
Handles enrollment, verification, listing, and deletion of fingerprints.
"""

import dbus
import dbus.mainloop.glib
from dbus.mainloop.glib import DBusGMainLoop
from typing import Optional, List, Callable
import os
import threading


# Valid finger names for fprintd
FINGER_NAMES = [
    "left-thumb", "left-index-finger", "left-middle-finger",
    "left-ring-finger", "left-little-finger",
    "right-thumb", "right-index-finger", "right-middle-finger",
    "right-ring-finger", "right-little-finger",
]

# Enrollment status messages
ENROLL_STATUS_MESSAGES = {
    "enroll-completed": "Enrollment completed successfully!",
    "enroll-failed": "Enrollment failed. Please try again.",
    "enroll-stage-passed": "Good! Keep going...",
    "enroll-retry-scan": "Didn't quite get that. Try again.",
    "enroll-swipe-too-short": "Swipe was too short. Try again.",
    "enroll-finger-not-centered": "Finger not centered. Adjust position.",
    "enroll-remove-and-retry": "Remove finger and try again.",
    "enroll-data-full": "Storage full. Delete some fingerprints first.",
    "enroll-disconnected": "Sensor disconnected!",
    "enroll-unknown-error": "Unknown error occurred.",
}

# Verify status messages
VERIFY_STATUS_MESSAGES = {
    "verify-match": "Fingerprint matched!",
    "verify-no-match": "No match. Try again.",
    "verify-retry-scan": "Couldn't read. Try again.",
    "verify-swipe-too-short": "Swipe too short.",
    "verify-finger-not-centered": "Finger not centered.",
    "verify-remove-and-retry": "Remove finger and try again.",
    "verify-disconnected": "Sensor disconnected!",
    "verify-unknown-error": "Unknown error occurred.",
}


class FingerprintManager:
    """
    Manages fingerprint operations via fprintd D-Bus interface.
    
    Provides async callbacks for enrollment/verification progress
    so the UI can show real-time animation updates.
    """

    FPRINT_SERVICE = "net.reactivated.Fprint"
    FPRINT_MANAGER_PATH = "/net/reactivated/Fprint/Manager"
    FPRINT_MANAGER_IFACE = "net.reactivated.Fprint.Manager"
    FPRINT_DEVICE_IFACE = "net.reactivated.Fprint.Device"

    def __init__(self):
        # Initialize D-Bus main loop for GLib integration
        DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SystemBus()
        self._device = None
        self._device_iface = None
        self._device_props = None
        self._claimed = False
        self._username = os.environ.get("USER", os.getlogin())

        # Callbacks
        self._on_verify_status: Optional[Callable] = None
        self._on_enroll_status: Optional[Callable] = None

        # Connect signals
        self._bus.add_signal_receiver(
            self._handle_verify_status,
            signal_name="VerifyStatus",
            dbus_interface=self.FPRINT_DEVICE_IFACE,
        )
        self._bus.add_signal_receiver(
            self._handle_enroll_status,
            signal_name="EnrollStatus",
            dbus_interface=self.FPRINT_DEVICE_IFACE,
        )

    def _get_manager(self):
        """Get the fprintd manager proxy."""
        obj = self._bus.get_object(self.FPRINT_SERVICE, self.FPRINT_MANAGER_PATH)
        return dbus.Interface(obj, self.FPRINT_MANAGER_IFACE)

    def get_devices(self) -> List[str]:
        """Get list of available fingerprint devices."""
        try:
            manager = self._get_manager()
            devices = manager.GetDevices()
            return [str(d) for d in devices]
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error getting devices: {e}")
            return []

    def has_device(self) -> bool:
        """Check if any fingerprint device is available."""
        return len(self.get_devices()) > 0

    def _get_default_device(self):
        """Get the default (first) fingerprint device."""
        try:
            manager = self._get_manager()
            device_path = manager.GetDefaultDevice()
            obj = self._bus.get_object(self.FPRINT_SERVICE, device_path)
            self._device = obj
            self._device_iface = dbus.Interface(obj, self.FPRINT_DEVICE_IFACE)
            self._device_props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error getting default device: {e}")
            return False

    def get_device_info(self) -> dict:
        """Get information about the fingerprint device."""
        if not self._device_props:
            if not self._get_default_device():
                return {}
        try:
            info = {
                "name": str(self._device_props.Get(self.FPRINT_DEVICE_IFACE, "name")),
                "num-enroll-stages": int(self._device_props.Get(
                    self.FPRINT_DEVICE_IFACE, "num-enroll-stages"
                )),
                "scan-type": str(self._device_props.Get(
                    self.FPRINT_DEVICE_IFACE, "scan-type"
                )),
            }
            return info
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error getting device info: {e}")
            return {}

    def claim_device(self, username: str = "") -> bool:
        """Claim the fingerprint device for exclusive use."""
        if not self._device_iface:
            if not self._get_default_device():
                return False
        try:
            self._device_iface.Claim(username or self._username)
            self._claimed = True
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error claiming device: {e}")
            return False

    def release_device(self) -> bool:
        """Release the fingerprint device."""
        if not self._device_iface or not self._claimed:
            return True
        try:
            self._device_iface.Release()
            self._claimed = False
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error releasing device: {e}")
            return False

    def list_enrolled_fingers(self, username: str = "") -> List[str]:
        """List all enrolled fingers for a user."""
        if not self._device_iface:
            if not self._get_default_device():
                return []
        try:
            fingers = self._device_iface.ListEnrolledFingers(
                username or self._username
            )
            return [str(f) for f in fingers]
        except dbus.exceptions.DBusException as e:
            # No enrolled fingerprints returns an error
            if "No enrolled prints" in str(e):
                return []
            print(f"[FP] Error listing fingers: {e}")
            return []

    def start_enrollment(self, finger_name: str,
                         on_status: Optional[Callable] = None) -> bool:
        """
        Start fingerprint enrollment for a specific finger.
        
        Args:
            finger_name: One of FINGER_NAMES (e.g., "right-index-finger")
            on_status: Callback(status: str, done: bool) for progress updates
        """
        if finger_name not in FINGER_NAMES:
            print(f"[FP] Invalid finger name: {finger_name}")
            return False

        if not self._claimed:
            if not self.claim_device():
                return False

        self._on_enroll_status = on_status
        try:
            self._device_iface.EnrollStart(finger_name)
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error starting enrollment: {e}")
            return False

    def stop_enrollment(self) -> bool:
        """Stop ongoing enrollment."""
        if not self._device_iface:
            return True
        try:
            self._device_iface.EnrollStop()
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error stopping enrollment: {e}")
            return False

    def start_verify(self, finger_name: str = "any",
                     on_status: Optional[Callable] = None) -> bool:
        """
        Start fingerprint verification.
        
        Args:
            finger_name: Finger to verify or "any" for any enrolled finger
            on_status: Callback(status: str, match: bool) for result
        """
        if not self._claimed:
            if not self.claim_device():
                return False

        self._on_verify_status = on_status
        try:
            self._device_iface.VerifyStart(finger_name)
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error starting verify: {e}")
            return False

    def stop_verify(self) -> bool:
        """Stop ongoing verification."""
        if not self._device_iface:
            return True
        try:
            self._device_iface.VerifyStop()
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error stopping verify: {e}")
            return False

    def delete_enrolled_fingers(self, username: str = "") -> bool:
        """Delete all enrolled fingerprints for a user."""
        if not self._claimed:
            if not self.claim_device():
                return False
        try:
            self._device_iface.DeleteEnrolledFingers(username or self._username)
            return True
        except dbus.exceptions.DBusException as e:
            print(f"[FP] Error deleting fingers: {e}")
            return False

    def delete_enrolled_finger(self, finger_name: str,
                                username: str = "") -> bool:
        """Delete a specific enrolled fingerprint."""
        if not self._claimed:
            if not self.claim_device():
                return False
        try:
            self._device_iface.DeleteEnrolledFinger2(finger_name)
            return True
        except dbus.exceptions.DBusException as e:
            # Fallback: some versions don't have DeleteEnrolledFinger2
            print(f"[FP] Error deleting finger {finger_name}: {e}")
            return False

    # --- Signal Handlers ---

    def _handle_verify_status(self, status, done):
        """Handle VerifyStatus signal from fprintd."""
        status = str(status)
        done = bool(done)
        is_match = status == "verify-match"

        print(f"[FP] Verify: {status} (done={done})")

        if self._on_verify_status:
            self._on_verify_status(status, is_match)

    def _handle_enroll_status(self, status, done):
        """Handle EnrollStatus signal from fprintd."""
        status = str(status)
        done = bool(done)
        completed = status == "enroll-completed"

        print(f"[FP] Enroll: {status} (done={done})")

        if self._on_enroll_status:
            self._on_enroll_status(status, completed)

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop_verify()
        except Exception:
            pass
        try:
            self.stop_enrollment()
        except Exception:
            pass
        self.release_device()

    def get_enroll_message(self, status: str) -> str:
        """Get human-readable message for enrollment status."""
        return ENROLL_STATUS_MESSAGES.get(status, f"Status: {status}")

    def get_verify_message(self, status: str) -> str:
        """Get human-readable message for verify status."""
        return VERIFY_STATUS_MESSAGES.get(status, f"Status: {status}")
