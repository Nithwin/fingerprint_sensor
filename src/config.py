"""
Configuration management for Fingerprint Lock Screen.
Stores user preferences, enrolled finger names, and UI settings.
"""

import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration with persistent storage."""

    DEFAULT_CONFIG = {
        "animation_speed": 1.0,          # Animation speed multiplier
        "idle_timeout": 300,             # Seconds before auto-lock
        "max_verify_attempts": 5,        # Max failures before password-only
        "show_clock": True,
        "show_battery": True,
        "show_network": True,
        "blur_radius": 40,              # Wallpaper blur radius
        "theme": "dark",                # "dark" or "light"
        "accent_color": "#3B82F6",      # Blue accent
        "success_color": "#10B981",     # Green
        "failure_color": "#EF4444",     # Red
        "scanning_color": "#F59E0B",    # Amber
        "finger_names": {},             # {finger_id: custom_name}
        "lock_on_suspend": True,
        "lock_on_lid_close": True,
        "enable_sound": False,
        "font_family": "Inter",
    }

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "fingerprint-lock"
        self.config_file = self.config_dir / "config.json"
        self.data = dict(self.DEFAULT_CONFIG)
        self._load()

    def _load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    saved = json.load(f)
                self.data.update(saved)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Config] Warning: Could not load config: {e}")

    def save(self):
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"[Config] Warning: Could not save config: {e}")

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.data.get(key, default)

    def set(self, key: str, value):
        """Set a configuration value and save."""
        self.data[key] = value
        self.save()

    def get_finger_name(self, finger_id: str) -> str:
        """Get the custom name for an enrolled finger."""
        names = self.data.get("finger_names", {})
        # Provide readable defaults
        default_names = {
            "left-thumb": "Left Thumb",
            "left-index-finger": "Left Index",
            "left-middle-finger": "Left Middle",
            "left-ring-finger": "Left Ring",
            "left-little-finger": "Left Little",
            "right-thumb": "Right Thumb",
            "right-index-finger": "Right Index",
            "right-middle-finger": "Right Middle",
            "right-ring-finger": "Right Ring",
            "right-little-finger": "Right Little",
        }
        return names.get(finger_id, default_names.get(finger_id, finger_id))

    def set_finger_name(self, finger_id: str, name: str):
        """Set a custom name for an enrolled finger."""
        if "finger_names" not in self.data:
            self.data["finger_names"] = {}
        self.data["finger_names"][finger_id] = name
        self.save()


# Global config instance
config = Config()
