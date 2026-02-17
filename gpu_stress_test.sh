#!/bin/bash
# GPU Stress Test Monitor for Tesla P40
# Usage: bash gpu_stress_test.sh

echo "==================================================="
echo "Tesla P40 Cooling Test - Monitoring Temperatures"
echo "==================================================="
echo ""
echo "Fan Capability Test:"
echo "- Target: Keep GPU under 85°C under load"
echo "- Power limit: 250W (P40 max)"
echo "- Your fan must handle ~200W heat dissipation"
echo ""
echo "Starting 60-second monitoring..."
echo "Press Ctrl+C to stop"
echo ""

printf "%-8s %-10s %-12s %-8s %-15s\n" "Time" "Temp(°C)" "Power(W)" "Fan RPM" "Status"
printf "%-8s %-10s %-12s %-8s %-15s\n" "----" "--------" "--------" "-------" "------"

for i in {1..30}; do
    # Get GPU stats
    STATS=$(nvidia-smi --query-gpu=temperature.gpu,power.draw,clocks.current.graphics --format=csv,noheader,nounits 2>/dev/null)
    TEMP=$(echo $STATS | cut -d',' -f1 | tr -d ' ')
    POWER=$(echo $STATS | cut -d',' -f2 | tr -d ' ')
    CLOCK=$(echo $STATS | cut -d',' -f3 | tr -d ' ')
    TIME=$(date +%H:%M:%S)
    
    # Determine status
    if [ "$TEMP" -lt "70" ]; then
        STATUS="✓ Good"
    elif [ "$TEMP" -lt "85" ]; then
        STATUS="⚠ Warm"
    else
        STATUS="✗ HOT!"
    fi
    
    printf "%-8s %-10s %-12s %-8s %-15s\n" "$TIME" "$TEMP" "$POWER" "$CLOCK" "$STATUS"
    
    sleep 2
done

echo ""
echo "==================================================="
echo "Test Complete"
echo "==================================================="