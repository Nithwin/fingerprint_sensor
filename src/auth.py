"""
PAM authentication module for password fallback.
Provides secure password verification when fingerprint is unavailable.
"""

import pam
import os
import subprocess
from typing import Optional, Tuple


class PAMAuthenticator:
    """
    Handles password-based authentication via PAM.
    Used as a fallback when fingerprint authentication fails.
    """

    def __init__(self):
        self._pam = pam.pam()
        self._username = os.environ.get("USER", os.getlogin())

    def verify_password(self, password: str, username: str = "") -> Tuple[bool, str]:
        """
        Verify a user's password via PAM.
        
        Args:
            password: The password to verify
            username: Username (defaults to current user)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        user = username or self._username
        try:
            result = self._pam.authenticate(user, password, service="login")
            if result:
                return True, "Authentication successful"
            else:
                reason = self._pam.reason or "Invalid password"
                return False, str(reason)
        except Exception as e:
            return False, f"Authentication error: {e}"

    def get_username(self) -> str:
        """Get the current username."""
        return self._username

    def get_user_display_name(self) -> str:
        """Get the user's display name (from GECOS field)."""
        try:
            import pwd
            pw = pwd.getpwnam(self._username)
            gecos = pw.pw_gecos
            # GECOS field is comma-separated, first field is full name
            display_name = gecos.split(",")[0] if gecos else self._username
            return display_name if display_name else self._username
        except (KeyError, ImportError):
            return self._username

    def get_user_avatar_path(self) -> Optional[str]:
        """Get the path to the user's avatar image."""
        # Check AccountsService avatar
        avatar_path = f"/var/lib/AccountsService/icons/{self._username}"
        if os.path.exists(avatar_path):
            return avatar_path

        # Check GNOME user icon
        home = os.path.expanduser("~")
        face_path = os.path.join(home, ".face")
        if os.path.exists(face_path):
            return face_path

        return None

    def get_hostname(self) -> str:
        """Get the system hostname."""
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return "fedora"
