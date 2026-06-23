# 🔐 Fingerprint Lock Screen for Fedora

A Windows Hello-inspired fingerprint lock screen for Fedora Linux with beautiful animations.

## Features

- 🎨 **Stunning Lock Screen** — Blurred desktop background with glassmorphism design
- 🔒 **Fingerprint Authentication** — Uses your laptop's built-in fingerprint sensor
- ✨ **Smooth Animations** — Pulse glow, scanning ripple, success particles, failure shake
- 👆 **Multi-Fingerprint Support** — Enroll up to 10 fingers with visual hand diagram
- 🔑 **Password Fallback** — Secure password input when fingerprint fails
- 🖥️ **Multi-Monitor** — Works across all connected displays
- ⚡ **Lightweight** — Pure Python with PyQt6, minimal resources

## Quick Start

### 1. Set Up the Fingerprint Driver

Your ELAN 04f3:0c00 sensor needs a custom driver:

```bash
./scripts/setup-driver.sh
```

### 2. Enroll Fingerprints

```bash
python3 -m src.main enroll
```

### 3. Try the Lock Screen (Demo Mode)

```bash
python3 -m src.main lock --demo
```

### 4. Install System-Wide

```bash
./scripts/install.sh
```

## Commands

| Command | Description |
|---|---|
| `fingerprint-lock lock` | Lock the screen |
| `fingerprint-lock lock --demo` | Demo mode (windowed) |
| `fingerprint-lock enroll` | Manage fingerprints |
| `fingerprint-lock status` | Check sensor status |
| `fingerprint-lock test` | Quick verify test |

## Tech Stack

- **Python 3.14** — Core language
- **PyQt6** — UI framework with animation support
- **fprintd + libfprint** — Fingerprint daemon (elanmoc2 branch)
- **PAM** — Password authentication fallback
- **D-Bus** — Communication with fprintd

## Project Structure

```
fingerprint_sensor/
├── src/
│   ├── main.py              # Entry point
│   ├── lock_screen.py        # Lock screen window
│   ├── enrollment_window.py  # Enrollment management
│   ├── fingerprint_dbus.py   # fprintd D-Bus client
│   ├── auth.py               # PAM authentication
│   ├── config.py             # Configuration
│   ├── widgets/              # UI components
│   └── animations/           # Animation effects
├── scripts/
│   ├── setup-driver.sh       # ELAN driver installer
│   ├── install.sh            # App installer
│   └── uninstall.sh          # Uninstaller
└── README.md
```

## Requirements

- Fedora 44 (or later)
- HP laptop with ELAN fingerprint sensor
- GNOME desktop on Wayland
- Python 3.10+, PyQt6, dbus-python, python-pam
