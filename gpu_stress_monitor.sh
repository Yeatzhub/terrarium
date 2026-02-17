#!/bin/bash
# GPU Stress Test with Real-time Monitoring

echo "==================================================="
echo "Tesla P40 Fan Stress Test - 60 seconds"
echo "==================================================="
echo ""
echo "Monitoring GPU temperature and power..."
echo ""
printf "%-10s %-12s %-10s %-10s %-10s\n" "Time" "Power(W)" "Temp(C)" "Clock(MHz)" "Status"
printf "%-10s %-12s %-10s %-10s %-10s\n" "----" "--------" "-------" "----------" "------"

# Monitor for 60 seconds
for i in {1..30}; do
    STATS=$(nvidia-smi --query-gpu=power.draw,temperature.gpu,clocks.current.graphics --format=csv,noheader,nounits 2>/dev/null)
    POWER=$(echo $STATS | cut -d',' -f1 | tr -d ' ')
    TEMP=$(echo $STATS | cut -d',' -f2 | tr -d ' ')
    CLOCK=$(echo $STATS | cut -d',' -f3 | tr -d ' ')
    TIME=$(date +%H:%M:%S)
    
    # Status indicator
    if (( $(echo "$TEMP < 70" | bc -l 2>/dev/null || echo "1") )); then
        STATUS="✓ GOOD"
    elif (( $(echo "$TEMP < 83" | bc -l 2>/dev/null || echo "0") )); then
        STATUS="⚠ WARM"
    else
        STATUS="🔥 HOT"
    fi
    
    printf "%-10s %-12s %-10s %-10s %-10s\n" "$TIME" "$POWER" "$TEMP" "$CLOCK" "$STATUS"
    sleep 2
done

echo ""
echo "==================================================="
echo "Test Complete"
echo "==================================================="
