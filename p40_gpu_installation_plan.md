# Tesla P40 GPU Installation Plan

## Delivery Status

**Tracking Number**: 9405508106245831259625  
**Status**: ⚠️ **MANUAL VERIFICATION REQUIRED**

> USPS tracking websites use heavy JavaScript obfuscation that prevents automated checking. Please verify delivery status manually at:
> - https://tools.usps.com/go/TrackConfirmAction?tLabels=9405508106245831259625
> - or https://parcelsapp.com (mobile app recommended)

**Items Expected**:
- [ ] Tesla P40 24GB GPU
- [x] Noctua fan (delivered Feb 16 per user context)
- [ ] PCIe adapter/riser

---

## System Analysis: yeatz-MS-7A46

### Current Hardware
| Component | Details |
|-----------|---------|
| **Motherboard** | MSI B150M BAZOOKA PLUS (MS-7A46) |
| **CPU** | Intel Core i5-6600K @ 3.5GHz (Skylake) |
| **Memory** | 32GB DDR4 |
| **Current GPU** | AMD Radeon RX 580 (in PCIe x16 slot) |
| **PCIe Configuration** | Gen3 x16 @ 8.0 GT/s confirmed |
| **Storage** | SK Hynix NVMe SSD |
| **Network** | Intel AX200 Wi-Fi 6, Realtek Gigabit |
| **OS** | Zorin OS 17.3 (Ubuntu 22.04 Jammy base) |
| **Kernel** | 6.8.0-94-generic |

### PCIe Slot Layout
```
-[0000:00]-+-00.0  Host Bridge (Intel)
           +-01.0-[01]--+-00.0  AMD RX 580 (Current GPU - x16 slot)
           |            \-00.1  AMD HDMI Audio
           +-02.0  Intel HD Graphics 530
           +-1c.0-[02]----00.0  Realtek Ethernet (x1)
           +-1c.6-[03]----00.0  Intel Wi-Fi 6 AX200 (x1)
           +-1d.0-[04]----00.0  SK Hynix NVMe (x4)
```

**Key Finding**: Only one PCIe x16 slot available, currently occupied by RX 580.

---

## P40 GPU Specifications

| Spec | Details |
|------|---------|
| **GPU Architecture** | NVIDIA Pascal |
| **Memory** | 24GB GDDR5X |
| **Memory Bandwidth** | 346 GB/s |
| **CUDA Cores** | 3,840 |
| **TDP** | **250W** (revised: not 300W) |
| **Power Connectors** | 1x 8-pin + 1x 6-pin PCIe |
| **PCIe Interface** | PCIe 3.0 x16 |
| **Cooling** | Passive (requires active airflow) |
| **Display Outputs** | NONE (compute-only) |
| **Form Factor** | Dual-slot, 10.5" length |

### Critical Notes
- ⚠️ **NO VIDEO OUTPUT** - You need the iGPU (Intel HD 530) or another GPU for display
- ⚠️ **PASSIVE COOLING** - Requires the Noctua fan for airflow
- ⚠️ **PCIe x16 SLOT REQUIRED** - Must replace RX 580 or use riser (not recommended for P40)

---

## Hardware Compatibility Assessment

### ✅ Compatible
- [x] PCIe 3.0 x16 slot available
- [x] CPU has iGPU (Intel HD 530) for display output
- [x] Motherboard supports above 75W PCIe power
- [x] 32GB RAM sufficient for large models

### ⚠️ Concerns
- [ ] **PSU Wattage Unknown** - Need to verify sufficient power (recommend 500W+ for single P40)
- [ ] **Physical Space** - Verify case clearance for 10.5" dual-slot card
- [ ] **Cooling Mod** - Must install Noctua fan to blow across P40 heatsink

### ❌ Blockers
- [ ] **Slot Occupied** - RX 580 currently in the x16 slot

---

## Installation Options

### Option 1: Replace RX 580 with P40 (Recommended)
**Setup**: Remove RX 580, install P40 in x16 slot, use Intel iGPU for display

**Pros**:
- Full x16 bandwidth for P40
- Cleanest configuration
- P40 gets maximum cooling/airflow

**Cons**:
- Lose RX 580 gaming capability
- Must rely on Intel HD 530 for display

**Power Requirements**: 
- i5-6600K: ~95W
- P40: ~250W
- System overhead: ~50W
- **Minimum PSU: 450W** (recommend 550W+)

---

### Option 2: Keep Both GPUs (Advanced)
**Setup**: Use PCIe riser/extender for P40, keep RX 580

