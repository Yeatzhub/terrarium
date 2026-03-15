#!/bin/bash
# GPU Fan Controller Cleanup Script

echo "=== Removing GPU Fan Controller ==="

# Stop and disable service
sudo systemctl stop gpu-fan.service 2>/dev/null || true
sudo systemctl disable gpu-fan.service 2>/dev/null || true

# Remove service file
sudo rm -f /etc/systemd/system/gpu-fan.service

# Remove control script
sudo rm -f /usr/local/bin/gpu-fan-control.sh

# Reload systemd
sudo systemctl daemon-reload

# Reset fan4 to auto mode
echo 2 | sudo tee /sys/class/hwmon/hwmon4/pwm4_enable 2>/dev/null || true

echo ""
echo "✓ GPU Fan Controller removed"
echo "✓ Fan4 set to auto mode"
echo ""
echo "Current fan speeds:"
sensors | grep fan