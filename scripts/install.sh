#!/bin/bash
# ================================================================
#  Fingerprint Lock Screen — Installer
#  Installs the lock screen as a system service
# ================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="fingerprint-lock"
USER_NAME="$(whoami)"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Fingerprint Lock Screen — Installer${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Step 1: Verify sensor
echo -e "${BLUE}[1/5] Checking fingerprint sensor...${NC}"
if fprintd-list "$USER_NAME" 2>&1 | grep -qi "No devices"; then
    echo -e "${RED}  ❌ No fingerprint sensor detected!${NC}"
    echo -e "${RED}  Run setup-driver.sh first.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Sensor available${NC}"

# Step 2: Check Python deps
echo ""
echo -e "${BLUE}[2/5] Checking Python dependencies...${NC}"
python3 -c "import PyQt6.QtWidgets; import dbus; import pam" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}  Installing missing Python packages...${NC}"
    pip3 install --user PyQt6 dbus-python python-pam
fi
echo -e "${GREEN}  ✅ All dependencies available${NC}"

# Step 3: Install application
echo ""
echo -e "${BLUE}[3/5] Installing application...${NC}"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
mkdir -p "$INSTALL_DIR"
cp -r "$PROJECT_DIR/src" "$INSTALL_DIR/"
echo -e "${GREEN}  ✅ Installed to $INSTALL_DIR${NC}"

# Step 4: Create launcher script
echo ""
echo -e "${BLUE}[4/5] Creating launcher...${NC}"
mkdir -p "$HOME/.local/bin"

cat > "$HOME/.local/bin/$APP_NAME" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
exec python3 -m src.main "\$@"
EOF
chmod +x "$HOME/.local/bin/$APP_NAME"

# Enrollment launcher
cat > "$HOME/.local/bin/${APP_NAME}-enroll" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
exec python3 -m src.main enroll
EOF
chmod +x "$HOME/.local/bin/${APP_NAME}-enroll"

echo -e "${GREEN}  ✅ Launchers created${NC}"

# Step 5: Create desktop entries
echo ""
echo -e "${BLUE}[5/5] Creating desktop entries...${NC}"
mkdir -p "$HOME/.local/share/applications"

cat > "$HOME/.local/share/applications/$APP_NAME-settings.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Fingerprint Settings
Comment=Manage fingerprint enrollment
Exec=$HOME/.local/bin/${APP_NAME}-enroll
Icon=fingerprint-gui
Terminal=false
Categories=Settings;Security;
Keywords=fingerprint;biometric;lock;security;
EOF

echo -e "${GREEN}  ✅ Desktop entries created${NC}"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Usage:"
echo -e "  ${BLUE}fingerprint-lock lock${NC}         — Lock the screen"
echo -e "  ${BLUE}fingerprint-lock lock --demo${NC}  — Demo mode (windowed)"
echo -e "  ${BLUE}fingerprint-lock enroll${NC}       — Manage fingerprints"
echo -e "  ${BLUE}fingerprint-lock status${NC}       — Check sensor status"
echo -e "  ${BLUE}fingerprint-lock test${NC}         — Quick verify test"
echo ""
echo -e "  Or search '${BLUE}Fingerprint Settings${NC}' in GNOME Activities"
echo ""
