package com.terrarium.app.ui.terrarium

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.terrarium.app.data.model.*

/**
 * Screen for setting up base layers in a new terrarium.
 * Users add gravel, charcoal, and soil before planting.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BaseLayerSetupScreen(
    jarType: JarType,
    onComplete: (BaseLayerConfig) -> Unit,
    onSkip: () -> Unit
) {
    var hasGravel by remember { mutableStateOf(false) }
    var hasCharcoal by remember { mutableStateOf(false) }
    var hasSoil by remember { mutableStateOf(false) }
    var hasMoss by remember { mutableStateOf(false) }
    
    val canContinue = hasSoil // Minimum requirement
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Set Up Your Terrarium") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Instructions
            Text(
                text = "Add base layers to your ${jarType.name.lowercase().capitalize()} jar",
                style = MaterialTheme.typography.titleMedium,
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "Base layers improve plant health and give XP bonuses!",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Jar Preview with Layers
            Box(
                modifier = Modifier
                    .size(200.dp, 280.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant)
            ) {
                // Draw layers from bottom to top
                var currentBottom = 1f
                
                // Moss (top of soil)
                if (hasMoss) {
                    val mossHeight = 0.05f
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(14.dp)
                            .align(Alignment.BottomCenter)
                            .offset(y = (-260 + 14).dp)
                            .background(Color(0xFF228B22))
                    )
                }
                
                // Soil
                if (hasSoil) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(42.dp)
                            .align(Alignment.BottomCenter)
                            .background(Color(0xFF4A3728))
                    )
                }
                
                // Charcoal
                if (hasCharcoal) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(14.dp)
                            .align(Alignment.BottomCenter)
                            .offset(y = (if (hasSoil) -42 else 0).dp)
                            .background(Color(0xFF2C2C2C))
                    )
                }
                
                // Gravel
                if (hasGravel) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(28.dp)
                            .align(Alignment.BottomCenter)
                            .offset(y = (if (hasSoil && hasCharcoal) -56 else if (hasSoil || hasCharcoal) -42 else 0).dp)
                            .background(Color(0xFF8B7355))
                    )
                }
                
                // Jar outline placeholder
                Text(
                    text = "🫙",
                    fontSize = 80.sp,
                    modifier = Modifier.align(Alignment.Center)
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Layer Selection
            Text(
                text = "Tap to add layers:",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                LayerButton(
                    emoji = "🪨",
                    name = "Gravel",
                    description = "Drainage",
                    isSelected = hasGravel,
                    bonus = "+5 XP",
                    onClick = { hasGravel = !hasGravel }
                )
                
                LayerButton(
                    emoji = "⬛",
                    name = "Charcoal",
                    description = "Filter",
                    isSelected = hasCharcoal,
                    bonus = "+10 XP",
                    onClick = { hasCharcoal = !hasCharcoal }
                )
                
                LayerButton(
                    emoji = "🟤",
                    name = "Soil",
                    description = "Required",
                    isSelected = hasSoil,
                    bonus = "+15 XP",
                    isRequired = true,
                    onClick = { hasSoil = !hasSoil }
                )
                
                LayerButton(
                    emoji = "🌿",
                    name = "Moss",
                    description = "Decorative",
                    isSelected = hasMoss,
                    bonus = "+10 XP",
                    onClick = { hasMoss = !hasMoss }
                )
            }
            
            Spacer(modifier = Modifier.weight(1f))
            
            // XP Bonus Display
            val totalBonus = listOf(
                if (hasGravel) 5 else 0,
                if (hasCharcoal) 10 else 0,
                if (hasSoil) 15 else 0,
                if (hasMoss) 10 else 0
            ).sum()
            
            if (totalBonus > 0) {
                Surface(
                    color = MaterialTheme.colorScheme.primaryContainer,
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = "Setup Bonus: +$totalBonus XP",
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
                Spacer(modifier = Modifier.height(16.dp))
            }
            
            // Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                OutlinedButton(
                    onClick = onSkip,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Skip")
                }
                
                Button(
                    onClick = {
                        onComplete(
                            BaseLayerConfig(
                                hasGravel = hasGravel,
                                hasCharcoal = hasCharcoal,
                                hasSoil = hasSoil,
                                hasMoss = hasMoss
                            )
                        )
                    },
                    enabled = canContinue,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Continue")
                }
            }
        }
    }
}

@Composable
private fun LayerButton(
    emoji: String,
    name: String,
    description: String,
    isSelected: Boolean,
    bonus: String,
    isRequired: Boolean = false,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable { onClick() }
    ) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(
                    if (isSelected) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.surfaceVariant
                ),
            contentAlignment = Alignment.Center
        ) {
            if (isSelected) {
                Icon(
                    imageVector = Icons.Default.Check,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text(text = emoji, fontSize = 24.sp)
            }
        }
        
        Spacer(modifier = Modifier.height(4.dp))
        
        Text(
            text = name,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold
        )
        
        Text(
            text = description,
            style = MaterialTheme.typography.labelSmall,
            color = if (isRequired) MaterialTheme.colorScheme.error
                    else MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Text(
            text = bonus,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.primary
        )
    }
}