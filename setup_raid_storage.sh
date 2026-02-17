#!/bin/bash
# RAID 0 Setup Script for 2x 2TB drives
# Run with: sudo bash setup_raid_storage.sh

set -e  # Exit on error

echo "=========================================="
echo "   RAID 0 Storage Setup Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo bash setup_raid_storage.sh"
    exit 1
fi

# Detect drives
echo "🔍 Detecting drives..."
DRIVE1="/dev/sda"
DRIVE2="/dev/sdb"

# Verify drives exist
if [ ! -b "$DRIVE1" ] || [ ! -b "$DRIVE2" ]; then
    echo "❌ Drives not found. Expected $DRIVE1 and $DRIVE2"
    lsblk -d -o NAME,SIZE,MODEL | grep -E "(sda|sdb)"
    exit 1
fi

echo "✅ Found drives:"
echo "   Drive 1: $DRIVE1 ($(lsblk -dn -o SIZE $DRIVE1))"
echo "   Drive 2: $DRIVE2 ($(lsblk -dn -o SIZE $DRIVE2))"
echo ""

# Install required packages
echo "📦 Installing packages (mdadm, xfsprogs)..."
apt-get update -qq
apt-get install -y -qq mdadm xfsprogs

echo "✅ Packages installed"
echo ""

# Warning and confirmation
echo "⚠️  WARNING: This will DESTROY all data on $DRIVE1 and $DRIVE2"
echo "   Current partitions:"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E "(sda|sdb)"
echo ""
echo "   RAID 0 will give you:"
echo "   - 4TB usable space (2TB + 2TB striped)"
echo "   - High performance"
echo "   - NO redundancy (one drive fails = all data lost)"
echo ""

# Unmount any existing mounts
echo "🔓 Unmounting any existing partitions..."
umount ${DRIVE1}* 2>/dev/null || true
umount ${DRIVE2}* 2>/dev/null || true

# Wipe drives
echo "🧹 Wiping drive signatures..."
wipefs -a $DRIVE1 2>/dev/null || true
wipefs -a $DRIVE2 2>/dev/null || true

# Create RAID 0 array
echo ""
echo "🛠️  Creating RAID 0 array..."
mdadm --create /dev/md0 --level=0 --raid-devices=2 $DRIVE1 $DRIVE2 --force

echo "✅ RAID array created"
echo ""

# Wait for array to initialize
echo "⏳ Waiting for array initialization..."
sleep 2
mdadm --detail /dev/md0 | grep -E "(State|Size|Devices)"
echo ""

# Format with XFS
echo "💾 Formatting with XFS filesystem..."
mkfs.xfs -f -L storage /dev/md0

echo "✅ Filesystem created"
echo ""

# Create mount point
echo "📁 Creating mount point /storage..."
mkdir -p /storage

# Get UUID for fstab
UUID=$(blkid -s UUID -o value /dev/md0)
echo "   UUID: $UUID"

# Add to /etc/fstab if not already present
if ! grep -q "$UUID" /etc/fstab; then
    echo "📝 Adding to /etc/fstab..."
    echo "UUID=$UUID /storage xfs defaults,noatime 0 2" >> /etc/fstab
    echo "✅ Added to fstab"
else
    echo "ℹ️  Already in fstab"
fi

# Mount
echo "📂 Mounting /storage..."
mount /dev/md0 /storage

# Set permissions (replace 'yeatz' with your username)
USERNAME="${SUDO_USER:-$USER}"
if [ "$USERNAME" = "root" ]; then
    USERNAME="yeatz"  # fallback
fi

echo "🔐 Setting ownership to $USERNAME..."
chown -R $USERNAME:$USERNAME /storage
chmod 755 /storage

# Update initramfs to include RAID config
echo "🔄 Updating initramfs..."
update-initramfs -u

# Save RAID config
echo "💾 Saving RAID configuration..."
mdadm --detail --scan >> /etc/mdadm/mdadm.conf
update-initramfs -u

echo ""
echo "=========================================="
echo "   ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Summary:"
df -h /storage

echo ""
echo "🔧 RAID Status:"
cat /proc/mdstat | head -5

echo ""
echo "📋 Details:"
mdadm --detail /dev/md0 | grep -E "(RAID Level|Array Size|State|Devices)"

echo ""
echo "💡 Usage:"
echo "   Location: /storage"
echo "   Space: ~4TB usable"
echo "   Mount: Auto-mounts on boot"
echo ""
echo "⚠️  Remember: RAID 0 has NO redundancy!"
echo "   Backup important data elsewhere."
echo ""
echo "Done! 🎉"
