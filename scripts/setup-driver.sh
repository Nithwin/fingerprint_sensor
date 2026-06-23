#!/bin/bash
# ================================================================
#  ELAN 04f3:0c00 Fingerprint Sensor — Driver Setup Script
#  Builds and installs the elanmoc2 branch of libfprint
# ================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LIBFPRINT_DIR="$PROJECT_DIR/libfprint-elanmoc2"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  ELAN Fingerprint Sensor Driver Setup${NC}"
echo -e "${BLUE}  For: ELAN 04f3:0c00 (ELAN:ARM-M4)${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if running as root for install steps
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: This script will need sudo for installation steps.${NC}"
    echo ""
fi

# Step 1: Check for the sensor
echo -e "${BLUE}[1/6] Checking for ELAN fingerprint sensor...${NC}"
if lsusb | grep -q "04f3:0c00"; then
    echo -e "${GREEN}  ✅ ELAN 04f3:0c00 sensor detected!${NC}"
else
    echo -e "${RED}  ❌ ELAN sensor not found! Make sure the sensor is enabled in BIOS.${NC}"
    exit 1
fi

# Step 2: Install build dependencies
echo ""
echo -e "${BLUE}[2/6] Installing build dependencies...${NC}"
sudo dnf install -y \
    glib2-devel \
    libgusb-devel \
    gobject-introspection-devel \
    pixman-devel \
    nss-devel \
    libgudev-devel \
    gtk-doc \
    meson \
    ninja-build \
    git

echo -e "${GREEN}  ✅ Dependencies installed${NC}"

# Step 3: Clone libfprint elanmoc2 branch
echo ""
echo -e "${BLUE}[3/6] Cloning libfprint (elanmoc2 branch)...${NC}"
if [ -d "$LIBFPRINT_DIR" ]; then
    echo "  Directory exists, pulling latest..."
    cd "$LIBFPRINT_DIR"
    git pull || true
else
    git clone https://gitlab.freedesktop.org/depau/libfprint.git "$LIBFPRINT_DIR"
    cd "$LIBFPRINT_DIR"
    git switch elanmoc2
fi
echo -e "${GREEN}  ✅ Source code ready${NC}"

# Step 4: Build
echo ""
echo -e "${BLUE}[4/6] Building libfprint...${NC}"
cd "$LIBFPRINT_DIR"
if [ -d "builddir" ]; then
    rm -rf builddir
fi
meson setup builddir
cd builddir
ninja
echo -e "${GREEN}  ✅ Build successful${NC}"

# Step 5: Install
echo ""
echo -e "${BLUE}[5/6] Installing libfprint...${NC}"
sudo ninja install

# Configure library path
echo -e "/usr/local/lib
/usr/local/lib64" | sudo tee /etc/ld.so.conf.d/local-libfprint.conf > /dev/null
sudo ldconfig
echo -e "${GREEN}  ✅ Installed and library cache updated${NC}"

# Step 6: Restart fprintd and verify
echo ""
echo -e "${BLUE}[6/6] Restarting fingerprint service...${NC}"
sudo systemctl restart fprintd.service
sleep 2

# Verify
echo ""
echo -e "${BLUE}Verifying sensor detection...${NC}"
if fprintd-list "$USER" 2>&1 | grep -qi "using device"; then
    echo -e "${GREEN}  ✅ Sensor detected by fprintd!${NC}"
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Driver installation SUCCESSFUL!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "You can now enroll fingerprints:"
    echo -e "  ${BLUE}python3 -m src.main enroll${NC}"
    echo ""
    echo -e "Or test with the system tool:"
    echo -e "  ${BLUE}fprintd-enroll${NC}"
else
    echo -e "${YELLOW}  ⚠️  Sensor may need a moment to initialize.${NC}"
    echo -e "${YELLOW}  Try running: fprintd-list \$USER${NC}"
    echo -e "${YELLOW}  If still not working, try rebooting.${NC}"
fi
