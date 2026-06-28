"""
D-Bus Service for org.freedesktop.ScreenSaver
Intercepts lock requests and launches the fingerprint lock screen.
"""

import sys
import subprocess
import dbus
import dbus.service
"""
D-Bus Service for listening to system lock and sleep events.
"""

import sys
import subprocess
import dbus
import dbus.mainloop.glib
from gi.repository import GLib

def run_dbus_service():
    """Start the DBus service and block."""
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    
    try:
        # Listen to GNOME ScreenSaver active state
        session_bus.add_signal_receiver(
            on_gnome_screensaver_active_changed,
            signal_name='ActiveChanged',
            dbus_interface='org.gnome.ScreenSaver'
        )
        
        # Listen for sleep/suspend signals from systemd
        system_bus = dbus.SystemBus()
        system_bus.add_signal_receiver(
            on_sleep,
            signal_name='PrepareForSleep',
            dbus_interface='org.freedesktop.login1.Manager',
            bus_name='org.freedesktop.login1'
        )

        print("[Service] Listening for lock and sleep events...")
        
        loop = GLib.MainLoop()
        loop.run()
    except dbus.exceptions.DBusException as e:
        print(f"Error starting service: {e}")
        sys.exit(1)

def on_gnome_screensaver_active_changed(active):
    """Callback for GNOME ScreenSaver lock events."""
    if active:
        print("[Service] GNOME screensaver activated, launching custom lock screen...")
        # Launch lock screen with a small delay so it appears over GNOME's lock
        GLib.timeout_add(300, lambda: (subprocess.Popen(["python3", "-m", "src.main", "lock"]), False))

def on_sleep(is_sleeping):
    """Callback for systemd sleep/suspend events."""
    if is_sleeping:
        from src.config import config
        if config.get("lock_on_suspend", True):
            print("[Service] System is suspending, launching lock screen...")
            subprocess.Popen(["python3", "-m", "src.main", "lock"])