**Pros**:
- Keep gaming GPU (RX 580)
- Compute and graphics separated

**Cons**:
- P40 limited to x1/x4 bandwidth on riser
- Complexity of dual-GPU setup
- Power/thermal concerns
- **NOT RECOMMENDED** for P40 (needs x16 bandwidth)

---

## Installation Checklist

### Pre-Installation
- [ ] Verify PSU wattage (label on unit or `sudo dmidecode -t power`)
- [ ] Measure case clearance (need 10.5" length, 2 slots)
- [ ] Confirm delivery of P40 and PCIe adapter
- [ ] Backup current system

### Physical Installation
- [ ] Power off and unplug system
- [ ] Remove RX 580 (store safely if keeping)
- [ ] Install P40 in top PCIe x16 slot
- [ ] Connect 8-pin + 6-pin PCIe power cables
- [ ] Mount Noctua fan to blow directly across P40 heatsink
- [ ] Verify fan positioned to push air through P40 fins

### BIOS Configuration
- [ ] Enter BIOS (DEL key during boot)
- [ ] Set Primary Display to `iGPU` or `Internal`
- [ ] Enable `Above 4G Decoding` (required for compute cards)
- [ ] Set PCIe to Gen3 (disable auto/Gen4 if available)
- [ ] Save and exit

### Software Installation
```bash
# 1. Install NVIDIA drivers
sudo apt update
sudo apt install nvidia-driver-550  # or latest

# 2. Install CUDA toolkit (optional)
sudo apt install nvidia-cuda-toolkit

# 3. Reboot
sudo reboot

# 4. Verify installation
nvidia-smi
```

### Post-Installation Verification
- [ ] `nvidia-smi` shows P40 with 24GB memory
- [ ] Temperature under load < 85°C
- [ ] Noctua fan spinning and providing airflow
- [ ] Intel iGPU driving display (check with `glxinfo | grep renderer`)

---

## Driver Information

**Recommended Driver**: NVIDIA 550.x or later (R550/R570 series)

**Ubuntu 22.04/Zorin 17 Install**:
```bash
# Method 1: Standard Ubuntu drivers
sudo ubuntu-drivers autoinstall

# Method 2: Latest from graphics-drivers PPA
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update
sudo apt install nvidia-driver-550

# Method 3: Manual from NVIDIA (most recent)
wget https://us.download.nvidia.com/tesla/550.90.07/NVIDIA-Linux-x86_64-550.90.07.run
sudo bash NVIDIA-Linux-x86_64-550.90.07.run
```

---

## Daily Tracking Check Script

Create this script to check delivery status daily:

```bash
#!/bin/bash
# ~/check_p40_delivery.sh

TRACKING="9405508106245831259625"
LOGFILE="~/p40_delivery.log"
DATE=$(date '+%Y-%m-%d %H:%M')

# Use curl to check (may need tweaking for USPS API)
echo "[$DATE] Checking delivery status..." >> $LOGFILE

# Note: Actual USPS API requires registration
# For now, manual checking is recommended:
# https://tools.usps.com/go/TrackConfirmAction?tLabels=$TRACKING
```

**Recommended**: Set a phone reminder to check tracking daily or use the USPS mobile app with notifications enabled.

---

## Action Items Summary

### Immediate Actions
1. ✅ System analyzed - PCIe x16 slot confirmed, iGPU available
2. ⚠️ **MANUAL**: Check tracking at https://tools.usps.com/go/TrackConfirmAction?tLabels=9405508106245831259625
3. ⚠️ **VERIFY**: Check PSU wattage (look for label or run `sudo dmidecode -t power`)
4. ⚠️ **VERIFY**: Measure case clearance for 10.5" card

### Upon Delivery
1. Install P40 in x16 slot (replace RX 580 or decide on dual-GPU)
2. Mount Noctua fan for active cooling
3. Connect PCIe power (8-pin + 6-pin)
4. Configure BIOS for iGPU primary display
5. Install NVIDIA drivers
6. Run `nvidia-smi` to verify

---

## Notes

- **Noctua fan delivered Feb 16**: Ready for cooling mod installation
- **PCIe adapter included**: May be riser cable or power adapter - verify on arrival
- **Kernel 6.8**: Modern kernel, good NVIDIA driver support
- **Zorin 17.3**: Ubuntu 22.04 base, compatible with NVIDIA datacenter drivers

---

*Plan generated: 2026-02-16*  
*System: yeatz-MS-7A46*  
*Tracking: 9405508106245831259625*
