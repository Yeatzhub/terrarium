#!/bin/bash
# Fix for remote desktop with P40 (compute-only GPU)

# Option 1: Create virtual display with Xvfb
# Run this if XRDP gives black screen

if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting virtual display..."
    Xvfb :99 -screen 0 1920x1080x24 &
    sleep 2
fi

# Option 2: Force Intel iGPU for the session
export DISPLAY=:0
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia

# Option 3: Create simple X11 config in user dir
mkdir -p ~/.config/X11/xorg.conf.d/

cat > ~/.config/X11/xorg.conf.d/99-intel-display.conf << 'EOF'
Section "Device"
    Identifier "Card0"
    Driver "intel"
    BusID "PCI:0:2:0"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "Card0"
EndSection

Section "ServerLayout"
    Identifier "Layout0"
    Screen "Screen0"
EndSection
EOF

echo "Config created at ~/.config/X11/xorg.conf.d/99-intel-display.conf"
echo ""
echo "To apply:"
echo "1. Log out of current session"
echo "2. Log back in via XRDP"
echo ""
echo "Or try connecting to existing session:"
echo "  DISPLAY=:0 x11vnc -display :0 -forever -usepw"
