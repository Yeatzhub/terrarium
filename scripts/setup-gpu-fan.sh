#!/bin/bash
# GPU Fan Controller Setup Script
# Pairs fan4 with GPU temperature via nvidia-smi

set -e

echo "=== GPU Fan Controller Setup ==="

# Check prerequisites
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi not found. NVIDIA drivers required."
    exit 1
fi

if [ ! -d "/sys/class/hwmon/hwmon4" ]; then
    echo "ERROR: hwmon4 not found. Run sensors-detect first."
    exit 1
fi

# Create fan control script
echo "Creating /usr/local/bin/gpu-fan-control.sh ..."
sudo tee /usr/local/bin/gpu-fan-control.sh > /dev/null << 'SCRIPT'
#!/bin/bash
# GPU Fan Controller for fan4
HWMON="/sys/class/hwmon/hwmon4"
PWM="pwm4"
ENABLE="pwm4_enable"

# GPU temp thresholds
MIN_TEMP=40
MAX_TEMP=80
MIN_PWM=80   # ~30% min speed
MAX_PWM=255  # 100% max speed

# Set manual mode
echo 1 > "$HWMON/$ENABLE"

while true; do
    GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null)
    
    if [[ -n "$GPU_TEMP" ]]; then
        # Linear scaling: temp → PWM
        if (( GPU_TEMP <= MIN_TEMP )); then
            PWM_VAL=$MIN_PWM
        elif (( GPU_TEMP >= MAX_TEMP )); then
            PWM_VAL=$MAX_PWM
        else
            PWM_VAL=$(( MIN_PWM + (GPU_TEMP - MIN_TEMP) * (MAX_PWM - MIN_PWM) / (MAX_TEMP - MIN_TEMP) ))
        fi
        
        echo $PWM_VAL > "$HWMON/$PWM"
    fi
    
    sleep 5
done
SCRIPT

sudo chmod +x /usr/local/bin/gpu-fan-control.sh
echo "✓ Script installed"

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/gpu-fan.service > /dev/null << 'SERVICE'
[Unit]
Description=GPU Fan Controller
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/bin/gpu-fan-control.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

echo "✓ Service created"

# Enable and start
echo "Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable gpu-fan.service
sudo systemctl start gpu-fan.service

echo ""
echo "=== Done! ==="
echo "GPU fan controller is now running."
echo ""
echo "Commands:"
echo "  Status:   sudo systemctl status gpu-fan"
echo "  Stop:     sudo systemctl stop gpu-fan"
echo "  Logs:     sudo journalctl -u gpu-fan -f"
echo ""
echo "Current fan speeds:"
sensors | grep fan