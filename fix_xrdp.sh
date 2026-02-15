#!/bin/bash
# Fix xrdp configuration for concurrent sessions

echo "Fixing xrdp configuration..."

# Backup original config
sudo cp /etc/xrdp/xrdp.ini /etc/xrdp/xrdp.ini.backup.$(date +%Y%m%d_%H%M%S)

# Update MaxLoginRetry
if grep -q "MaxLoginRetry" /etc/xrdp/xrdp.ini; then
    sudo sed -i 's/MaxLoginRetry=.*/MaxLoginRetry=10/' /etc/xrdp/xrdp.ini
    echo "✓ Updated MaxLoginRetry to 10"
else
    echo "MaxLoginRetry=10" | sudo tee -a /etc/xrdp/xrdp.ini > /dev/null
    echo "✓ Added MaxLoginRetry=10"
fi

# Set up session file
echo "gnome-session" > ~/.xsession
chmod +x ~/.xsession
echo "✓ Created ~/.xsession"

# Restart services
echo "Restarting xrdp services..."
sudo systemctl restart xrdp-sesman
sudo systemctl restart xrdp
echo "✓ Services restarted"

# Check status
echo ""
echo "Checking xrdp status:"
sudo systemctl status xrdp --no-pager -l | grep "Active:"

# Show listening ports
echo ""
echo "Listening ports:"
ss -tlnp | grep -E "(3389|3350)" || netstat -tlnp 2>/dev/null | grep -E "(3389|3350)" || echo "Port status check needs elevated access"

echo ""
echo "========================================="
echo "Fix applied! Try connecting now from Android."
echo "Use: 192.168.12.6:3389"
echo "========================================="