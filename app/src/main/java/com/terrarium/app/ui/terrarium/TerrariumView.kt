package com.terrarium.app.ui.terrarium

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.positionInRoot
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.terrarium.app.data.model.*

/**
 * Visual representation of a terrarium with tap-to-plant functionality.
 */
@Composable
fun TerrariumView(
    terrarium: Terrarium?,
    plants: List<Plant>,
    plantTypes: Map<Long, PlantType>,
    onTerrariumTap: (Float, Float) -> Unit,
    onPlantTap: (Plant) -> Unit,
    isPlantingMode: Boolean = false,
    modifier: Modifier = Modifier
) {
    var terrariumSize by remember { mutableStateOf(IntSize.Zero) }
    
    Box(
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(0.75f)
            .onGloballyPositioned { coordinates ->
                terrariumSize = coordinates.size
            }
            .clip(RoundedCornerShape(24.dp))
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFFE8F5E9),
                        Color(0xFFC8E6C9)
                    )
                )
            )
            .then(
                if (isPlantingMode) {
                    Modifier.pointerInput(Unit) {
                        detectTapGestures { offset ->
                            val normalizedX = offset.x / terrariumSize.width.toFloat()
                            val normalizedY = offset.y / terrariumSize.height.toFloat()
                            onTerrariumTap(normalizedX, normalizedY)
                        }
                    }
                } else {
                    Modifier
                }
            )
    ) {
        // Draw base layers (bottom to top)
        val layerDepth = terrarium?.getLayerDepth() ?: 0f
        val soilTop = 1f - layerDepth
        
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.BottomCenter)
                .height((layerDepth * 280).dp)
        ) {
            // Gravel at bottom
            if (terrarium?.hasGravel == true) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(28.dp)
                        .align(Alignment.BottomCenter)
                        .background(Color(0xFF8B7355))
                )
            }
            
            // Charcoal layer
            if (terrarium?.hasCharcoal == true) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(14.dp)
                        .align(Alignment.BottomCenter)
                        .offset(y = (if (terrarium.hasGravel) 28 else 0).dp)
                        .background(Color(0xFF2C2C2C))
                )
            }
            
            // Soil layer
            if (terrarium?.hasSoil == true) {
                val soilOffset = (if (terrarium.hasGravel) 28 else 0) + (if (terrarium.hasCharcoal) 14 else 0)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(42.dp)
                        .align(Alignment.BottomCenter)
                        .offset(y = soilOffset.dp)
                        .background(Color(0xFF4A3728))
                )
            }
            
            // Moss layer
            if (terrarium?.hasMoss == true) {
                val mossOffset = (if (terrarium.hasGravel) 28 else 0) + 
                                 (if (terrarium.hasCharcoal) 14 else 0) + 
                                 (if (terrarium.hasSoil) 42 else 0)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(14.dp)
                        .align(Alignment.BottomCenter)
                        .offset(y = mossOffset.dp)
                        .background(Color(0xFF228B22))
                )
            }
        }
        
        // Draw plants at their positions
        plants.forEach { plant ->
            val plantType = plantTypes[plant.typeId]
            PlantView(
                plant = plant,
                plantType = plantType,
                onClick = { onPlantTap(plant) },
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(
                        x = ((plant.positionX - 0.5f) * 200).dp,
                        y = ((plant.positionY - 0.5f) * 280).dp
                    )
            )
        }
        
        // Planting mode indicator
        if (isPlantingMode) {
            Surface(
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .padding(8.dp),
                color = MaterialTheme.colorScheme.primaryContainer,
                shape = RoundedCornerShape(16.dp)
            ) {
                Text(
                    text = "🌱 Tap to plant",
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelMedium
                )
            }
        }
    }
}

/**
 * Visual representation of a plant in the terrarium.
 */
@Composable
private fun PlantView(
    plant: Plant,
    plantType: PlantType?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val emoji = when (plant.growthStage) {
        GrowthStage.SEED -> "🌰"
        GrowthStage.SPROUT -> "🌱"
        GrowthStage.YOUNG -> plantType?.emoji ?: "🌿"
        GrowthStage.MATURE -> plantType?.emoji ?: "🌳"
    }
    
    val healthColor = when (plant.getStatus()) {
        PlantStatus.HEALTHY -> Color(0xFF4CAF50)
        PlantStatus.FAIR -> Color(0xFF8BC34A)
        PlantStatus.UNHEALTHY -> Color(0xFFFF9800)
        PlantStatus.WILTING -> Color(0xFFFF5722)
        PlantStatus.OVERWATERED -> Color(0xFF2196F3)
        PlantStatus.DEAD -> Color(0xFF9E9E9E)
    }
    
    Box(
        modifier = modifier
            .size(48.dp)
            .clickable { onClick() }
    ) {
        // Health indicator ring
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(healthColor.copy(alpha = 0.3f))
        )
        
        // Plant emoji
        Text(
            text = emoji,
            fontSize = 32.sp,
            modifier = Modifier.align(Alignment.Center)
        )
        
        // Water drop if needs water
        if (plant.moisture < 0.3f) {
            Text(
                text = "💧",
                fontSize = 12.sp,
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .offset(x = 4.dp, y = (-4).dp)
            )
        }
    }
}

/**
 * Planting mode overlay that shows where plants will go.
 */
@Composable
fun PlantingOverlay(
    position: Offset?,
    onConfirm: () -> Unit,
    onCancel: () -> Unit
) {
    if (position != null) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Plant here?",
                style = MaterialTheme.typography.titleMedium
            )
            
            Row(
                modifier = Modifier.padding(8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(onClick = onCancel) {
                    Text("Cancel")
                }
                Button(onClick = onConfirm) {
                    Text("Plant")
                }
            }
        }
    }
}