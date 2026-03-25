#!/bin/bash
# Create simple 1x1 green PNG icons for ic_launcher and ic_launcher_round
for density in mipmap-hdpi mipmap-mdpi mipmap-xhdpi mipmap-xxhdpi mipmap-xxxhdpi; do
  dir="app/src/main/res/$density"
  # Create a minimal valid PNG (1x1 green pixel won't work for icons, need proper size)
  # Using placeholder - will need real icons later
  touch "$dir/ic_launcher.png"
  touch "$dir/ic_launcher_round.png"
done
